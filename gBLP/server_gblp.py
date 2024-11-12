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

import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import logging
import string
import random
from collections import defaultdict
import json
import datetime as dt
import os
import threading
import signal
from functools import partial
import queue
import blpapi
import msvcrt
import traceback

import grpc
from bloomberg_pb2 import KeyRequestId, KeyResponse
from bloomberg_pb2 import HistoricalDataRequest 
from bloomberg_pb2 import HistoricalDataResponse
from bloomberg_pb2 import IntradayBarRequest
from bloomberg_pb2 import IntradayBarResponse
from bloomberg_pb2 import Topic
from bloomberg_pb2 import TopicList
from bloomberg_pb2 import Ping 
from bloomberg_pb2 import Pong 
from bloomberg_pb2 import topicType
from bloomberg_pb2 import subscriptionType

from bloomberg_pb2_grpc import BbgServicer, KeyManagerServicer
from bloomberg_pb2_grpc import add_BbgServicer_to_server, \
    add_KeyManagerServicer_to_server

from responseParsers import (
    buildHistoricalDataResponse, 
    buildIntradayBarResponse,
)

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from google.protobuf import empty_pb2
# import value

from argparse import ArgumentParser, RawTextHelpFormatter

from pathlib import Path

from util.SubscriptionOptions import \
    addSubscriptionOptions, \
    setSubscriptionSessionOptions
from util.ConnectionAndAuthOptions import \
    addConnectionAndAuthOptions, \
    createSessionOptions

from EventRouter import EventRouter

from util.certMaker import get_conf_dir, make_client_certs, make_all_certs
from util.utils import makeName
from cryptography.hazmat.primitives import serialization, hashes

from rich.console import Console; console = Console()
from rich.traceback import install; install()


done = asyncio.Event() # signal to stop the subscription stream loop

# logging

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

globalOptions = parseCmdLine()


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


async def serveBbgSession(bbgAioServer) -> None:

    listenAddr = f"{globalOptions.grpchost}:{globalOptions.grpcport}"
    bbgManager = Bbg()
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
    logging.info("Key server stopped.")



# -------------------- individual session handler ----------------------

class SessionRunner(object):
    def __init__(self, options):
        self.interval = options.interval # subscription interval
        self.maxEventQueueSize = 10000
        self.servicesOpen = dict()
        self.correlators = dict()
        self.alive = False
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
        self.subq = asyncio.Queue()
        self.numDispatcherThreads = 1 # if > 1 then threaded dispatchers will be created
        self.loop = asyncio.get_event_loop() # used by the event handler
        self.open()


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
        sessionOptions = createSessionOptions(globalOptions) 
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
            self.alive = False
        else:
            logger.info("Session started.")
            self.alive = True
        # return all the details over gRPC
        logger.debug(f"Session opened")

    async def close(self):
        """ close the session """
        self.session.stop()
        if self.numDispatcherThreads > 1:
            self.eventDispatcher.stop()
        self.alive = False
        logger.info(f"Bloomberg session closed")

    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    q: asyncio.Queue,
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
                                 q: asyncio.Queue,
                                 clientid: string) -> IntradayBarResponse:
        """ request intraday bar data """
        logger.info(f"Requesting intraday bar data {request}")
        success, bbgRequest = self._createEmptyRequest("IntradayBarRequest")
        if not success:
            return []
        logger.info(f"setting security {request.topic}")
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



    # ------------ subscriptions -------------------

    def makeCorrelatorString(self, topic: Topic, service) -> str:
        intervalstr = f"interval={int(topic.interval)}"
        fieldsstr = ",".join(topic.fields)
        topicTypeName = topicType.Name(topic.topictype) # SEDOL1/TICKER/CUSIP etc
        substring = f"{service}/{topicTypeName}/{topic.topic}?fields={fieldsstr}&{intervalstr}"
        return substring

    async def sub(self, topicList: TopicList, 
                        subq: asyncio.Queue, 
                        clientid: string) -> bool:
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
                                           "clientid": clientid}  
            logger.info(f"Subscribing {substring} for {clientid}")
        if barsublist.size() > 0:
            self.session.subscribe(barsublist)
        if ticksublist.size() > 0:
            self.session.subscribe(ticksublist)
        return True

    async def subscriptionInfo(self, clientid) -> TopicList:
        """ get the current subscription list """
        tl = TopicList()
        for v in self.correlators.values():
            if v["clientid"] == clientid:
                tl.topics.append(v["topic"])
        return tl


    async def unsub(self, topicList: TopicList):
        """ unsubscribe from a list of topics """
        _success, barservice = self._getService("BarSubscribe")
        _success, tickservice = self._getService("Subscribe")
        for t in topicList.topics:
            if t.subtype == subscriptionType.BAR:
                service = self.servicesOpen["BarSubscribe"]
            else:
                service = self.servicesOpen["Subscribe"]
            substring = self.makeCorrelatorString(t, service)
            logger.info(f"Unsubscribing {substring}")
            correlid = blpapi.CorrelationId(substring)
            bbgunsublist = blpapi.SubscriptionList()
            #bbgunsublist.add(substring, correlationId=correlid)
            bbgunsublist.add(correlid)
        if bbgunsublist.size() > 0:
            self.session.unsubscribe(bbgunsublist)



