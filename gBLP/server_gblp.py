# colorscheme blue dark

# Copyright 2021 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from gBLP.util.utils import makeName, printLicence, checkThreads, exitNotNT, printBeta
exitNotNT() # make sure we're on Windows otherwise exit. 

from rich.console import Console
from rich.pretty import pprint
from rich.logging import RichHandler
import logging

# Create a Rich console instance
console = Console()

class CustomRichHandler(RichHandler):
    def emit(self, record):
        # Use the formatter to generate the full log string
        log_entry = self.format(record)
        if record.levelno == logging.ERROR:
            # Print the entire formatted log entry in red
            console.print(f"[bold red]{log_entry}[/bold red]")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(processName)s | %(funcName)s | %(message)s"
)
logger = logging.getLogger(__name__)  # Get the current module's logger
custom_handler = CustomRichHandler()
logger.addHandler(custom_handler)  # Add the custom handler


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
import traceback
import os

import multiprocessing # no more thread leaking from blpapi. Wrap and shut. 
from multiprocessing import Manager

import grpc
from gBLP.bloomberg_pb2 import KeyRequestId, KeyResponse
from gBLP.bloomberg_pb2 import HistoricalDataRequest 
from gBLP.bloomberg_pb2 import HistoricalDataResponse
from gBLP.bloomberg_pb2 import IntradayBarRequest
from gBLP.bloomberg_pb2 import IntradayBarResponse
from gBLP.bloomberg_pb2 import ReferenceDataRequest
from gBLP.bloomberg_pb2 import ReferenceDataResponse 
from gBLP.bloomberg_pb2 import Topic
from gBLP.bloomberg_pb2 import TopicList
from gBLP.bloomberg_pb2 import topicType
from gBLP.bloomberg_pb2 import subscriptionType

from gBLP.bloomberg_pb2_grpc import BbgServicer, KeyManagerServicer
from gBLP.bloomberg_pb2_grpc import add_BbgServicer_to_server, \
    add_KeyManagerServicer_to_server

from gBLP.responseParsers import (
    buildHistoricalDataResponse, 
    buildIntradayBarResponse,
    buildReferenceDataResponse
)

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from google.protobuf import empty_pb2
# import value

from argparse import ArgumentParser, RawTextHelpFormatter

from pathlib import Path

from gBLP.util.SubscriptionOptions import \
    addSubscriptionOptions, \
    setSubscriptionSessionOptions
from gBLP.util.ConnectionAndAuthOptions import \
    addConnectionAndAuthOptions, \
    createSessionOptions

from gBLP.EventRouter import EventRouter

from gBLP.util.certMaker import get_conf_dir, make_client_certs, make_all_certs
from gBLP.util.utils import makeName, printLicence, checkThreads

from cryptography.hazmat.primitives import serialization, hashes



# ----------------- global variables ----------------------



NUMBER_OF_REPLY = 10


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
        logging.info("Serving keyRequest request %s", request)
        accept = await self.input_timeout((f"Received request from {context.peer()}"
                        f" with id {request.id}. Accept? (y/n) "), 5)
        if accept is None:
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "Request timed out")
        if accept.lower() == "y":
            key, cert, cacert = make_client_certs(globalOptions.grpchost, get_conf_dir())
            bcacert = cacert.public_bytes(serialization.Encoding.PEM)
            logger.info(f"Key request granted for {request.id} and {context.peer()}")
            return KeyResponse(key=key, cert=cert, cacert=bcacert)
        else:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Request denied")


async def serveBbgSession(bbgAioServer, bbgManager) -> None:

    listenAddr = f"{globalOptions.grpchost}:{globalOptions.grpcport}"
    add_BbgServicer_to_server(bbgManager, bbgAioServer)

    # first check if the certs are there
    confdir = get_conf_dir()
    if not ((confdir / "server_certificate.pem").exists() and \
            (confdir / "server_private_key.pem").exists() and \
            (confdir / "ca_certificate.pem").exists()):
        yn = input("Certificates not found. Make them? (y/n) ")
        if yn.lower() == "y":
            make_all_certs(str(globalOptions.grpchost), confdir)
        else:
            print("Exiting.")


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
    logging.info(f"Starting session server on {listenAddr}")
    await bbgAioServer.wait_for_termination()
    await bbgManager.close()
    logging.info("Sessions server stopped.")
    #raise # propagate


