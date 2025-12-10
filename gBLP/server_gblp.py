# colorscheme blue dark 

# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------

from utils import makeName, printLicence, checkThreads, exitNotNT, printBeta
exitNotNT() # make sure we're on Windows otherwise exit. 

from rich.console import Console; console = Console()

from loguru import logger

import grpc; grpc.aio.init_grpc_aio()

from constants import MAX_MESSAGE_LENGTH

# python importpio.server

import os
os.environ["GRPC_VERBOSITY"] = "error"
import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import string
import random
from collections import defaultdict
import json
import datetime as dt
import threading
import signal
import queue
import blpapi
import msvcrt
import time
import traceback
from pathlib import Path
from prompt_toolkit import PromptSession
import multiprocessing # no more thread leaking from blpapi. Wrap and shut. 
from multiprocessing import Manager
from cryptography.hazmat.primitives import serialization, hashes 

# gRPC imports
import grpc; grpc.aio.init_grpc_aio() # logging
from grpc.aio import ServerInterceptor

from bloomberg_pb2 import (
    KeyRequestId, 
    KeyResponse,
    HistoricalDataRequest,
    HistoricalDataResponse,
    IntradayBarRequest,
    IntradayBarResponse,
    ReferenceDataRequest,
    ReferenceDataResponse,
    Topic,
    TopicList,
    Ping,
    Pong,
    topicType,
    subscriptionType, 
    ServicesInfoRequest,
    ServicesInfoResponse,
    ServiceInfo)

from bloomberg_pb2_grpc import (
    BbgServicer, 
    KeyManagerServicer, 
    add_BbgServicer_to_server, 
    add_KeyManagerServicer_to_server, 
    BbgStub
)

from responseParsers import (
    buildHistoricalDataResponse, 
    buildIntradayBarResponse,
    buildReferenceDataResponse,
    makeTopicString
)

from requestHelpers import (
    bool_evaluator,
    add_dates_to_request_if_missing,
    add_overrides_to_bbgrequest
)


from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from google.protobuf import empty_pb2
# import value

from argparse import ArgumentParser, RawTextHelpFormatter


from SubscriptionOptions import (
    addSubscriptionOptions, 
    setSubscriptionSessionOptions
)

from ConnectionAndAuthOptions import (
    addConnectionAndAuthOptions, 
    createSessionOptions
)   

from EventRouter import EventRouter

from certMaker import get_conf_dir, make_client_certs, make_all_certs, check_for_certs
from utils import makeName, printLicence, checkThreads


# ----------------- global variables ----------------------

globalOptions = None

from constants import DEFAULT_FIELDS

# ----------------- thread creation tracking ----------------------
def trace_function(frame, event, arg):
    """Trace function that will be called for every line of code in every thread."""
    if threading.current_thread().name != "asyncio_0":
        if event == 'call':
            console.print(f"[bold blue]Calling function: {frame.f_code.co_name} in {threading.current_thread().name}")
        elif event == 'line':
            console.print(f"[bold green]Line {frame.f_lineno} in {frame.f_code.co_name} in {threading.current_thread().name}")
        elif event == 'return':
            console.print(f"[bold red]Returning from {frame.f_code.co_name} in {threading.current_thread().name}")
        return trace_function  # Return itself to continue tracing

# Set this trace function to be used for all new threads
# threading.settrace(trace_function)
# ----------------- util functions ----------------------

def serialize_datetime(obj): 
    if isinstance(obj, dt.datetime) or isinstance(obj, dt.date):
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

# ----------------- parse the command line and session options ---------------

def parseCmdLine():
    """Parse command line arguments"""
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter,
                            description="Asynchronous subscription with event handler")
    addConnectionAndAuthOptions(parser)
    addSubscriptionOptions(parser)
    parser.add_argument(
        "--grpchost",
        dest="grpchost",
        help="Hostname that this gRPC will respond to.",
        type=str)
    parser.add_argument(
        "--grpcport",
        dest="grpcport",
        type=str,
        help="Bloomberg session grpc port",
        default="50051")
    parser.add_argument(
        "--grpckeyport",
        dest="grpckeyport",
        type=str,
        help="Key request grpc port (for client certificates)",
        default="50052")
    # add a boolean make-cert argument
    parser.add_argument(
        "--gencerts",
        dest="gencerts",
        help="Generate a self-signed certificate",
        action="store_true",
        default=False)
    parser.add_argument(
        "--delcerts",
        dest="delcerts",
        help="Delete all certificates",
        action="store_true",
        default=False)
    parser.add_argument(
        "--nokeypress",
        dest="nokeypress",
        help="Prevent the server from detecting status keypresses (only use if debugging with pdb)",
        action="store_true",
        default=False)
    options = parser.parse_args()
    options.options.append(f"interval=1")
    return options



