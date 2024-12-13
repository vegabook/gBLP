# colorscheme blue dark

# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------

from gBLP.util.utils import makeName, printLicence, checkThreads, exitNotNT, printBeta
exitNotNT() # make sure we're on Windows otherwise exit. 

from rich.console import Console; console = Console()

from loguru import logger

import grpc; grpc.aio.init_grpc_aio()

# python imports
import os
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
import multiprocessing # no more thread leaking from blpapi. Wrap and shut. 
from multiprocessing import Manager
from cryptography.hazmat.primitives import serialization, hashes 

# gRPC imports
import grpc; grpc.aio.init_grpc_aio() # logging
from grpc.aio import ServerInterceptor

from gBLP.bloomberg_pb2 import KeyRequestId, KeyResponse
from gBLP.bloomberg_pb2 import HistoricalDataRequest 
from gBLP.bloomberg_pb2 import HistoricalDataResponse
from gBLP.bloomberg_pb2 import IntradayBarRequest
from gBLP.bloomberg_pb2 import IntradayBarResponse
from gBLP.bloomberg_pb2 import ReferenceDataRequest
from gBLP.bloomberg_pb2 import ReferenceDataResponse 
from gBLP.bloomberg_pb2 import Topic
from gBLP.bloomberg_pb2 import TopicList
from gBLP.bloomberg_pb2 import Ping, Pong
from gBLP.bloomberg_pb2 import topicType
from gBLP.bloomberg_pb2 import subscriptionType

from gBLP.bloomberg_pb2_grpc import BbgServicer, KeyManagerServicer
from gBLP.bloomberg_pb2_grpc import add_BbgServicer_to_server, \
    add_KeyManagerServicer_to_server

from gBLP.responseParsers import (
    buildHistoricalDataResponse, 
    buildIntradayBarResponse,
    buildReferenceDataResponse,
    makeTopicString
)

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from google.protobuf import empty_pb2
# import value

from argparse import ArgumentParser, RawTextHelpFormatter


from gBLP.util.SubscriptionOptions import (
    addSubscriptionOptions, 
    setSubscriptionSessionOptions
)

from gBLP.util.ConnectionAndAuthOptions import (
    addConnectionAndAuthOptions, 
    createSessionOptions
)   

from gBLP.EventRouter import EventRouter

from gBLP.util.certMaker import get_conf_dir, make_client_certs, make_all_certs, check_for_certs
from gBLP.util.utils import makeName, printLicence, checkThreads


# ----------------- global variables ----------------------

globalOptions = None

from gBLP.constants import DEFAULT_FIELDS

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
        # Run the blocking input() function in a separate thread
        try:
            return await asyncio.wait_for(asyncio.to_thread(input, prompt), 
                                          timeout=timeout)
        except asyncio.TimeoutError:
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


async def serveBbgSession(bbgAioServer, bbgManager) -> None:

    listenAddr = f"{globalOptions.grpchost}:{globalOptions.grpcport}"
    add_BbgServicer_to_server(bbgManager, bbgAioServer)

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
    await bbgManager.close()
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