async def keySession(keyAioServer) -> None:

    keyListenAddr = f"{globalOptions.grpchost}:{globalOptions.grpckeyport}"
    add_KeyManagerServicer_to_server(KeyManager(), keyAioServer)
    keyAioServer.add_insecure_port(keyListenAddr) # this listens without credentials

    await keyAioServer.start()
    logging.info(f"Starting key server on {keyListenAddr}")
    await keyAioServer.wait_for_termination()



# -------------------- individual session handler ----------------------

class SessionRunner(object):
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
                                    q: multiprocessing.Queue,
                                    clientid: string) -> list:
        """ request historical data """
        logger.info(f"Requesting historical data {request}")
        success, bbgRequest = self._createEmptyRequest("HistoricalDataRequest")
        if not success:
            return []
        logger.info(f"setting securities {request.topics}")
        dtstart = request.start.ToDatetime().strftime("%Y%m%d")
        dtend = request.end.ToDatetime().strftime("%Y%m%d")
        for t in request.topics:
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
        q.put(tl)


    async def unsub(self, topicList: TopicList):
        """ unsubscribe from a list of topics. Note removal from the 
        correlators only happens when the event handler receives the
        unsubscription event """
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
            logger.info(f"Unsubscribing {substring}")
            correlator = self.correlators.get(substring)
            if not correlator:
                logger.error(f"Correlator not found for {substring}")
                continue
            substrings.append(substring)
            correlid = correlator["correlid"]
            bbgunsublist.add(substring, correlationId=correlid) 
        if substrings:
            self.session.unsubscribe(bbgunsublist)



    async def listenComq(self):
        """Listen for messages from the grpc handler"""
        while not self.done.is_set():
            try:
                msg = await asyncio.to_thread(self.comq.get, timeout=0.1)
                # Process the message here
                match msg:
                    case ("key", b"c"):
                        console.print(f"[bold cyan]Number of correlators: {len(self.correlators)}")
                        for k in self.correlators.keys():
                            console.print(f"[cyan]{k}")
                    case ("key", b"t"):
                        checkThreads(processes=False, colour="green")
                    case ("request", "historicalDataRequest", (request, q, clientid)):
                        await self.historicalDataRequest(request, q, clientid)
                    case ("request", "intradayBarRequest", (request, q, clientid)):
                        await self.intradayBarRequest(request, q, clientid)
                    case ("request", "referenceDataRequest", (request, q, clientid)):
                        await self.referenceDataRequest(request, q, clientid)
                    case ("request", "sub", (topicList, subq, clientid)):
                        await self.sub(topicList, subq, clientid)
                    case ("request", "unsub", (topicList,)):
                        await self.unsub(topicList)
                    case ("request", "subscriptionInfo", (clientid, q)):
                        tlist = await self.subscriptionInfo(clientid, q)
                    case ("request", "close"):
                        self.done.set()
            except queue.Empty:
                continue  # No message; keep looping
            except asyncio.CancelledError:
                logger.info("CancelledError")
                self.done.set
                break
            except Exception as e:
                logger.error(f"Error in comq listener: {e}")
                break
        logger.info("Comq listener stopped.")
        await self.close()


            
# ----------------- multiple sessions are managed here ----------------------