# ----------------- keys manager for mTLS ----------------------

class KeyManager(KeyManagerServicer):
    # responds on an insecure port with client certificates
    # but only if authorised by the server. 

    def __init__(self):
        pass

    async def input_timeout(self, prompt, timeout):
        session = PromptSession()
        try:
            # Prompt with timeout; raises EOFError on timeout
            result = await asyncio.wait_for(session.prompt_async(prompt), timeout=timeout)
            return result.strip() if result else None
        except asyncio.TimeoutError:
            logger.info("Input timed out")
            return None
        except EOFError:
            # This can happen if interrupted
            return None

    async def requestKey(self, 
                         request: KeyRequestId, 
                         context: grpc.aio.ServicerContext) -> KeyResponse:
        logger.info("Serving keyRequest request %s", request)
        accept = await self.input_timeout((f"Received request from {context.peer()}"
            f" with id {request.id}. \nType Yes <Enter> within the next 10 seconds to authorise: "), 10)
        if accept is None:
            return KeyResponse(authorised=False, reason="Server timed out")
        if accept == "Yes":
            key, cert, cacert = make_client_certs(globalOptions.grpchost, get_conf_dir())
            bcacert = cacert.public_bytes(serialization.Encoding.PEM)
            logger.info(f"Key request granted for {request.id} and {context.peer()}")
            return KeyResponse(key=key, cert=cert, cacert=bcacert, authorised=True)
        else:
            print(f"Got {accept} not Yes. Denying request.")
            return KeyResponse(authorised=False, reason="Request denied")


async def serveBbgSession(bbgAioServer, bbgAioManager) -> None:

    listenAddr = f"{globalOptions.grpchost}:{globalOptions.grpcport}"
    add_BbgServicer_to_server(bbgAioManager, bbgAioServer)

    confdir = get_conf_dir()

    # Load server's certificate and private key
    with open(confdir / "server_certificate.pem", "rb") as f:
        serverCert = f.read()
    with open(confdir / "server_private_key.pem", "rb") as f:
        serverKey = f.read()
    # Load CA certificate to verify clients
    with open(confdir / "ca_certificate.pem", "rb") as f:
        CAcert = f.read()


    serverCredentials = grpc.ssl_server_credentials(
        [(serverKey, serverCert)],
        root_certificates=CAcert,
        require_client_auth=True,  # Require clients to provide valid certificates
    )
    bbgAioServer.add_secure_port(listenAddr, serverCredentials) 

    await bbgAioServer.start()
    logger.info(f"Starting session server on {listenAddr}")
    await bbgAioServer.wait_for_termination()
    await bbgAioManager.close()
    logger.info("gRPC sessions server stopped.")
    #raise # propagate


async def serveKeySession(keyAioServer) -> None:

    keyListenAddr = f"{globalOptions.grpchost}:{globalOptions.grpckeyport}"
    add_KeyManagerServicer_to_server(KeyManager(), keyAioServer)
    keyAioServer.add_insecure_port(keyListenAddr) # this listens without credentials

    await keyAioServer.start()
    logger.info(f"Starting key server on {keyListenAddr}")
    await keyAioServer.wait_for_termination()
    logger.info("Key server stopped.")



# -------------------- individual session handler ----------------------

