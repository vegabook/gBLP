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
from rich.traceback import install; install()
from google.protobuf import empty_pb2

from constants import (RESP_INFO, RESP_REF, RESP_SUB, RESP_BAR,
        RESP_STATUS, RESP_ERROR, RESP_ACK, DEFAULT_FIELDS)

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
                 handler_class = None, #This is a class
                 grpchost="localhost",
                 grpcport=50051,
                 grpckeyport=50052,
                 maxdDequeSize = 10000):       # max size of deques each holding one topic
        if name is None:
            self.cid= bloomberg_pb2.ClientID(name=makeName(alphaLength=6, digitLength=3))
        else:
            self.cid = bloomberg_pb2.ClientID(name=name)
        self.grpchost = grpchost
        self.grpcport = grpcport
        self.grpckeyport = grpckeyport
        self.alive = False
        self.done = asyncio.Event()
        if handler_class is not None:
            self.handler = handler_class() # instantiate
        else:
            self.handler = None
        self.subsdata = defaultdict(lambda: deque(maxlen = maxdDequeSize)) # store subscription data
        self.statusLog = [] # store status messages
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, args=(self.loop,), daemon=False)
        self.thread.start()
        # Run asynchronous initialization in the event loop
        self.run_async(self.async_init())
        self.stream = self.stub.subscriptionStream(empty_pb2.Empty(), metadata=[("cidname", self.cid.name)])
        self.run_async_nowait(self.subscriptionsStream(self.stream))
        logger.info("Subscription stream started.")
        self.alive = True
        self.subscriptionList = bloomberg_pb2.SubscriptionList(cid=self.cid)


    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.done.wait())
        except asyncio.CancelledError:
            logger.info("Event loop cancelled.")
        finally:
            logger.info("Outta here")
            checkThreads() # DEBUG


    def run_async(self, coro):
        """Schedules a coroutine to be run on the event loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()  # Waits until the coroutine is done and returns the result

    async def async_init(self):
        await self.connect()

    def run_async_nowait(self, coro):
        """Schedules a coroutine to be run on the event loop without waiting."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def makeCerts(self):
        """Make certificates if they do not exist."""
        confdir = get_conf_dir()
        ihostandport = f"{self.grpchost}:{self.grpckeyport}"
        ichannel = grpc.aio.insecure_channel(ihostandport)  # Insecure for keys
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
        self.channel = grpc.aio.secure_channel(hostandport, client_credentials)
        self.stub = bloomberg_pb2_grpc.BbgStub(self.channel)


    def close(self):
        if self.alive:
            logger.info("Closing stream")
            self.stream.cancel()
            logger.info("Running async shutdown")
            self.run_async(self.shutdown())
            # Stop the event loop and thread
            logger.info("Joining thread")
            self.thread.join()
            logger.info("Setting alive False")
            self.alive = False
        else:
            logger.info("Session already closed.")


    async def shutdown(self):
        logger.info("closing grpc session")
        logger.info("Obtaining all tasks")
        tasks = [task for task in asyncio.all_tasks(self.loop) if task is not asyncio.current_task(self.loop)]
        for task in tasks:
            logger.info(f"Cancelling task: {task}")
            task.cancel()
        os._exit(0)
        logger.info("Gathering tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        # Stop the event loop
        logger.info("Stopping loop")
        self.done.set()
        self.loop.stop()


    def historicalDataRequest(self, 
                              topics, 
                              fields = ["LAST_PRICE"], 
                              start = dt.datetime.today() - dt.timedelta(days=365),
                              end = dt.datetime.today()):
        return self.run_async(self.async_historicalDataRequest(topics, fields, start, end))

    async def async_historicalDataRequest(self, topics, fields, start, end):
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
        data = await self.stub.historicalDataRequest(hreq)
        return data


    def subscribe(self, topics, 
                  fields=["LAST_PRICE"],
                  type="TICKER",
                  interval=2):
        """ synchronous subscribe method """
        return self.run_async(
            self.async_subscribe(topics, fields, type, interval)
        )

    async def async_subscribe(self, topics, 
                              fields=["LAST_PRICE"],
                              type="TICKER",
                              interval=2):
        sub = bloomberg_pb2.SubscriptionList(
            cid=self.cid,
            topics=[
                bloomberg_pb2.Topic(
                    name=t, 
                    field=f,
                    type=type, 
                    interval=interval
                ) for t in topics for f in fields   
            ]
        )
        # Perform the asynchronous subscribe call
        await self.stub.subscribe(sub, metadata=[("cidname", self.cid.name)])
        logger.info(f"Subscribed to topics: {sub}")


    def unsubscribe(self, topics):
        pass

    async def subscriptionsStream(self, stream):
        async for response in stream:
            try:
                if response.msgtype in (RESP_SUB, RESP_BAR):
                    self.subsdata[response.topic].append(response)
                elif response.msgtype in (RESP_STATUS, RESP_ERROR):
                    self.statusLog.append(response)
                else:
                    pass
                if self.handler:
                    #self.loop.call_soon_threadsafe(self.handler.handle, response)
                    asyncio.run_coroutine_threadsafe(self.handler.handle(response), self.loop)
                if self.done.is_set():
                    break
            except asyncio.CancelledError:
                logger.info("subscriptionsStream was cancelled.")
                # Properly cancel the stream
                await stream.cancel()
            except Exception as e:
                logger.error(f"Error in subscriptionsStream: {e}")
            finally:
                logger.info("subscriptionsStream ended.")



class Handler():
    """ Optional handler class to handle subscription responses. 
        This must be sent as a class and not as an instance, because it
        will be instantiated in the Bbg class. """

    def __init__(self):
        self.mysubsdata = defaultdict(lambda: deque(maxlen = 1000))
        self.statusLog = deque(maxlen = 1000)
    
    async def handle(self, response):
        # this function must be present in any handler
        try:
            if response.msgtype in (RESP_SUB, RESP_BAR):
                self.statusLog.append(response)
                print(Fore.GREEN, f"Received: {response}", Style.RESET_ALL)
            else:
                self.mysubsdata[response.topic].append(response)
                print(Fore.MAGENTA, Style.BRIGHT, f"Received: {response}", Style.RESET_ALL)
        except Exception as e:
            print(f"{Fore.MAGENTA}Error: {e}{Style.RESET_ALL}")


def syncmain():
    bbg = Bbg(
        grpchost=args.grpchost,
        grpcport=args.grpcport,
        grpckeyport=args.grpckeyport,
        handler_class = Handler  # Optional handler class that will run in addition to defaul handler
    )

    # Request historical data
    hist = bbg.historicalDataRequest(
        ["RNO FP Equity", "MSFT US Equity"],
        ["PX_LAST", "CUR_MKT_CAP"],
        dt.datetime(2023, 11, 28),
        dt.datetime(2023, 11, 30)
    )
    print(hist)

    bbg.subscribe(["XBTUSD Curncy"])
    IPython.embed

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
            bbg = syncmain()
            import time
            time.sleep(3)
            bbg.close()
        except KeyboardInterrupt:
            print("Keyboard interrupt")
        finally:
            pass




