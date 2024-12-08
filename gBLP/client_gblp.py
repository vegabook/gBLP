# colorscheme aiseered dark

# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------

import asyncio
import threading
import grpc
import gBLP.bloomberg_pb2 as bloomberg_pb2
from gBLP.bloomberg_pb2 import topicType
from gBLP.bloomberg_pb2 import subscriptionType
from gBLP.bloomberg_pb2 import allBbgFields
from gBLP.bloomberg_pb2 import statusType
import gBLP.bloomberg_pb2_grpc as bloomberg_pb2_grpc
import random
from pathlib import Path
import datetime as dt
import time
import os
import sys
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from gBLP.util.certMaker import get_conf_dir
from gBLP.util.utils import makeName, printBeta, printLicence
import getpass
from loguru import logger
from collections import deque, defaultdict
import IPython
from queue import Queue
from rich.console import Console; console = Console()
from google.protobuf import empty_pb2
import json

from gBLP.constants import (
    MAX_MESSAGE_LENGTH, 
    PONG_SECONDS_TIMEOUT,
    DEFAULT_FIELDS,
)

# TODO FIRST RELEASE
# * client open and close explicitly instead of on instantiation
# * server correlators must show who is correlating
# * write tests
# * write examples
# * write documentation
# * overrides
# * put colours into logger and upgrade to loguru
# TODO FROLLOW UP RELEASE
# * session reconnection with resubscription
# * check UTC status (recall reference data request must have UTC TRUE specified)
# * comq and process per client
# * curve data request
# * intraday tick request
# * instrument search request


ALL_FIELDS = allBbgFields.keys()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--message', default='hello!')
parser.add_argument('--grpchost')
parser.add_argument('--grpcport', default='50051')
parser.add_argument('--grpckeyport', default='50052')
parser.add_argument('--delcerts', action='store_true', default=False)
parser.add_argument('--nobetawarn', action='store_true', default=False)
args = parser.parse_args()
username = getpass.getuser()

from loguru import logger

def delCerts():
    """Delete certificates."""
    confdir = get_conf_dir()
    for f in ["client_certificate.pem", "client_private_key.pem", "ca_certificate.pem"]:
        if (confdir / f).exists():
            (confdir / f).unlink()
    logger.info("Certificates deleted.")


