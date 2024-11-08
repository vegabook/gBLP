# colorscheme aiseered dark


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

import asyncio
import threading
import grpc
import bloomberg_pb2
import bloomberg_pb2_grpc
import random
from pathlib import Path
import datetime as dt
import time
import os
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from util.certMaker import get_conf_dir
from util.utils import makeName
import getpass
import logging
from colorama import Fore, Back, Style, init as colinit; colinit()
from collections import deque, defaultdict
import IPython
from queue import Queue
from rich.console import Console; console = Console()
#from rich.traceback import install; install()
from google.protobuf import empty_pb2

from constants import (RESP_INFO, RESP_REF, RESP_SUB, RESP_BAR,
        RESP_STATUS, RESP_ERROR, RESP_ACK, DEFAULT_FIELDS, 
        MAX_MESSAGE_LENGTH, 
        PONG_SECONDS_TIMEOUT)

TTYPETICKER = bloomberg_pb2.Topic.topicType.Value("TICKER")
TTYPESEDOL = bloomberg_pb2.Topic.topicType.Value("SEDOL1")
TTYPECUSIP = bloomberg_pb2.Topic.topicType.Value("CUSIP")


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--message', default='hello!')
parser.add_argument('--grpchost', default='localhost')
parser.add_argument('--grpcport', default='50051')
parser.add_argument('--grpckeyport', default='50052')
parser.add_argument('--delcerts', action='store_true', default=False)
args = parser.parse_args()
username = getpass.getuser()

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