class SessionRunner(BbgServicer):
    # the internal gRPC server which responds to requests from the Bbg
    # internal gRPC client. 
    def __init__(self, options, comq, done):
        self.options = options
        self.comq = comq 
        self.done = done
        self.interval = options.interval # subscription interval
        self.maxEventQueueSize = 10000
        self.servicesOpen = dict()
        self.correlators = dict()
        self.session = None # must SessionRunner.open() one first
        self.servicesAvail = {"Subscribe": "//blp/mktdata",
                              "UnSubscribe": "//blp/mktdata",
                              "BarSubscribe": "//blp/mktbar",
                              "BarUnSubscribe": "//blp/mktbar",
                              "TaSubscribe": "//blp/tasvc",
                              "HistoricalDataRequest": "//blp/refdata",
                              "IntradayBarRequest": "//blp/refdata",
                              "IntradayTickRequest": "//blp/refdata",
                              "ReferenceDataRequest": "//blp/refdata",
                              "instrumentListRequest": "//blp/instruments", # terminal SECF
                              "curveListRequest": "//blp/instruments",      # terminal CRVF
                              "govtListRequest": "//blp/instruments",
                              "FieldListRequest": "//blp/apiflds",
                              "FieldSearchRequest": "//blp/apiflds",
                              "FieldInfoRequest": "//blp/apiflds",
                              "CategorizedFieldSearchRequest": "//blp/apiflds",
                              "studyRequest": "//blp/tasvc",
                              "SnapshotRequest": "//blp/mktlist"}
        self.subq = asyncio.Queue() # sends messages out back to grpc handler
        self.numDispatcherThreads = 1 # if > 1 then threaded dispatchers will be created
        self.loop = asyncio.get_event_loop() # used by the event handler
        # start the comq
        self.comqTask = asyncio.create_task(self.listenComq())


    def _getService(self, serviceReq: str) -> bool:
        """ open a service from the sub and ref services available """
        if not self.session:
            error = "Session not open"
            logger.error(error)
            return (False, error)
        if not self.servicesOpen.get(serviceReq):
            if not self.session.openService(self.servicesAvail[serviceReq]):
                error = "Failed to open service HistoricalDataRequest"
                logger.error(error)
                return(False, error)
            else:
                self.servicesOpen[serviceReq] = self.servicesAvail[serviceReq]
                logger.info("Opened service HistoricalDataRequest")
        logger.info(f"Service {serviceReq} is open via {self.servicesOpen[serviceReq]}")
        return (True, self.servicesOpen[serviceReq])


    def _createEmptyRequest(self, serviceReq: str) -> blpapi.Request:
        success, service = self._getService(serviceReq)
        if not success:
            return (False, service)
        request = self.session.getService(service).createRequest(serviceReq)
        return (True, request)


    def sessionTerminatedCallback(self):
        logger.error("!!!!!!!!!!!!!!!!!!!!!!!! SESSION TERMINATED !!!!!!!!!!!!!!!!!!!!!!!!")
        # try to recreate session constantly 
        fail24 = dt.datetime.now() + dt.timedelta(minutes = 1) # minutes = 24 * 60
        try:
            self.session.stop()
        except:
            logger.warning("Could not stop session")
        while True:
            if self.open(fail_with_session = False):
                logger.info("Session re-opened")
                # TODO subscribe
                break
            if dt.datetime.now() > fail24:
                logger.error("Couldn't re-open session after 24 hours. Exiting")
                self.close()
                break
            logger.info("Session re-open retry in 1 minute")
            time.sleep(60)


    def open(self, fail_with_session = True):
        """ open the session and associated services """
        # setup the correct options
        sessionOptions = createSessionOptions(self.options)
        sessionOptions.setMaxEventQueueSize(self.maxEventQueueSize)
        self.handler = EventRouter(parent = self)
        if self.numDispatcherThreads > 1:
            self.eventDispatcher = blpapi.EventDispatcher(numDispatcherThreads=self.numDispatcherThreads) 
            self.eventDispatcher.start()
            self.session = blpapi.Session(sessionOptions, 
                                          eventHandler=self.handler.processEvent,
                                          eventDispatcher=self.eventDispatcher)
        else:
            self.session = blpapi.Session(sessionOptions, 
                                          eventHandler=self.handler.processEvent)
        if not self.session.start():
            logger.error("Failed to start session.")
            if fail_with_session:
                self.done.set()
            return False
        else:
            logger.debug(f"Session opened")
            return True

    def close(self):
        """ close the session """
        self.session.stop()
        if self.numDispatcherThreads > 1:
            self.eventDispatcher.stop()
        if not self.comqTask.done():
            logger.info("Cancelling comq listener")
            self.comqTask.cancel()
        logger.info(f"Bloomberg session closed")


    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:

        # validate dates
        request = add_dates_to_request_if_missing(request)

        # make request dict
        success, bbgRequest = self._createEmptyRequest("HistoricalDataRequest")
        if not success:
            raise context.abort(grpc.StatusCode.NOT_FOUND, "Service not found")
        dtstart = request.start.ToDatetime().strftime("%Y%m%d")
        dtend = request.end.ToDatetime().strftime("%Y%m%d")
        requestDict = {"securities": request.topics,
                       "fields": request.fields,
                       "startDate": dtstart,
                       "endDate": dtend} # TODO OVERRIDES

        # make bbg request and add options and overrides
        requestDict = requestDict | bool_evaluator(request.options) # make options dict and merge
        bbgRequest.fromPy(requestDict) # make bbgrequest
        bbgRequest = add_overrides_to_bbgrequest(bbgRequest, request.overrides)

        # send request to bloomberg 
        # create a random 32-character string as the correlationId
        corrString = f"hist:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        q = asyncio.Queue() # for responses
        self.correlators[corrString] = {"q": q,
                                       "request": request}
        self.session.sendRequest(bbgRequest, correlationId=correlid)

        # wait for response
        messageList = []
        while True:
            msg = await q.get()
            messageList.append(msg["data"])
            if not msg["partial"]:
                break
        if messageList:    
            result = buildHistoricalDataResponse(messageList)
            return result 
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")



    async def intradayBarRequest(self, request: IntradayBarRequest,
                                 context: grpc.aio.ServicerContext) -> IntradayBarResponse:
        """ request intraday bar data """

        # validate and complete
        request = add_dates_to_request_if_missing(request)

        # send request to bloomberg 
        logger.info(f"Requesting intraday bar data {str(request.topic)}")
        success, bbgRequest = self._createEmptyRequest("IntradayBarRequest")
        if not success:
            raise context.abort(grpc.StatusCode.NOT_FOUND, "Service not found")
        dtstart = request.start.ToDatetime().strftime("%Y-%m-%dT%H:%M:%S")
        dtend = request.end.ToDatetime().strftime("%Y-%m-%dT%H:%M:%S")
        if not request.interval:
            request.interval = 5
        requestDict = {"security": request.topic,
                       "eventType": "TRADE",
                       "startDateTime": dtstart,
                       "endDateTime": dtend,
                       "gapFillInitialBar": "true",
                       "interval": request.interval} # TODO OVERRIDES

        # make bbg request and add interval and options (no overrides for intradayBarRequest)
        requestDict = requestDict | bool_evaluator(request.options) # make options dict and merge
        bbgRequest.fromPy(requestDict)

        # create a random 32-character string as the correlationId
        corrString = f"bar:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        q = asyncio.Queue() 
        self.correlators[corrString] = {"q": q,
                                       "request": request}
        self.session.sendRequest(bbgRequest, correlationId=correlid)

        # wait for response
        messageList = []
        while True:
            msg = await q.get()
            messageList.append(msg["data"])
            if not msg["partial"]: 
                break # last message received
        if messageList:
            result = buildIntradayBarResponse(messageList)
            return result
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")


    async def referenceDataRequest(self, request: ReferenceDataRequest,
                                   context: grpc.aio.ServicerContext) -> ReferenceDataResponse:
        """ request reference data """

        # send request to bloomberg
        logger.info((f"Reference request recieved. "
                     f"Topics: {' '.join(list(request.topics))} "
                     f"Fields: {' '.join(list(request.fields))}"))
        success, bbgRequest = self._createEmptyRequest("ReferenceDataRequest")
        if not success:
            raise context.abort(grpc.StatusCode.NOT_FOUND, "Service not found")
        requestDict = {"securities": request.topics,
                       "fields": request.fields}

        # make bbg request and add options and overrides
        requestDict = requestDict | bool_evaluator(request.options) # make options dict and merge
        bbgRequest.fromPy(requestDict) # make bbgrequest
        bbgRequest = add_overrides_to_bbgrequest(bbgRequest, request.overrides)

        corrString = f"ref:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        q = asyncio.Queue() 
        self.correlators[corrString] = {"q": q,
                                       "request": request}
        self.session.sendRequest(bbgRequest, correlationId=correlid)
       
        # wait for response
        messageList = []
        while True:
            msg = await q.get()
            messageList.append(msg["data"])
            if not msg["partial"]:
                break
        if messageList:
            result = buildReferenceDataResponse(messageList)
            return result
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")


    async def servicesInfoRequest(self, _request,
                                 context: grpc.aio.ServicerContext) -> ServicesInfoResponse:
        refservices = set([v for k, v in self.servicesAvail.items() if "subscribe" not in k.lower()])
        sir = ServicesInfoResponse()
        for service in filter(lambda x: "subscribe" not in x.lower(), self.servicesAvail.keys()):
            logger.info(f"Requesting service info for {service}")
            success, req = self._createEmptyRequest(service)
            if not success:
                info = "No service info"
            else:
                try:
                    inforesp = req.asElement().elementDefinition()
                    info = inforesp.toString() # LATER may be better ways; check methods on inforesp
                except Exception as e:
                    info = "No service info"
            si = ServiceInfo(serviceName=service, serviceDescription=info)
            sir.services.append(si)
        return sir


    def close(self):
        """ close the session """
        self.session.stop()
        if self.numDispatcherThreads > 1:
            self.eventDispatcher.stop()
        if not self.comqTask.done():
            logger.info("Cancelling comq listener")
            self.comqTask.cancel()
        logger.info(f"Bloomberg session closed")


    # ------------ subscriptions -------------------

    def makeCorrelatorString(self, topic: Topic, service: str, clientid = None) -> str:
        """ make a unique correlator string """
        intervalstr = f"interval={int(topic.interval)}"
        fieldsstr = ",".join(topic.fields)
        topicTypeName = topicType.Name(topic.topictype) # SEDOL1/TICKER/CUSIP etc
        corrstring = f"{service}/{topic.topic}?fields={fieldsstr}&{intervalstr}" 
        if clientid:
            corrstring = f"{clientid}/{corrstring}"
        return str(hash(corrstring))


    def makeSubString(self, topic: Topic, service: str) -> str:
        """ make a valid Bloomberg subscription string """
        intervalstr = f"interval={int(topic.interval)}"
        fieldsstr = ",".join(topic.fields)
        topicTypeName = topicType.Name(topic.topictype) # SEDOL1/TICKER/CUSIP etc
        substring = f"{service}/{topic.topic}?fields={fieldsstr}&{intervalstr}" 
        return substring


    async def sub(self, topicList: TopicList, context: grpc.aio.ServicerContext) -> TopicList:
        """ subscribe to a list of topics """

        clientid = dict(context.invocation_metadata()).get("client")

        # make sure the service is open
        _success, barservice = self._getService("BarSubscribe")
        _success, tickservice = self._getService("Subscribe")
        barsublist = blpapi.SubscriptionList()
        ticksublist = blpapi.SubscriptionList()
        subq = asyncio.Queue() # for responses
        for t in topicList.topics:
            if t.subtype == subscriptionType.BAR:
                substring = self.makeSubString(t, barservice)
                corrstring = self.makeCorrelatorString(t, barservice, clientid)
                correlid = blpapi.CorrelationId(corrstring)
                barsublist.add(substring, correlationId=correlid)
            else:
                substring = self.makeSubString(t, tickservice)
                corrstring = self.makeCorrelatorString(t, tickservice, clientid)
                correlid = blpapi.CorrelationId(corrstring) 
                ticksublist.add(substring, correlationId=correlid)
            self.correlators[corrstring] = {"q": subq, 
                                           "topic": t, 
                                           "clientid": clientid,
                                           "correlid": correlid}
        if barsublist.size() > 0:
            self.session.subscribe(barsublist)
        if ticksublist.size() > 0:
            self.session.subscribe(ticksublist)

        while not self.done.is_set():
            try:
                topic = await subq.get() 
            except asyncio.CancelledError:
                logger.info("Subscription stream cancelled, unsubscribing.")
                # unsubscribe from all topics TODO
                break
            except Exception as e:
                logger.error(f"Error in subscription stream {e}")
                break
            yield topic


    async def subscriptionInfo(self, _request, 
                               context: grpc.aio.ServicerContext) -> TopicList:
        """ get the current subscription list """

        clientid = dict(context.invocation_metadata()).get("client")

        tl = TopicList()
        for v in self.correlators.values():
            if v["clientid"] == clientid:
                tl.topics.append(v["topic"])
        return tl


    async def unsub(self, topicList: TopicList, context: grpc.aio.ServicerContext) -> empty_pb2.Empty:
        """ unsubscribe from a list of topics. Note removal from the 
        correlators only happens when the event handler receives the
        unsubscription event."""

        clientid = dict(context.invocation_metadata()).get("client")

        _success, barservice = self._getService("BarSubscribe")
        _success, tickservice = self._getService("Subscribe")
        substrings = [] # will refer to these later to make sure unsubbed
        bbgunsublist = blpapi.SubscriptionList()
        for t in topicList.topics:
            if t.subtype == subscriptionType.BAR:
                service = self.servicesOpen["BarSubscribe"]
            else:
                service = self.servicesOpen["Subscribe"]
            corrstring = self.makeCorrelatorString(t, service, clientid)
            correlator = self.correlators.get(corrstring)
            if not correlator:
                logger.warning(f"Correlator not found for {substring}")
                continue # skip this one if no correlator found
            else:
                logger.info(f"Unsubscribing: {makeTopicString(t)}")
                substring = self.makeSubString(t, service)
                substrings.append(substring)
                correlid = correlator["correlid"]
                bbgunsublist.add(substring, correlationId=correlid) 
        if substrings:
            self.session.unsubscribe(bbgunsublist)
        return empty_pb2.Empty()


    async def serviceInfo(self):
        """ get the service info """
        for service in self.servicesAvail.keys():
            try:
                console.print(f"[bold blue]Service {service}")
                succes, req = self._createEmptyRequest(service)
                info = req.asElement().elementDefinition()
                console.print(f"[bold orange1]{dir(info)}") 
                print(info.toString())
            except Exception as e:
                logger.error(f"Error in service info: {e}")
                # print full trace
                traceback.print_exc()



    async def listenComq(self):
        """Listen for messages from the grpc handler. This will also close
        the session if the done event is set. """
        while not self.done.is_set():
            try:
                msg = await asyncio.to_thread(self.comq.get, timeout=0.15)
                # Process the message here
                match msg:
                    case ("key", b"c"):
                        console.print(f"[bold cyan]Number of correlators: {len(self.correlators)}")
                        for k, v in self.correlators.items():
                            if v.get("topic"):
                                ts = makeTopicString(v["topic"])
                            else:
                                ts = "No topic"
                            console.print(f"[bold cyan]{k},  {ts}")
                    case ("key", b"t"):
                        checkThreads(processes=False, colour="green")
                    case ("key", b"i"): # DEBUG
                        await self.serviceInfo()
                    case("key", b"s"): # DEBUG -- session disconnected test
                        self.sessionTerminatedCallback()
                    case ("request", "close"):
                        self.done.set()
            except queue.Empty:
                continue  # No message; keep looping
            except asyncio.CancelledError:
                logger.info("CancelledError")
                self.done.set()
                break
            except Exception as e:
                logger.error(f"Error in comq listener: {e}")
                break
        logger.info("Comq listener stopped.")
        await self.close()


            