class Bbg:
    def __init__(self,
                 name=None,
                 grpchost=args.grpchost,
                 grpcport=args.grpcport,
                 grpckeyport=args.grpckeyport,
                 maxdDequeSize = 10000, 
                 nobetawarn = args.nobetawarn):       # max size of deques each holding one topic
        if not nobetawarn:
            printBeta()
            printLicence()
        if not grpchost:
            raise ValueError("grpchost must be specified.")
        if not grpcport:
            raise ValueError("grpcport must be specified.")
        # setup grpc
        if name:
            self.name = name
        else:
            self.name = makeName(alphaLength=6, digitLength=3)
        self.grpchost = grpchost
        self.grpcport = grpcport
        self.grpckeyport = grpckeyport

        # setup dictionaries for subscription data
        self.subsdata = defaultdict(lambda: deque(maxlen = maxdDequeSize)) # store subscription data
        self.statusdata = deque(maxlen = maxdDequeSize)

        # Start the event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop_and_wait_done,
                                       daemon=False,
                                       name="grpc_thread")
        self.thread.start()
        # Run asynchronous initialization in the event loop
        #self._loop_run_async(self.connect())
        self.streams = []
        self.closing = False


    def _start_loop_and_wait_done(self):
        asyncio.set_event_loop(self.loop) # start loop
        self.done = asyncio.Event()
        self.loop.run_until_complete(self._make_channel_and_stub()) # get the channel and caller stub
        # wait for done event
        print("Waiting for done event.")
        self.loop.run_until_complete(self.done.wait())
        self.loop.run_until_complete(self.channel.close())
        # ----------------- clean up -----------------
        while len(self.streams) > 0:
            logger.info("Cancelling stream")
            stream = self.streams.pop()
            console.print(f"[bold gold3]pre: {stream.cancelled()}")
            if not stream.cancelled():
                stream.cancel()
                time.sleep(0.2)
                console.print(f"[bold magenta]post: {stream.cancelled()}")
        logger.info("Goodbye.")


    def close(self):
        if not self.closing:
            self.closing = True
            self.loop.call_soon_threadsafe(self.done.set)

        
    def _loop_run_async(self, coro):
        """Schedules a coroutine to be run on the event loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()  # Waits until the coroutine is done and returns the result

    
    def _loop_run_async_nowait(self, coro):
        """Schedules a coroutine to be run on the event loop without waiting."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)


    async def _make_channel_and_stub(self):
        """Connect to the gRPC server."""
        confdir = get_conf_dir()
        # Now look for keys, request them and write them if not found
        if not ((confdir / "client_certificate.pem").exists() and
                (confdir / "client_private_key.pem").exists() and
                (confdir / "ca_certificate.pem").exists()):
            await self._makeCerts()

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


    async def _makeCerts(self):
        """Make certificates if they do not exist."""
        confdir = get_conf_dir()
        ihostandport = f"{self.grpchost}:{self.grpckeyport}"
        ichannel = grpc.aio.insecure_channel(ihostandport)
        idkey = input("Certificates not found. Identify yourself for the server (any string): ")
        logger.info("Waiting for authorization response from server...")
        async with ichannel as chan:
            istub = bloomberg_pb2_grpc.KeyManagerStub(chan)
            try:
                iresponse = await istub.requestKey(
                    bloomberg_pb2.KeyRequestId(id=str(idkey) + "@" + username)
                )
            except grpc.aio.AioRpcError as e:
                logger.info(f"Error: {e}")
                return
            if iresponse.authorised: 
                confdir.mkdir(parents=True, exist_ok=True)
                with open(confdir / "client_certificate.pem", "wb") as f:
                    f.write(iresponse.cert)
                with open(confdir / "client_private_key.pem", "wb") as f:
                    f.write(iresponse.key)
                with open(confdir / "ca_certificate.pem", "wb") as f:
                    f.write(iresponse.cacert)
                logger.info(f"Certificates written to {confdir}.")
            else:
                logger.warning(f"Authorization denied for reason {iresponse.reason}")


    def check_connection_up(self):
        """Check the connection status."""
        state = self.channel.get_state()
        return(state != grpc.ChannelConnectivity.SHUTDOWN \
            and state != grpc.ChannelConnectivity.TRANSIENT_FAILURE)




    def historicalDataRequest(self, 
                              topics, 
                              fields = None,
                              start = None,
                              end = None, 
                              options = None) -> bloomberg_pb2.HistoricalDataResponse:
        if not type(topics) == list and all(isinstance(topic, str) for topic in topics):
            logger.error("Topics must be a list of strings.")
            return  
        return self._loop_run_async(self.async_historicalDataRequest(topics, fields, start, end, options))

    async def async_historicalDataRequest(self, 
                                          topics, 
                                          fields, 
                                          start, 
                                          end, 
                                          options) -> bloomberg_pb2.HistoricalDataResponse:
        args = {k: v for k, v in locals().items() if v is not None and k != "self"}
        hreq = bloomberg_pb2.HistoricalDataRequest(**args)
        logger.info(f"Requesting historical data: {hreq}")
        data = await self.stub.historicalDataRequest(hreq, metadata=[("client", self.name)])
        return data



    def intradayBarRequest(self, 
                           topic,
                           start = None, # defaults on server side
                           end = None,  # defaults on server side
                           interval = None, # defaults on server side
                           options = None) -> bloomberg_pb2.IntradayBarResponse:
        if not type(topic) == str:
            logger.error("Topic must be a string.")
            return
        return self._loop_run_async(self.async_intradayBarRequest(topic, start, end, interval, options))

    async def async_intradayBarRequest(self, 
                                       topic, 
                                       start, 
                                       end, 
                                       interval, 
                                       options) -> bloomberg_pb2.IntradayBarResponse:
        # filter out None args and self
        args = {k: v for k, v in locals().items() if v is not None and k != "self"}
        bareq = bloomberg_pb2.IntradayBarRequest(**args)
        logger.info(f"Requesting intraday bars: {bareq}")
        data = await self.stub.intradayBarRequest(bareq, metadata=[("client", self.name)])
        return data


    def referenceDataRequest(self,
                             topics,
                             fields,
                             overrides = None) -> bloomberg_pb2.ReferenceDataResponse:

        if not type(topics) == list:
            logger.error("Topics must be a list.")
            return
        if not type(fields) == list:
            logger.error("Fields must be a list.")
            return
        return self._loop_run_async(self.async_referenceDataRequest(topics, fields, overrides))

    async def async_referenceDataRequest(self,
                                         topics,
                                         fields,
                                         overrides) -> bloomberg_pb2.ReferenceDataResponse:
        refreq = bloomberg_pb2.ReferenceDataRequest(
            topics=topics,
            fields=fields,
            overrides=overrides
        )
        logger.info(f"Requesting reference data: {refreq}")
        data = await self.stub.referenceDataRequest(refreq, metadata=[("client", self.name)])
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
        return self._loop_run_async(self.async_sub(topics, handler))


    async def async_sub(self, topics, handler):
        stream = self.stub.sub(topics, metadata=[("client", self.name)])
        self.streams.append(stream)
        self._loop_run_async_nowait(self.streamHandler(stream, handler))
        logger.info("Subscription stream started.")
        return topics 

    async def streamHandler(self, stream, handler):
        while True:
            try:
                async for topic in stream:
                    if topic.HasField("status"):
                        self.statusdata.append(topic)
                    elif topic.HasField("barvals") or topic.HasField("fieldvals"):
                        self.subsdata[topic.topic].append(topic)
                    if handler:
                        asyncio.run_coroutine_threadsafe(handler.handle(topic), self.loop)
            except Exception as e:
                if not self.closing:
                    self.close()
                break
            if self.done.is_set():
                break
        logger.info("Exiting streamHandler.")


    def unsub(self, topicList):
        return self._loop_run_async(self.async_unsub(topicList))


    async def async_unsub(self, topicList):
        response = await self.stub.unsub(topicList, metadata=[("client", self.name)])
        return response


    def subscriptionInfo(self) -> bloomberg_pb2.TopicList:
        return self._loop_run_async(self.async_subscriptionInfo())

    async def async_subscriptionInfo(self):
        response = await self.stub.subscriptionInfo(empty_pb2.Empty(), metadata=[("client", self.name)])
        return response


    def ping(self) -> bloomberg_pb2.Pong:
        return self._loop_run_async(self.async_ping())

    async def async_ping(self) -> bloomberg_pb2.Pong:
        message = f"Name: {self.name}, Message: {makeName(10, 4)}"
        logger.info(f"Pinging server with message: '{message}'")
        response = await self.stub.ping(bloomberg_pb2.Ping(message=message), metadata=[("client", self.name)])
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

class HandlerPrintnum():
    async def handle(self, response):
        if response.HasField("fieldvals"):
            for fv in response.fieldvals.vals:
                if fv.name == "LAST_PRICE":
                    print(fv.val.number_value)  

if __name__ == "__main__":

    # TODO move certs into another class
    if args.delcerts:
        delCerts()
    else:
        data = dict()
        bbg = Bbg()

        subs1 = bbg.mtl(["XBTUSD Curncy"], DEFAULT_FIELDS, bar=False, interval = 1)
        bbg.sub(subs1)
        subs2 = bbg.mtl(["XETUSD Curncy"], DEFAULT_FIELDS, bar=True, interval = 1)
        bbg.sub(subs2)

        IPython.embed()



