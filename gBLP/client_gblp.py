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
from bloomberg_pb2 import topicType
from bloomberg_pb2 import subscriptionType
from bloomberg_pb2 import allBbgFields
from bloomberg_pb2 import statusType
import bloomberg_pb2_grpc
import random
from pathlib import Path
import datetime as dt
import time
import os
import sys
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
from google.protobuf import empty_pb2
import json

from constants import (
    MAX_MESSAGE_LENGTH, 
    PONG_SECONDS_TIMEOUT,
    DEFAULT_FIELDS,
)

# TODO FIRST RELEASE
# * unsubscribe must work
# * unsubscribe server on cancel
# * reference data request
# * commit, then simplify and lint in new branch
# TODO FROLLOW UP RELEASE
# * curve data request
# * instrument search request


ALL_FIELDS = allBbgFields.keys()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--message', default='hello!')
parser.add_argument('--grpchost', default='signaliser.com')
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
        self.name = makeName(alphaLength=6, digitLength=3)
        self.grpchost = grpchost
        self.grpcport = grpcport
        self.grpckeyport = grpckeyport
        self.done = asyncio.Event()

        # setup dictionaries for subscription data
        self.subsdata = defaultdict(lambda: deque(maxlen = maxdDequeSize)) # store subscription data

        # Start the event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, 
                                       args=(self.loop,), 
                                       daemon=False,
                                       name="grpc_thread")
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

        



    def close(self):
        while len(self.streams) > 0:
            logger.info("Cancelling stream")
            stream = self.streams.pop()
            stream.cancel()
            time.sleep(0.5)
        logger.info("Setting done event")
        self.loop.call_soon_threadsafe(self.done.set)
        time.sleep(0.5)
        logger.info("closing channel")
        self.loop.call_soon_threadsafe(self.channel.close())
        time.sleep(0.5)
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


    def check_connection(self):
        """Check the connection status."""
        state = self.channel.get_state()
        if state == grpc.ChannelConnectivity.SHUTDOWN:
            return False
        else:
            return False


    def historicalDataRequest(self, 
                              topics, 
                              fields = ["LAST_PRICE"], 
                              start = dt.datetime.today() - dt.timedelta(days=365),
                              end = dt.datetime.today(), 
                              options = None) -> bloomberg_pb2.HistoricalDataResponse:
        return self.loop_run_async(self.async_historicalDataRequest(topics, fields, start, end, options))

    async def async_historicalDataRequest(self, 
                                          topics, 
                                          fields, 
                                          start, 
                                          end, 
                                          options) -> bloomberg_pb2.HistoricalDataResponse:
        sst = protoTimestamp()
        sst.FromDatetime(start)
        est = protoTimestamp()
        est.FromDatetime(end)
        hreq = bloomberg_pb2.HistoricalDataRequest(
            topics=topics,
            fields=fields,
            start=sst,
            end=est
        )
        logger.info(f"Requesting historical data: {hreq}")
        data = await self.stub.historicalDataRequest(hreq, metadata=[("client", self.name)])
        return data


    def intradayBarRequest(self, 
                           topic,
                           start = dt.datetime.now() - dt.timedelta(days=3),
                           end = dt.datetime.now(),
                           interval = 1, 
                           options = None) -> bloomberg_pb2.IntradayBarResponse:
        return self.loop_run_async(self.async_intradayBarRequest(topic, start, end, interval, options))

    async def async_intradayBarRequest(self, 
                                       topic, 
                                       start, 
                                       end, 
                                       interval, 
                                       options) -> bloomberg_pb2.IntradayBarResponse:
        sst = protoTimestamp()
        sst.FromDatetime(start)
        est = protoTimestamp()
        est.FromDatetime(end)
        bareq = bloomberg_pb2.IntradayBarRequest(
            topic=topic,
            start=sst,
            end=est,
            interval=interval
        )
        logger.info(f"Requesting intraday bars: {bareq}")
        data = await self.stub.intradayBarRequest(bareq, metadata=[("client", self.name)])
        return data


    def mtl(self, 
            topics, 
            fields=DEFAULT_FIELDS,
            topictype=topicType.TICKER,
            interval=2, 
            bar=False) -> bloomberg_pb2.TopicList:
        """Make a topic list."""
        if not type(topics) == list:
            logger.error("Topics must be a list.")
            return
        if not type(fields) == list:
            logger.error("Fields must be a list.")
            return
        if bar:
            subtype = subscriptionType.BAR
        else:
            subtype = subscriptionType.TICK
        preptopics=[
            bloomberg_pb2.Topic(
                topic=topic,
                fields=fields,
                topictype=topictype,
                interval=interval,
                subtype=subtype
            ) for topic in topics
        ]
        randomname = makeName(alphaLength=6, digitLength=3)
        subtype = bloomberg_pb2.subscriptionType.BAR if bar else bloomberg_pb2.subscriptionType.TICK
        return bloomberg_pb2.TopicList(tlid=randomname, topics=preptopics)

    def sub(self, topics, handler=None):
        """ synchronous subscribe method """
        return self.loop_run_async(self.async_sub(topics, handler))

    async def async_sub(self, topics, handler):
        stream = self.stub.sub(topics, metadata=[("client", self.name)])
        self.streams.append(stream)
        self.loop_run_async_nowait(self.streamHandler(stream, handler))
        logger.info("Subscription stream started.")
        return topics 