# -------------------------- gRPC method implementations ---------------------------



class ConnectionLoggingInterceptor(ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        console.print(f"[cyan]Incoming connection: {handler_call_details.method}")
        # Proceed with the normal handling of the RPC
        return await continuation(handler_call_details)


def runSessionRunner(options, comq, done, winPipeName):

    async def start_session_runner():
        logger.info("Starting session runner grpc server")
        sessionRunner = SessionRunner(options, comq, done)
        bbgSessionServer = grpc.aio.server(
            options=[
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ])
        add_BbgServicer_to_server(sessionRunner, bbgSessionServer)
        console.print(f"[bold blue]Starting session runner on {winPipeName}")
        bbgSessionServer.add_insecure_port(winPipeName)# this listens without credentials
        await bbgSessionServer.start()
        sessionRunner.open()
        try:
            # Keep the event loop running
            await asyncio.Future()  # Run until cancelled
        except asyncio.CancelledError:
            logger.info("SessionRunner event loop stopped.")
        finally:
            await sessionRunner.close()

    # Set up and run the asyncio event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_session_runner())
    except KeyboardInterrupt:
        console.print("[bold red on white]SessionRunnner stopped by keyboard interrupt.")
        done.set()
        time.sleep(1)
    finally:
        loop.close()


class Bbg(BbgServicer):
    # implements all the gRPC methods for the session manager. This is where the grPC
    # calls from clients get serviced. These call a second internal gRPC server 
    # which communicates with the SessionRunner(s), which are the bloomberg api classes.

    def __init__(self, options, comq, done, manager):
        winPipeName = "localhost:50055"
        self.sessionProc = multiprocessing.Process(target=runSessionRunner, 
                                                   args=(options, comq, done, winPipeName), 
                                                   name="SessionRunner")
        self.channel = grpc.aio.insecure_channel(
            winPipeName,
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ])
        self.stub = BbgStub(self.channel)
        self.sessionProc.start()
        self.options = options
        self.manager = manager
        self.comq = comq
        self.done = done

    def _makeClientId(self, context):
        client = dict(context.invocation_metadata()).get("client")
        if not client:
            client = "unknown"
        ip = context.peer().split(":")[1]
        return f"{client}:{ip}"


    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:
        # report
        clientid = self._makeClientId(context)
        topicstr = ",".join(request.topics)
        logger.info(f"Received historical data request {topicstr} from {clientid}")

        # dispatch 
        result = await self.stub.historicalDataRequest(request)
        return result


    async def intradayBarRequest(self, request: IntradayBarRequest,
                                  context: grpc.aio.ServicerContext) -> IntradayBarResponse:
        clientid = self._makeClientId(context)
        logger.info(f"Received intraday bar request {str(request.topic)} from {clientid}")
        logger.debug(f"Received request {request}")
        result = await self.stub.intradayBarRequest(request)
        return result


    async def referenceDataRequest(self, request: ReferenceDataRequest,
                                   context: grpc.aio.ServicerContext) -> ReferenceDataResponse:
        clientid = self._makeClientId(context)
        topicstr = ",".join(request.topics)
        logger.info(f"Received reference data request {topicstr} from {clientid}")
        result = await self.stub.referenceDataRequest(request)
        return result


    async def sub(self, topicList: TopicList, context: grpc.aio.ServicerContext) -> TopicList:
        """subscribe""" 
        clientid = self._makeClientId(context)
        topicstr = ",".join([t.topic for t in topicList.topics])
        logger.info(f"Received subscription request {topicstr} from {clientid}")
        stream = self.stub.sub(topicList, metadata=[("client", clientid)])
        try:
            async for topic in stream:
                yield topic
        # except cancelled error
        except asyncio.CancelledError:
            logger.info("Subscription stream cancelled, unsubscribing.")
            await self.unsub(topicList, context)
            raise
        except grpc.aio.AioRpcError as e:
            logger.error(f"Error in subscription stream: {e}")
            raise


    async def unsub(self, topicList: TopicList, context: grpc.aio.ServicerContext) -> empty_pb2.Empty:
        clientid = self._makeClientId(context)
        topicstr = ",".join([t.topic for t in topicList.topics])
        logger.info(f"Received unsubscription request {topicstr} from {clientid}")
        self.stub.unsub(topicList, metadata=[("client", clientid)])
        return empty_pb2.Empty()


    async def subscriptionInfo(self, _request, 
                               context: grpc.aio.ServicerContext) -> TopicList:
        clientid = self._makeClientId(context)
        logger.info(f"Received subscription info request from {clientid}")
        result = await self.stub.subscriptionInfo(_request, metadata=[("client", clientid)])
        return result

    async def servicesInfoRequest(self, _request, 
                                 context: grpc.aio.ServicerContext) -> ServicesInfoResponse:
        clientid = self._makeClientId(context)
        logger.info(f"Received service info request from {clientid}")
        result = await self.stub.servicesInfoRequest(_request, metadata=[("client", clientid)])
        return result


    async def ping(self, request: Ping, context: grpc.aio.ServicerContext) -> Pong:
        message = f"Pong: {request.message}"
        logger.info(f"Received ping {request.message}. Sending pong.")
        return Pong(message=message)


    async def close(self):
        self.comq.put(("key", b"q"))
        self.sessionProc.terminate()