# ----------------- multiple sessions are managed here ----------------------


class Bbg(BbgServicer):
    # implements all the gRPC methods for the session manager
    # and communicates with the SessionRunner(s)

    def __init__(self):
        self.queues = dict()
        self.session = SessionRunner(options=globalOptions)
        self.grpc_rep = self.session.open()

    def makeClientID(self, context):
        client = dict(context.invocation_metadata())["client"]
        ip = context.peer().split(":")[1]
        return f"{client}:{ip}"

    async def closeSession(self):
        await self.session.close()


    async def ping(self, request: Ping, context: grpc.aio.ServicerContext) -> Pong:
        nowstamp = protoTimestamp()
        nowstamp.GetCurrentTime()
        pong = Pong(timestamp=nowstamp)
        return pong


    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:
        clientid = self.makeClientID(context)
        logger.info(f"Received historical data request {request} from {clientid}")
        q = asyncio.Queue()
        messageList = []
        await self.session.historicalDataRequest(request, q, clientid)
        while True:
            msg = await q.get()
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
        logger.info(f"Received intraday bar request {request} from {clientid}")
        q = asyncio.Queue()
        messageList = []
        await self.session.intradayBarRequest(request, q, clientid)
        while True:
            msg = await q.get()
            messageList.append(msg[1]["data"])
            if not msg[1]["partial"]:
                break
        if messageList:
            result = buildIntradayBarResponse(messageList)
            return result
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Data not found")


    async def sub(self, topicList: TopicList, context: grpc.aio.ServicerContext):
        """subscribe""" 
        clientid = self.makeClientID(context)
        subq = asyncio.Queue()
        success = await self.session.sub(topicList, subq, clientid)
        if not success:
            context.abort(grpc.StatusCode.NOT_FOUND, "Failed to subscribe")
        while not done.is_set():
            # Get messages from the session's queue
            # async get from the queue
            try:
                msg = await subq.get() 
            except asyncio.CancelledError:
                await self.session.unsub(topicList)
                logger.info("Subscription stream cancelled")
                break
            except Exception as e:
                logger.error(f"Error in subscription stream {e}")
                break
            yield msg
        logger.info("Subscription stream closed")


    async def unsub(self, topicList: TopicList, context: grpc.aio.ServicerContext):
        clientid = self.makeClientID(context)
        logger.info(f"Unsubscribing {topicList} for {clientid}")
        await self.session.unsub(topicList)
        return empty_pb2.Empty()


    async def subscriptionInfo(self, _request, 
                               context: grpc.aio.ServicerContext) -> TopicList:
        clientid = self.makeClientID(context)
        logger.info(f"Received subscription info request from {clientid}")
        tlist = await self.session.subscriptionInfo(clientid)
        return tlist



    async def close(self):
        await self.session.close()


async def keypressDetector():
    while not done.is_set():
        # Offload the blocking part to a different thread
        key = await asyncio.to_thread(check_keypress)
        if key == b'q':
            print("Q pressed")
            done.set()
        elif key == b't':
            printThreads()
        await asyncio.sleep(0.1)
    logger.info("Keypress detector stopped.")


def check_keypress():
    # This function will be executed in a separate thread
    if msvcrt.kbhit():
        return msvcrt.getch()
    return None

def printThreads(id = ""):
    console.print(f"[bold magenta]----------------------------------------------------------------{id}")
    for th in threading.enumerate(): 
        if not th.name == "MainThread":
            console.print(f"[bold magenta]Thread {th.name} is running[/bold magenta]")

async def main():
    bbgAioServer = grpc.aio.server()
    keyAioServer = grpc.aio.server()
    bbgTask = asyncio.create_task(serveBbgSession(bbgAioServer))
    keyTask = asyncio.create_task(keySession(keyAioServer))
    console.print("[bold red on white blink]Press Q to stop the server")
    console.print("[bold blue]--------------------------------")
    keypressTask =asyncio.create_task(keypressDetector()) 
    await done.wait()
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
    logging.basicConfig(level=logging.INFO)
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
            asyncio.run(main())
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