class SessionServicer(BbgServicer):
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


    def open(self):
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
            self.done.set()
        else:
            logger.debug(f"Session opened")

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

        # hhhh historical data request prep
        clientid = self.makeClientID(context)
        topicstr = ",".join(request.topics)
        logger.info(f"Received historical data request {topicstr} from {clientid}")

        if not request.HasField("start"):
            start = protoTimestamp()
            start.FromDatetime(dt.datetime.now() - dt.timedelta(days=365))
            request.start.CopyFrom(start)

        if not request.HasField("end"):
            end = protoTimestamp()
            end.FromDatetime(dt.datetime.now())
            request.end.CopyFrom(end)

        if not request.fields:
            request.fields.extend(["LAST_PRICE"])

        q = self.manager.Queue()
        
        # hhhh historical data request send to bbg

        logger.info(f"Requesting historical data {request}")
        success, bbgRequest = self._createEmptyRequest("HistoricalDataRequest")
        if not success:
            return []
        dtstart = request.start.ToDatetime().strftime("%Y%m%d")
        dtend = request.end.ToDatetime().strftime("%Y%m%d")
        requestDict = {"securities": request.topics,
                       "fields": request.fields,
                       "startDate": dtstart,
                       "endDate": dtend} # TODO OVERRIDES
        bbgRequest.fromPy(requestDict)
        # create a random 32-character string as the correlationId
        corrString = f"hist:{clientid}:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        self.correlators[corrString] = {"q": q,
                                       "request": request, 
                                       "clientid": clientid}
        self.session.sendRequest(bbgRequest, correlationId=correlid)

        # hhhh historical data request responde 
        messageList = []
        while True:
            # get from multprocessing queue from async
            msg = await self.loop.run_in_executor(None, q.get)
            messageList.append(msg[1]["data"])
            if not msg[1]["partial"]:
                break
        if messageList:    
            result = buildHistoricalDataResponse(messageList)
            return result 
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")



    async def intradayBarRequest(self, request: IntradayBarRequest, 
                                 q: multiprocessing.Queue,
                                 clientid: string) -> IntradayBarResponse:
        """ request intraday bar data """
        logger.info(f"Requesting intraday bar data {str(request.topic)}")
        success, bbgRequest = self._createEmptyRequest("IntradayBarRequest")
        if not success:
            return []
        dtstart = request.start.ToDatetime().strftime("%Y-%m-%dT%H:%M:%S")
        dtend = request.end.ToDatetime().strftime("%Y-%m-%dT%H:%M:%S")
        requestDict = {"security": request.topic,
                       "eventType": "TRADE",
                       "startDateTime": dtstart,
                       "endDateTime": dtend,
                       "gapFillInitialBar": "true",
                       "interval": request.interval} # TODO OVERRIDES
        bbgRequest.fromPy(requestDict)
        # create a random 32-character string as the correlationId
        corrString = f"bar:{clientid}:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        self.correlators[corrString] = {"q": q,
                                       "request": request, 
                                       "clientid": clientid}
        self.session.sendRequest(bbgRequest, correlationId=correlid)


    async def referenceDataRequest(self, request: ReferenceDataRequest,
                                   q: multiprocessing.Queue,
                                   clientid: string) -> ReferenceDataResponse:
        """ request reference data """
        logger.info(f"Requesting reference data {request}")
        success, bbgRequest = self._createEmptyRequest("ReferenceDataRequest")
        if not success:
            return []
        logger.info(f"setting securities {request.topics}")
        requestDict = {"securities": request.topics,
                       "fields": request.fields}
        if request.overrides:
            requestDict["overrides"] = request.overrides
        bbgRequest.fromPy(requestDict)
        corrString = f"ref:{clientid}:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        self.correlators[corrString] = {"q": q,
                                       "request": request, 
                                       "clientid": clientid}
        self.session.sendRequest(bbgRequest, correlationId=correlid)


    # -------------- DEBUG ---------------

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

    # -------------- !DEBUG ---------------




    def open(self):
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
            self.done.set()
        else:
            logger.debug(f"Session opened")

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

    def makeCorrelatorString(self, topic: Topic, service: str) -> str:
        intervalstr = f"interval={int(topic.interval)}"
        fieldsstr = ",".join(topic.fields)
        topicTypeName = topicType.Name(topic.topictype) # SEDOL1/TICKER/CUSIP etc
        # substring will be used as the correlation ID _and_ the subscription string
        substring = f"{service}/{topicTypeName}/{topic.topic}?fields={fieldsstr}&{intervalstr}"
        substring = f"{service}/{topic.topic}?fields={fieldsstr}&{intervalstr}" 
        return substring


    async def sub(self, 
                  topicList: TopicList, 
                  subq: multiprocessing.Queue,
                  clientid: string):
        """ subscribe to a list of topics """
        
        # make sure the service is open
        _success, barservice = self._getService("BarSubscribe")
        _success, tickservice = self._getService("Subscribe")
        barsublist = blpapi.SubscriptionList()
        ticksublist = blpapi.SubscriptionList()
        for t in topicList.topics:
            if t.subtype == subscriptionType.BAR:
                substring = self.makeCorrelatorString(t, barservice)
                correlid = blpapi.CorrelationId(substring)
                barsublist.add(substring, correlationId=correlid)
            else:
                substring = self.makeCorrelatorString(t, tickservice)
                correlid = blpapi.CorrelationId(substring) 
                ticksublist.add(substring, correlationId=correlid)
            self.correlators[substring] = {"q": subq, 
                                           "topic": t, 
                                           "clientid": clientid,
                                           "correlid": correlid}
            logger.info(f"Subscribing {substring} for {clientid}")
        if barsublist.size() > 0:
            self.session.subscribe(barsublist)
        if ticksublist.size() > 0:
            self.session.subscribe(ticksublist)


    async def subscriptionInfo(self, clientid, q) -> TopicList:
        """ get the current subscription list """
        tl = TopicList()
        for v in self.correlators.values():
            if v["clientid"] == clientid:
                tl.topics.append(v["topic"])
        q.put(tl.SerializeToString())


    async def unsub(self, topicList: TopicList, unsubIsCancel = False):
        """ unsubscribe from a list of topics. Note removal from the 
        correlators only happens when the event handler receives the
        unsubscription event.
        unsubIsCancel is to differentiate between explicit cancellation
        and stream cancellation termination where all initial correlators will be sent
        and some may have been unsubbed already, so don't warn about them"""
        _success, barservice = self._getService("BarSubscribe")
        _success, tickservice = self._getService("Subscribe")
        substrings = [] # will refer to these later to make sure unsubbed
        bbgunsublist = blpapi.SubscriptionList()
        for t in topicList.topics:
            if t.subtype == subscriptionType.BAR:
                service = self.servicesOpen["BarSubscribe"]
            else:
                service = self.servicesOpen["Subscribe"]
            substring = self.makeCorrelatorString(t, service)
            correlator = self.correlators.get(substring)
            if not correlator:
                if not unsubIsCancel: # broad based stream cancellation unsub so may not be there
                    logger.warning(f"Correlator not found for {substring}")
                continue
            else:
                logger.info(f"Unsubscribing: {makeTopicString(t)}")
                substrings.append(substring)
                correlid = correlator["correlid"]
                bbgunsublist.add(substring, correlationId=correlid) 
        if substrings:
            print(bbgunsublist)
            print(substrings)
            self.session.unsubscribe(bbgunsublist)



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
                            console.print(f"[bold cyan]{k},  {v['clientid']=} ")
                    case ("key", b"t"):
                        checkThreads(processes=False, colour="green")
                    case ("key", b"i"): # DEBUG
                        await self.serviceInfo()
                    case ("request", "historicalDataRequest", (serquest, q, clientid)):
                        request = HistoricalDataRequest.FromString(serquest)
                        await self.historicalDataRequest(request, q, clientid)
                    case ("request", "intradayBarRequest", (serquest, q, clientid)):
                        request = IntradayBarRequest.FromString(serquest)
                        await self.intradayBarRequest(request, q, clientid)
                    case ("request", "referenceDataRequest", (serquest, q, clientid)):
                        request = ReferenceDataRequest.FromString(serquest)
                        await self.referenceDataRequest(request, q, clientid)
                    case ("request", "sub", (serquest, subq, clientid)):
                        topicList = TopicList.FromString(serquest)
                        await self.sub(topicList, subq, clientid)
                    case ("request", "unsub", (serquest,)):
                        topicList = TopicList.FromString(serquest)
                        await self.unsub(topicList)
                    case ("request", "unsubcancel", (serquest,)):
                        topicList = TopicList.FromString(serquest)
                        await self.unsub(topicList, unsubIsCancel=True)
                    case ("request", "subscriptionInfo", (clientid, q)):
                        tlist = await self.subscriptionInfo(clientid, q)
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


            
# ----------------- gRPC method implementations ----------------------