class Bbg:
    def __init__(self,
                 name=None,
                 grpchost=args.grpchost,
                 grpcport=args.grpcport,
                 grpckeyport=args.grpckeyport,
                 maxdDequeSize = 10000):       # max size of deques each holding one topic

        # setup grpc
        if name is None:
            self.cid= bloomberg_pb2.ClientID(name=makeName(alphaLength=6, digitLength=3))
        else:
            self.cid = bloomberg_pb2.ClientID(name=name)
        self.grpchost = grpchost
        self.grpcport = grpcport
        self.grpckeyport = grpckeyport
        self.done = asyncio.Event()

        # setup dictionaries for subscription data
        self.subsdata = defaultdict(lambda: deque(maxlen = maxdDequeSize)) # store subscription data
        self.statusLog = [] # store status messages

        # Start the event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, args=(self.loop,), daemon=False)
        self.thread.start()
        # Run asynchronous initialization in the event loop
        self.loop_run_async(self.connect())
        self.streams = []


    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.done.wait())
        logger.info("start_loop exiting after done.set()")


    def loop_run_async(self, coro):
        """Schedules a coroutine to be run on the event loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()  # Waits until the coroutine is done and returns the result

    def loop_run_async_nowait(self, coro):
        """Schedules a coroutine to be run on the event loop without waiting."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def connect(self):
        """Connect to the gRPC server."""
        confdir = get_conf_dir()
        # Now look for keys, request them and write them if not found
        if not ((confdir / "client_certificate.pem").exists() and
                (confdir / "client_private_key.pem").exists() and
                (confdir / "ca_certificate.pem").exists()):
            await self.makeCerts()

        # Load client certificate and private key
        with open(confdir / "client_certificate.pem", "rb") as f:
            cert = f.read()
        with open(confdir / "client_private_key.pem", "rb") as f:
            key = f.read()
        # Load CA certificate to verify the server
        with open(confdir / "ca_certificate.pem", "rb") as f:
            cacert = f.read()

        # Create SSL credentials for the client
        client_credentials = grpc.ssl_channel_credentials(
            root_certificates=cacert,
            private_key=key,
            certificate_chain=cert,
        )
        hostandport = f"{self.grpchost}:{self.grpcport}"
        logger.info(f"Connecting to {hostandport}...")
        self.channel = grpc.aio.secure_channel(hostandport, client_credentials, 
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ])
        self.stub = bloomberg_pb2_grpc.BbgStub(self.channel)

        
    async def close_channel(self):
        """Close the gRPC channel asynchronously."""
        if self.channel:
            await self.channel.close()
            logger.info("Channel closed.")


    def close(self):
        logger.info("Closing streams")
        while len(self.streams) > 0:
            stream = self.streams.pop()
            stream.cancel()
        logger.info("Closing channel")
        self.loop_run_async(self.close_channel())
        logger.info("Setting done event")
        self.done.set()
        logger.info("Joining thread")
        self.thread.join()
        logger.info("Thread joined. Exiting close.")


    async def makeCerts(self):
        """Make certificates if they do not exist."""
        confdir = get_conf_dir()
        ihostandport = f"{self.grpchost}:{self.grpckeyport}"
        ichannel = grpc.aio.insecure_channel(ihostandport)
        idkey = input("Certificates not found. Input ID key: ")
        logger.info("Waiting for response from server...")
        async with ichannel as chan:
            istub = bloomberg_pb2_grpc.KeyManagerStub(chan)
            try:
                iresponse = await istub.requestKey(
                    bloomberg_pb2.KeyRequestId(id=str(idkey) + "@" + username)
                )
            except grpc.aio.AioRpcError as e:
                logger.info(f"Error: {e}")
                return
            # Make the confdir if it does not exist already
            confdir.mkdir(parents=True, exist_ok=True)
            with open(confdir / "client_certificate.pem", "wb") as f:
                f.write(iresponse.cert)
            with open(confdir / "client_private_key.pem", "wb") as f:
                f.write(iresponse.key)
            with open(confdir / "ca_certificate.pem", "wb") as f:
                f.write(iresponse.cacert)
        logger.info("Certificates written.")

    def delCerts(self):
        """Delete certificates."""
        confdir = get_conf_dir()
        for f in ["client_certificate.pem", "client_private_key.pem", "ca_certificate.pem"]:
            if (confdir / f).exists():
                (confdir / f).unlink()
        logger.info("Certificates deleted.")


    def historicalDataRequest(self, 
                              topics, 
                              fields = ["LAST_PRICE"], 
                              start = dt.datetime.today() - dt.timedelta(days=365),
                              end = dt.datetime.today(), 
                              options = None):
        return self.loop_run_async(self.async_historicalDataRequest(topics, fields, start, end, options))

    async def async_historicalDataRequest(self, topics, fields, start, end, options):
        sst = protoTimestamp()
        sst.FromDatetime(start)
        est = protoTimestamp()
        est.FromDatetime(end)
        hreq = bloomberg_pb2.HistoricalDataRequest(
            cid=self.cid,
            topics=topics,
            fields=fields,
            start=sst,
            end=est
        )
        logger.info(f"Requesting historical data: {hreq}")
        data = await self.stub.historicalDataRequest(hreq, metadata=[("cidname", self.cid.name)])
        return data

    def intradayBarRequest(self, topic,
                           start = dt.datetime.now() - dt.timedelta(days=3),
                           end = dt.datetime.now(),
                           interval = 1, 
                           options = None):
        return self.loop_run_async(self.async_intradayBarRequest(topic, start, end, interval, options))

    async def async_intradayBarRequest(self, topic, start, end, interval, options):
        sst = protoTimestamp()
        sst.FromDatetime(start)
        est = protoTimestamp()
        est.FromDatetime(end)
        bareq = bloomberg_pb2.IntradayBarRequest(
            cid=self.cid,
            topic=topic,
            start=sst,
            end=est,
            interval=interval
        )
        logger.info(f"Requesting intraday bars: {bareq}")
        data = await self.stub.intradayBarRequest(bareq, metadata=[("cidname", self.cid.name)])
        return data

    def subscribe(self, topics, 
                  fields=["LAST_PRICE"],
                  ttype=TTYPETICKER,
                  interval=2, 
                  handler = None):
        """ synchronous subscribe method """
        return self.loop_run_async(self.async_subscribe(topics, fields, ttype, interval, handler))


    async def async_subscribe(self, topics, 
                              fields,
                              ttype,
                              interval, 
                              handler):

        subs = bloomberg_pb2.SubscriptionList(
            cid=self.cid,
            topics=[
                bloomberg_pb2.Topic(
                    name=t, 
                    field=f,
                    ttype=ttype, 
                    interval=interval
                ) for t in topics for f in fields   
            ]
        )
        stream = self.stub.subscribe(subs, metadata=[("cidname", self.cid.name)])
        self.streams.append(stream)
        self.loop_run_async_nowait(self.streamHandler(stream, handler))
        logger.info("Subscription stream started.")
        return subs


    async def streamHandler(self, stream, handler):
        async for response in stream:
            try:
                if response.msgtype in (RESP_SUB, RESP_BAR):
                    self.subsdata[response.topic].append(response)
                elif response.msgtype in (RESP_STATUS, RESP_ERROR):
                    self.statusLog.append(response)
                else:
                    pass
                if handler:
                    asyncio.run_coroutine_threadsafe(handler.handle(response), self.loop)
                #if self.done.is_set():
                #    break
            except asyncio.CancelledError:
                logger.info("streamHandler was cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in streamHandler: {e}")
        logger.info("self.done is set. Exiting streamHandler.")

    def ping(self):
        return self.loop_run_async_nowait(self.async_ping())


    async def async_ping(self):
        while not self.done.is_set():
            nowstamp = protoTimestamp()
            nowstamp.GetCurrentTime()
            Ping = bloomberg_pb2.Ping(cid=self.cid, timestamp=nowstamp)
            try:
                pong = await self.stub.ping(Ping, timeout = PONG_SECONDS_TIMEOUT)
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    logger.error("Ping timeout. Closing Bbg session.")
                    self.close()
                    break
                else:
                    logger.error("Ping error:", e)
            await asyncio.sleep(1)
                
        else:
            print("Ping error:", e)


    def unsubscribe(self, topics):
        pass


    def subscriptionInfo(self):
        return self.loop_run_async(self.aysnc_subscriptionInfo())

    async def aysnc_subscriptionInfo(self):
        return await self.stub.subscriptionInfo(self.cid)

    