def runSessionRunner(options, comq, done):

    async def start_session_runner():
        logger.info("Starting session runner")
        sessionRunner = SessionRunner(options, comq, done)
        sessionRunner.open()
        try:
            # Keep the event loop running
            await asyncio.Future()  # Run until cancelled
        except asyncio.CancelledError:
            logger.info("SessionRunner event loop stopped.")
        finally:
            await sessionRunner.close()

    # Set up and run the asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_session_runner())
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

    def makeClientID(self, context):
        client = dict(context.invocation_metadata())["client"]
        ip = context.peer().split(":")[1]
        return f"{client}:{ip}"

    async def closeSession(self):
        await self.session.close()

    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:
        clientid = self.makeClientID(context)
        topicstr = ",".join(request.topics)
        logger.info(f"Received historical data request {topicstr} from {clientid}")
        q = self.manager.Queue()
        messageList = []
        self.comq.put(("request", "historicalDataRequest", (request, q, clientid)))
        loop = asyncio.get_event_loop()
        while True:
            # get from multprocessing queue from async
            msg = await loop.run_in_executor(None, q.get)
            messageList.append(msg[1]["data"])
            if not msg[1]["partial"]:
                break
        if messageList:    
            result = buildHistoricalDataResponse(messageList)
            return result 
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")


    async def intradayBarRequest(self, request: IntradayBarRequest,
                                  context: grpc.aio.ServicerContext) -> IntradayBarResponse:
        clientid = self.makeClientID(context)
        logger.info(f"Received intraday bar request {str(request.topic)} from {clientid}")
        q = self.manager.Queue()
        messageList = []
        self.comq.put(("request", "intradayBarRequest", (request, q, clientid)))
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
        self.comq.put(("request", "referenceDataRequest", (request, q, clientid)))
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
        self.comq.put(("request", "sub", (topicList, subq, clientid)))
        loop = asyncio.get_event_loop()
        while not self.done.is_set():
            # Get messages from the session's queue
            # async get from the queue
            try:
                msg = await loop.run_in_executor(None, subq.get)
            except asyncio.CancelledError:
                logger.info("Subscription stream cancelled, unsubscribing.")
                self.comq.put(("request", "unsub", (topicList, subq, clientid)))
                break
            except Exception as e:
                logger.error(f"Error in subscription stream {e}")
                break
            yield msg
        logger.info("Subscription stream closed")


    async def unsub(self, topicList: TopicList, context: grpc.aio.ServicerContext):
        clientid = self.makeClientID(context)
        logger.info(f"Unsubscribing {topicList} for {clientid}")
        self.comq.put(("request", "unsub", (topicList,)))
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
        return tlist

    async def close(self):
        self.comq.put(("key", b"q"))
        self.sessionProc.terminate()


async def keypressDetector(comq, done):
    while not done.is_set():
        # Offload the blocking part to a different thread
        key = await asyncio.to_thread(check_keypress)
        if key is not None:
            logger.debug(f"Keypress detected: {key}")
        match key:
            case b'q':
                print("Q pressed")
                done.set()
            case b't':
                checkThreads()
                comq.put(("key", b"t"))
            case b'c':
                # TODO fix the comq below
                comq.put(("key", b"c"))
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


async def main(globalOptions):
    bbgAioServer = grpc.aio.server()
    keyAioServer = grpc.aio.server()
    manager = Manager()
    comq = manager.Queue() # communication queue
    #done = manager.Event()
    done = manager.Event()
    bbgManager = Bbg(globalOptions, comq, done, manager)
    bbgTask = asyncio.create_task(serveBbgSession(bbgAioServer, bbgManager))
    keyTask = asyncio.create_task(keySession(keyAioServer))
    console.print("[bold blue]--------------------------")
    console.print("[bold red on white blink]Press Q to stop the server")
    console.print("[bold blue]--------------------------")
    keypressTask =asyncio.create_task(keypressDetector(comq, done)) 
    await asyncio.to_thread(done.wait)
    logger.info("done waiting for. Stopping gRPC servers...")
    await bbgAioServer.stop(grace=3)
    logger.info("gRPC server stopped.") 
    await keyAioServer.stop(grace=3)
    logger.info("Key server stopped.")
    logger.info("Gathering asyncio gRPC task wrappers...")
    await asyncio.gather(bbgTask, keyTask, keypressTask)
    logger.info("All tasks stopped. Exiting.")
    os._exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    printBeta()
    printLicence()
    globalOptions = parseCmdLine()
    if globalOptions.gencerts:
        confdir = get_conf_dir()
        make_all_certs(str(globalOptions.grpchost), confdir)
    elif globalOptions.delcerts:
        confdir = get_conf_dir()
        for f in confdir.glob("*.pem"):
            f.unlink()
        print("Deleted all certificates. Run --gencerts to make new ones.")
    else:
        try:
            asyncio.run(main(globalOptions))
            logger.info("asyncio main() exited")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            console.print("[bold magenta on white]You should press <Enter> to stop the server.")
            console.print("[bold white on red] Killing all threads and processes.")
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