#    async def streamHandler(self, stream, handler, timeout=30):
#        try:
#            # Wrap the entire for loop with asyncio.wait_for to enforce a timeout on the whole loop
#            async def loop_body():
#                async for topic in stream:
#                    try:
#                        self.subsdata[topic.topic].append(topic)
#                        if handler:
#                            asyncio.run_coroutine_threadsafe(handler.handle(topic), self.loop)
#                    except asyncio.CancelledError:
#                        logger.info("streamHandler was cancelled.")
#                        break
#                    except Exception as e:
#                        logger.error(f"Error in streamHandler: {e}")
#
#            # Run the loop_body coroutine with a timeout
#            await asyncio.wait_for(loop_body(), timeout=timeout)
#
#        except asyncio.TimeoutError:
#            logger.warning("streamHandler timed out.")
#        except asyncio.CancelledError:
#            logger.info("streamHandler was cancelled.")
#        finally:
#            logger.info("self.done is set. Exiting streamHandler.")


    async def streamHandler(self, stream, handler):
        async for topic in stream:
            try:
                self.subsdata[topic.topic].append(topic)
                if handler:
                    asyncio.run_coroutine_threadsafe(handler.handle(topic), self.loop)
                #if self.done.is_set():
                #    break
            except asyncio.CancelledError:
                logger.info("streamHandler was cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in streamHandler: {e}")
                break
        logger.info("Exiting streamHandler.")


    def unsub(self, topicList):
        return self.loop_run_async(self.async_unsub(topicList))


    async def async_unsub(self, topicList):
        response = await self.stub.unsub(topicList, metadata=[("client", self.name)])
        return response


    def subscriptionInfo(self) -> bloomberg_pb2.TopicList:
        return self.loop_run_async(self.async_subscriptionInfo())

    async def async_subscriptionInfo(self):
        response = await self.stub.subscriptionInfo(empty_pb2.Empty(), metadata=[("client", self.name)])
        return response


class Handler():
    """ Optional handler class to handle subscription responses. 
        This must be sent as a class and not as an instance, because it
        will be instantiated in the Bbg class. """

    def __init__(self, colour = "blue"):
        self.mysubsdata = defaultdict(lambda: deque(maxlen = 1000))
        self.colour = colour
    
    async def handle(self, response):
        # this function must be present in any handler
        try:
            if response.HasField("status"):
                console.print(f"[magenta]{response.status}[/magenta]")
            elif response.HasField("barvals"):
                if response.barvals.bartype != bloomberg_pb2.barType.MARKETBARUPDATE:
                    console.print(f"[{self.colour}]Intraday bar: {response}[/{self.colour}]")
            elif response.HasField("fieldvals"):
                console.print(f"[green]{response}[/green]")
            else:
                console.print(f"[cyan]{response}[/cyan]")
        except Exception as e:
            print(f"Error in handler: {e}")