class ConnectionLoggingInterceptor(ServerInterceptor):
    """ DEBUG connections to server"""
    async def intercept_service(self, continuation, handler_call_details):
        console.print(f"[cyan]Incoming connection: {handler_call_details.method}")
        # Proceed with the normal handling of the RPC
        return await continuation(handler_call_details)


def runSessionRunner(options, comq, done):
    """ now we're already in a new process """

    async def start_session_runner():
        logger.info("Starting session runner")

        # TODO HERE IS WHERE YOU WILL PUT THE SESSION GRPC SERVER
        sessionAioServer = grpc.aio.server()
        sessionServicer = SessionServicer(options, comq, done) # this is the nested gRPC server
        sessionServicer.open()
        add_BbgServicer_to_server(sessionServicer, sessionAioServer)
        sessionAioServer.add_insecure_port('unix:////./pipe/my_named_pipe')
        sessionAioServer.start()
        try:
            # Keep the event loop running
            await asyncio.Future()  # Run until cancelled
        except asyncio.CancelledError:
            logger.info("SessionRunner event loop stopped.")
        finally:
            await sessionRunner.close()

    # Set up and run the asyncio event loop that the SessionServicer will run in
    try:
        loop = asyncio.new_event_loop() # the 
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_session_runner())
    except KeyboardInterrupt:
        console.print("[bold red on white]SessionRunnner stopped by keyboard interrupt.")
        done.set()
        time.sleep(1)
    finally:
        loop.close()