# ----------------- keypress management----------------------

async def keypressDetector(comq, done):
    while not done.is_set():
        # Offload the blocking part to a different thread
        key = await asyncio.to_thread(check_keypress)
        if key is not None:
            logger.debug(f"Keypress detected: {key}")
        match key:
            case b"q":
                print("Q pressed")
                done.set()
            case b"t":
                checkThreads()
                comq.put(("key", b"t"))
            case b"c":
                comq.put(("key", b"c"))
            case b"i": # DEBUG
                comq.put(("key", b"i"))
            case b"s":
                print("'s' pressed")
                comq.put(("key", b"s"))
            case None:
                pass
        await asyncio.sleep(0.2)
    logger.info("Keypress detector stopped.")


def check_keypress():
    # This function will be executed in a separate thread
    if msvcrt.kbhit():
        key = msvcrt.getch()
        return key
    return None


# ----------------- mains ----------------------


async def asyncMain(globalOptions):
    bbgAioServer = grpc.aio.server(
        interceptors=(ConnectionLoggingInterceptor(),),
        options=[
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ])
    keyAioServer = grpc.aio.server()
    manager = Manager()
    comq = manager.Queue() # communication queue
    done = manager.Event()
    bbgAioManager = Bbg(globalOptions, comq, done, manager)
    bbgAioTask = asyncio.create_task(serveBbgSession(bbgAioServer, bbgAioManager))
    keyTask = asyncio.create_task(serveKeySession(keyAioServer))
    if not globalOptions.nokeypress:
        keypressTask =asyncio.create_task(keypressDetector(comq, done)) 
        console.print("[bold blue]--------------------------")
        console.print("[bold red on white blink]Press Q to stop the server")
        console.print("[bold blue]--------------------------")
    await asyncio.to_thread(done.wait)
    logger.info("done event set")
    await bbgAioServer.stop(grace=3)
    await keyAioServer.stop(grace=3)
    logger.info("Gathering asyncio gRPC task wrappers...")
    if not globalOptions.nokeypress:
        await asyncio.gather(bbgAioTask, keyTask, keypressTask)
    else:
        await asyncio.gather(bbgAioTask, keyTask)
    logger.info("All tasks stopped. Exiting.")
    os._exit(0)


