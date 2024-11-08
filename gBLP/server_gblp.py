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
from bloomberg_pb2 import ClientID
from bloomberg_pb2 import KeyRequestId, KeyResponse
from bloomberg_pb2 import HistoricalDataRequest 
from bloomberg_pb2 import HistoricalDataResponse
from bloomberg_pb2 import IntradayBarRequest
from bloomberg_pb2 import IntradayBarResponse
from bloomberg_pb2 import SubscriptionList
from bloomberg_pb2 import SubscriptionDataResponse
from bloomberg_pb2 import Ping 
from bloomberg_pb2 import Pong 
from bloomberg_pb2 import Topic

from bloomberg_pb2_grpc import BbgServicer, KeyManagerServicer
from bloomberg_pb2_grpc import add_BbgServicer_to_server, \
    add_KeyManagerServicer_to_server

from responseParsers import (
    buildHistoricalDataResponse, 
    buildIntradayBarResponse,
    buildSubscriptionDataResponse
)

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp

from argparse import ArgumentParser, RawTextHelpFormatter

from pathlib import Path

from util.SubscriptionOptions import \
    addSubscriptionOptions, \
    setSubscriptionSessionOptions
from util.ConnectionAndAuthOptions import \
    addConnectionAndAuthOptions, \
    createSessionOptions

from EventHandler import EventHandler

from constants import (RESP_INFO, RESP_REF, RESP_SUB, RESP_BAR,
        RESP_STATUS, RESP_ERROR, RESP_ACK, DEFAULT_FIELDS, 
    MAX_MESSAGE_LENGTH)

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
        self.correlators = defaultdict(set)
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
        self.handler = EventHandler(parent = self)
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

    async def historicalDataRequest(self, request: HistoricalDataRequest, q: asyncio.Queue) -> list:
        """ request historical data """
        cid = request.cid
        logger.info(f"Requesting historical data {request}")
        success, bbgRequest = self._createEmptyRequest("HistoricalDataRequest")
        if not success:
            return []
        logger.info(f"setting securities {request.topics}")
        dtstart = request.start.ToDatetime().strftime("%Y%m%d")
        dtend = request.end.ToDatetime().strftime("%Y%m%d")
        requestDict = {"securities": request.topics,
                       "fields": request.fields,
                       "startDate": dtstart,
                       "endDate": dtend} # TODO OVERRIDES
        bbgRequest.fromPy(requestDict)
        # create a random 32-character string as the correlationId
        corrString = f"hist:{cid.name}:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        self.correlators[corrString].add((cid.name, q))
        self.session.sendRequest(bbgRequest, correlationId=correlid)


    async def intradayBarRequest(self, request: IntradayBarRequest, q: asyncio.Queue) -> IntradayBarResponse:
        """ request intraday bar data """
        cid = request.cid
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
        corrString = f"bar:{cid.name}:{makeName(alphaLength = 32, digitLength = 0)}"
        correlid = blpapi.CorrelationId(corrString)
        # queue for this request, with correlator so event handler can match it
        self.correlators[corrString].add((cid.name, q))
        self.session.sendRequest(bbgRequest, correlationId=correlid)



    # ------------ subscriptions -------------------

    async def subscribe_deprecated(self, subscriptionList: SubscriptionList, subq: asyncio.Queue):
        """ subscribe to a list of topics """
        
        # make sure the service is open
        cid = subscriptionList.cid
        success, service = self._getService("Subscribe")
        if not success:
            return SubscriptionList(cid=cid, topics=[]) # empty
        # split out the subscriptionList
        bbgsublist = blpapi.SubscriptionList()
        newRequests = SubscriptionList(cid=cid) # empty at first
        existRequests = SubscriptionList(cid=cid) # empty at first
        for t in subscriptionList.topics:
            topicTypeName = Topic.topicType.Name(t.ttype) # SEDOL1/TICKER/CUSIP etc
            corrString = f"sub:{t.name}:{topicTypeName}:{t.interval}:{t.field}" # make correlid
            # now add this to be subscribed if necessary
            if not corrString in self.correlators:    # not already subscribed 
                logger.info(f"Subscribing to {t.name} {t.ttype} {t.interval} {t.field}")
                substring = f"{service}/{topicTypeName}/{t.name}"
                intervalstr = f"interval={int(t.interval)}"
                correlid = blpapi.CorrelationId(corrString)
                bbgsublist.add(substring, t.field, intervalstr, correlid)
                newRequests.topics.append(t)
            else:
                existRequests.topics.append(t)
                logger.info(f"Already subscribed to {t.name} {topicTypeName} {t.interval} {t.field}")

            # add this topic to the correlator with this queue
            self.correlators[corrString].add((cid.name, subq))
            print(self.correlators)

        # subscribe to any securities that were not already subscribed 
        if bbgsublist.size():
            self.session.subscribe(bbgsublist)
        return newRequests


    async def subscribe(self, subscriptionList: SubscriptionList, subq: asyncio.Queue):
        """ subscribe to a list of topics """
        
        # make sure the service is open
        cid = subscriptionList.cid # NEXT THESE SHOULD BE PER STREAM

        success, service = self._getService("Subscribe")
        if not success:
            return SubscriptionList(cid=cid, topics=[]) # empty
        # split out the subscriptionList
        bbgsublist = blpapi.SubscriptionList()
        newRequests = SubscriptionList(cid=cid) # empty at first
        existRequests = SubscriptionList(cid=cid) # empty at first
        for t in subscriptionList.topics:
            topicTypeName = Topic.topicType.Name(t.ttype) # SEDOL1/TICKER/CUSIP etc
            corrString = f"sub:{t.name}:{topicTypeName}:{t.interval}:{t.field}" # make correlid
            # now add this to be subscribed if necessary
            if not corrString in self.correlators:    # not already subscribed 
                logger.info(f"Subscribing to {t.name} {t.ttype} {t.interval} {t.field}")
                substring = f"{service}/{topicTypeName}/{t.name}"
                intervalstr = f"interval={int(t.interval)}"
                correlid = blpapi.CorrelationId(corrString)
                bbgsublist.add(substring, t.field, intervalstr, correlid)
                newRequests.topics.append(t)
            else:
                existRequests.topics.append(t)
                logger.info(f"Already subscribed to {t.name} {topicTypeName} {t.interval} {t.field}")

            # add this topic to the correlator with this queue
            self.correlators[corrString].add((cid.name, subq))
            print(self.correlators)

        # subscribe to any securities that were not already subscribed 
        if bbgsublist.size():
            self.session.subscribe(bbgsublist)
        return newRequests


    async def unsubscribe(self, subscriptionList: SubscriptionList):
        """ unsubscribe from a list of topics """
        print(f"unsubcribing TODO")


    async def subscriptionInfo(self, cidname):
        """ list all subscriptions """
        logger.info(f"Getting subscription info for {cidname}")
        correls = []
        for k, v in self.correlators.items():
            for cidn, _ in v:
                if cidn == cidname:
                    correls.append(k)
        subinfolist = SubscriptionList(cid=ClientID(name=cidname))
        for c in correls:
            parts = c.split(":")
            subinfolist.topics.append(Topic(name=parts[1], 
                                            ttype=Topic.topicType.Value(parts[2]), 
                                            interval=int(parts[3]), 
                                            field=parts[4]))
        return subinfolist


    async def _sendInfo(self, command, bbgRequest):
        """ sends back structure information about the request TODO THIS IS JUST COPY PASTE FROM BLXX"""
        desc = bbgRequest.asElement().elementDefinition()
        strdesc = desc.toString()
        sendmsg = (RESP_INFO, {"request_type": command, "structure": strdesc})
        await dataq.put(sendmsg)