class Bbg(BbgServicer):
    # implements all the gRPC methods for the session manager
    # and communicates with the SessionRunner(s)

    def __init__(self, options, comq, done, manager):
        self.sessionProc = multiprocessing.Process(target=runSessionRunner, 
                                                   args=(options, comq, done), 
                                                   name="SessionRunner")
        self.sessionProc.start()
        self.options = options
        self.manager = manager
        self.comq = comq
        self.done = done
        # TODO we will need a stub here!!

    def makeClientID(self, context):
        client = dict(context.invocation_metadata()).get("client")
        return client

    async def closeSession(self):
        await self.session.close()

    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:


    async def intradayBarRequest(self, request: IntradayBarRequest,
                                  context: grpc.aio.ServicerContext) -> IntradayBarResponse:
        clientid = self.makeClientID(context)
        logger.info(f"Received intraday bar request {str(request.topic)} from {clientid}")

        if not request.HasField("start"):
            start = protoTimestamp()
            start.FromDatetime(dt.datetime.now() - dt.timedelta(days=140))
            request.start.CopyFrom(start)

        if not request.HasField("end"):
            end = protoTimestamp()
            end.FromDatetime(dt.datetime.now())
            request.end.CopyFrom(end)

        if not request.interval:
            request.interval = 5

        q = self.manager.Queue()
        messageList = []
        serquest = request.SerializeToString()
        self.comq.put(("request", "intradayBarRequest", (serquest, q, clientid)))
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, q.get)
            messageList.append(msg[1]["data"])
            if not msg[1]["partial"]:
                break
        if messageList:
            result = buildIntradayBarResponse(messageList)
            return result
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")

    async def referenceDataRequest(self, request: ReferenceDataRequest,
                                   context: grpc.aio.ServicerContext) -> ReferenceDataResponse:
        clientid = self.makeClientID(context)
        topicstr = ",".join(request.topics)
        logger.info(f"Received reference data request {topicstr} from {clientid}")
        q = self.manager.Queue()
        messageList = []
        serquest = request.SerializeToString()
        self.comq.put(("request", "referenceDataRequest", (serquest, q, clientid)))
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, q.get)
            messageList.append(msg[1]["data"])
            if not msg[1]["partial"]:
                break
        if messageList:
            result = buildReferenceDataResponse(messageList)
            return result
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")


    async def sub(self, topicList: TopicList, context: grpc.aio.ServicerContext):
        """subscribe""" 
        clientid = self.makeClientID(context)
        topicstr = ",".join([t.topic for t in topicList.topics])
        logger.info(f"Received subscription request {topicstr} from {clientid}")
        subq = self.manager.Queue()
        serquest = topicList.SerializeToString()
        self.comq.put(("request", "sub", (serquest, subq, clientid)))
        loop = asyncio.get_event_loop()
        while not self.done.is_set():
            # Get messages from the session's queue
            # async get from the queue
            try:
                msgtype, msg = await loop.run_in_executor(None, subq.get)
            except asyncio.CancelledError:
                logger.info("Subscription stream cancelled, unsubscribing.")
                self.comq.put(("request", "unsubcancel", (serquest,)))
                break
            except Exception as e:
                logger.error(f"Error in subscription stream {e}")
                break
            yield Topic.FromString(msg)
        logger.info("Subscription stream closed")


    async def unsub(self, topicList: TopicList, context: grpc.aio.ServicerContext):
        clientid = self.makeClientID(context)
        topicstr = ",".join([t.topic for t in topicList.topics])
        logger.info(f"Received unsubscription request {topicstr} from {clientid}")
        serquest = topicList.SerializeToString()
        self.comq.put(("request", "unsub", (serquest,)))
        return empty_pb2.Empty()


    async def subscriptionInfo(self, _request, 
                               context: grpc.aio.ServicerContext) -> TopicList:
        clientid = self.makeClientID(context)
        manager = Manager()
        q = manager.Queue()
        self.comq.put(("request", "subscriptionInfo", (clientid, q)))
        logger.info(f"Received subscription info request from {clientid}")
        loop = asyncio.get_event_loop()
        tlist = await loop.run_in_executor(None, q.get)
        return TopicList.FromString(tlist)


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
    bbgAioServer = grpc.aio.server(interceptors=(ConnectionLoggingInterceptor(),))
    keyAioServer = grpc.aio.server()
    manager = Manager()
    comq = manager.Queue() # communication queue
    #done = manager.Event()
    done = manager.Event()
    bbgManager = Bbg(globalOptions, comq, done, manager)
    bbgTask = asyncio.create_task(serveBbgSession(bbgAioServer, bbgManager))
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
        await asyncio.gather(bbgTask, keyTask, keypressTask)
    else:
        await asyncio.gather(bbgTask, keyTask)
    logger.info("All tasks stopped. Exiting.")
    os._exit(0)


def main():
    global globalOptions
    globalOptions = parseCmdLine()
    if globalOptions.gencerts:
        if not globalOptions.grpchost:
            print(("Must specify --grpchost xxxx where xxx is server hostname or IP address "
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