def main():
    global globalOptions
    globalOptions = parseCmdLine()
    if globalOptions.gencerts:
        if not globalOptions.grpchost:
            print(("Must specify --grpchost xxxx where xxxx is server hostname or IP address "
                   "when using --gencerts."))
            return
        else:
            confdir = get_conf_dir()
            make_all_certs(str(globalOptions.grpchost), confdir)
    elif not check_for_certs():
        print(("Secure TLS/SSL credentials not found. to create them: "
              "server_gblp --gencerts --grpchost xxxx "
              "where xxxx is the server hostname or IP address."))
        return
    elif globalOptions.delcerts:
        confdir = get_conf_dir()
        for f in confdir.glob("*.pem"):
            f.unlink()
        print("Deleted all certificates. Run --gencerts to make new ones.")
    elif not globalOptions.grpchost:
        console.print("[bold red]Must specify --grpchost xxxx where xxxx is server hostname or IP address.")
    else:
        printBeta()
        printLicence()
        try:
            asyncio.run(asyncMain(globalOptions))
            logger.debug("asyncio main() exited")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            console.print("[bold magenta on white]You should press 'q' to stop the server.")
            console.print("[bold white on red] Killing all threads and processes.")
            if not done.is_set():
                done.set()
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Caught exception {e}")
        finally:
            for th in threading.enumerate(): 
                if not th.name == "MainThread":
                    console.print(f"[bold magenta]Thread {th.name} is still running[/bold magenta]")
            console.print("[bold green on white]os._exit(0)")
            os._exit(1)


if __name__ == "__main__":
    main()