class HandlerStatusDot():
    """ Optional handler class to handle subscription responses. 
        This must be sent as a class and not as an instance, because it
        will be instantiated in the Bbg class. """

    def __init__(self, colour = "blue"):
        self.mysubsdata = defaultdict(lambda: deque(maxlen = 1000))
        self.colour = colour
    
    async def handle(self, response):
        # this function must be present in any handler
        try:
            console.print(f"[bold blue].{response.status}[/bold blue]", end="")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error in handler: {e}")

class HandlerTime():
    async def handle(self, response):
        if response.HasField("fieldvals"):
            for fv in response.fieldvals.vals :
                if fv.name == "LAST_PRICE_TIME_TODAY_REALTIME":
                    print(response.fieldvals.servertimestamp.seconds - fv.val.number_value)

class HandlerTimeBars():
    async def handle(self, response):
        if response.HasField("barvals"):
            if response.barvals.HasField("timestamp"):
                print(response.barvals.servertimestamp.seconds - response.barvals.timestamp.seconds)

if __name__ == "__main__":

    # TODO move certs into another class
    if args.delcerts:
        bbg = Bbg()
        bbg.delCerts()
    else:
        try:
            bbg = Bbg()
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


            handler1 = HandlerStatusDot("blue")
            subs1 = bbg.mtl(["XBTUSD Curncy", "XETUSD Curncy"], DEFAULT_FIELDS, bar=False, interval = 1)
            bbg.sub(subs1, handler = handler1)


            handler2 = Handler("red")
            subs2 = bbg.mtl(["SPX Index", "R2034 Govt"], DEFAULT_FIELDS, bar=True, interval = 1)
            bbg.sub(subs2, handler = handler2)

            handler3 = Handler("blue")
            subs3 = bbg.mtl(["TSLA US Equity", "NVDA US Equity"], DEFAULT_FIELDS, bar=False, interval = 1)
            bbg.sub(subs3, handler = handler3)

            fx = [
                "EURUSD Curncy",
                "USDJPY Curncy",
                "GBPUSD Curncy",
                "AUDUSD Curncy",
                "USDCAD Curncy",
                "USDCHF Curncy",
                "NZDUSD Curncy",
                "EURGBP Curncy",
                "EURJPY Curncy",
                "EURAUD Curncy",
                "EURCAD Curncy",
                "EURCHF Curncy",
                "GBPJPY Curncy",
                "GBPAUD Curncy",
                "GBPCAD Curncy",
                "GBPCHF Curncy",
                "AUDJPY Curncy",
                "AUDNZD Curncy",
                "AUDCAD Curncy",
                "AUDCHF Curncy",
                "CADJPY Curncy",
                "CADCHF Curncy",
                "NZDJPY Curncy",
                "NZDCAD Curncy",
                "NZDCHF Curncy",
                "USDSGD Curncy",
                "USDHKD Curncy",
                "USDCNY Curncy",
                "EURNZD Curncy",
                "EURSGD Curncy"
            ]
            handler4 = HandlerTime()
            subs4 = bbg.mtl(fx, DEFAULT_FIELDS, bar=False, interval = 1)
            bbg.sub(subs4, handler = handler4)

            import csv
            with open("/home/tbrowne/scratch/cusip.csv") as f:
                reader = csv.reader(f)
                tickers = [x[1] + " Corp" for x in list(reader)]
            subtickers = tickers[-100:]
            handler5 = HandlerTimeBars()
            subs5 = bbg.mtl(subtickers, ["LAST_PRICE"], bar=True, interval = 1)
            #bbg.sub(subs5)

            #time.sleep(10)
            #bbg.unsub(subs1)
            #time.sleep(3)
            #bbg.unsub(subs2)
            #time.sleep(3)
            #bbg.unsub(subs3)
            #time.sleep(3)
            #bbg.unsub(subs4)
            #bbg.close()
            IPython.embed()
        except KeyboardInterrupt:
            print("Keyboard interrupt")
        finally:
            pass