# ----------------- multiple sessions are managed here ----------------------


class Bbg(BbgServicer):
    # implements all the gRPC methods for the session manager
    # and communicates with the SessionRunner(s)

    def __init__(self):
        self.queues = dict()
        self.session = SessionRunner(options=globalOptions)
        self.grpc_rep = self.session.open()

    async def closeSession(self):
        await self.session.close()


    async def ping(self, request: Ping, context: grpc.aio.ServicerContext) -> Pong:
        cid = request.cid
        cidname = cid.name
        if not self.queues.get(cidname):
            self.queues[cidname] = asyncio.Queue()
        nowstamp = protoTimestamp()
        nowstamp.GetCurrentTime()
        pong = Pong(cid=cid, timestamp=nowstamp)
        return pong


    async def historicalDataRequest(self, request: HistoricalDataRequest, 
                                    context: grpc.aio.ServicerContext) -> HistoricalDataResponse:
        cidname = dict(context.invocation_metadata())["cidname"]
        if not self.queues.get(cidname):
            context.abort(grpc.StatusCode.NOT_FOUND, "Context not initialized")
        q = asyncio.Queue()
        messageList = []
        await self.session.historicalDataRequest(request, q)
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
        cidname = dict(context.invocation_metadata())["cidname"]
        if not self.queues.get(cidname):
            context.abort(grpc.StatusCode.NOT_FOUND, "Context not initialized")
        q = asyncio.Queue()
        messageList = []
        await self.session.intradayBarRequest(request, q)
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


    async def subscribe(self, subscriptionList: SubscriptionList, 
                                 context: grpc.aio.ServicerContext) -> SubscriptionDataResponse:
        subq = asyncio.Queue()
        subscribeRequests = await self.session.subscribe(subscriptionList, subq)
        while not done.is_set():
            # Get messages from the session's queue
            # async get from the queue
            try:
                msg = await subq.get() 
            except asyncio.CancelledError:
                self.session.unsubscribe(subscribeRequests)
                logger.info("Subscription stream cancelled")
                break
            response = buildSubscriptionDataResponse(msg)
            yield response
        logger.info("Subscription stream closed")


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
    print("waiting")
    await done.wait()
    print("waited")
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