class Handler():
    """ Optional handler class to handle subscription responses. 
        This must be sent as a class and not as an instance, because it
        will be instantiated in the Bbg class. """

    def __init__(self, colour = "blue"):
        self.mysubsdata = defaultdict(lambda: deque(maxlen = 1000))
        self.statusLog = deque(maxlen = 1000)
        self.colour = colour
    
    async def handle(self, response):
        # this function must be present in any handler
        try:
            if response.msgtype in (RESP_SUB, RESP_BAR):
                self.statusLog.append(response)
                console.print(f"[{self.colour}]{response}[/{self.colour}]")
            else:
                self.mysubsdata[response.topic].append(response)
                console.print(f"[magenta]{response}[/magenta]")   
        except Exception as e:
            print(f"Error in handler: {e}")


def syncmain():
    bbg = Bbg(
        grpchost=args.grpchost,
        grpcport=args.grpcport,
        grpckeyport=args.grpckeyport,
        handler_class = Handler  # Optional handler class that will run in addition to defaul handler
    )

    # Request historical data
    hist = bbg.historicalDataRequest(
        ["RNO FP Equity", "MSFT US Equity", "USDZAR Curncy"],
        ["PX_LAST", "CUR_MKT_CAP"],
        dt.datetime(2023, 11, 28),
        dt.datetime(2023, 11, 30)
    )
    print(hist)

    # Request intraday bars
    intra = bbg.intradayBarRequest(topic = "USDZAR Curncy",
        start = dt.datetime(2024, 10, 28, 6, 0),
        end = dt.datetime.now(),
        interval = 1
    )
    print(intra)

    # Request intraday bars
    intra = bbg.intradayBarRequest(topic = "EURCZK Curncy",
        start = dt.datetime.now() - dt.timedelta(days=3),
        end = dt.datetime.now(),
        interval = 1
    )
    print(intra)

    subs = bbg.subscribe(["USDZAR Curncy"])

    IPython.embed()

    return bbg


def checkThreads():
    for th in threading.enumerate(): 
        if not th.name == "MainThread":
            console.print(f"[bold magenta]Thread {th.name} is still running[/bold magenta]")

if __name__ == "__main__":
    # TODO move certs into another class
    if args.delcerts:
        bbg = Bbg()
        bbg.delCerts()
    else:
        try:
            bbg = Bbg()
            pong = bbg.ping() # start by pinging
            hist = bbg.historicalDataRequest(
                ["RNO FP Equity", "MSFT US Equity", "USDZAR Curncy"],
                ["PX_LAST", "CUR_MKT_CAP"],
                dt.datetime(2023, 11, 28),
                dt.datetime(2023, 11, 30)
            )
            print(hist)

            # Request intraday bars
            intra = bbg.intradayBarRequest(topic = "USDZAR Curncy",
                start = dt.datetime(2024, 10, 28, 6, 0),
                end = dt.datetime.now(),
                interval = 1
            )
            print(intra)

            # Request intraday bars
            intra = bbg.intradayBarRequest(topic = "EURCZK Curncy",
                start = dt.datetime.now() - dt.timedelta(days=3),
                end = dt.datetime.now(),
                interval = 1
            )
            print(intra)

            handler_zar = Handler("green")
            subs = bbg.subscribe(["USDZAR Curncy"], handler = handler_zar)

            handler_eur = Handler("blue")
            subs = bbg.subscribe(["EURCZK Curncy"], handler = handler_eur)

            IPython.embed()
        except KeyboardInterrupt:
            print("Keyboard interrupt")
        finally:
            pass




