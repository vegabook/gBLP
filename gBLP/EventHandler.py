# colorscheme greenvision dark

import blpapi
import datetime as dt
import time
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from bloomberg_pb2 import IntradayBarResponse
from bloomberg_pb2 import Topic
from bloomberg_pb2 import Field
from bloomberg_pb2 import msgType
from google.protobuf.struct_pb2 import Value

from rich.console import Console; console = Console() 

from constants import (RESP_INFO, RESP_REF, RESP_SUB, RESP_BAR,
        RESP_STATUS, RESP_ERROR, RESP_ACK, DEFAULT_FIELDS)

class EventHandler(object):

    def __init__(self, parent):
        self.parent = parent

    def multisend(self, cid, sendmsg):
        q = self.parent.correlators[cid][0] 
        self.parent.loop.call_soon_threadsafe(q.put_nowait, sendmsg)

    def getTimeStamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def processResponseEvent(self, event, partial):
        for msg in event:
            cid = msg.correlationId().value()
            logger.info((f"Received response to request {msg.getRequestId()} "
                        f"partial {partial}"))
            sendmsg = (RESP_REF, {"cid": cid, "partial": partial, "data": msg.toPy()})
            # now put message into correct asyncio queue. Ceremony here is because we're calling async from sync
            self.multisend(cid, sendmsg)
            if not partial:   # then we're done with this so deleate the correlator entry
                del self.parent.correlators[cid]


    def processSubscriptionStatus(self, event):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        for msg in event:
            console.print(f"[light blue]{msg}[/light blue]")
            pymsg = msg.toPy()
            cid = msg.correlationId().value()
            if msg.messageType() == blpapi.Names.SUBSCRIPTION_FAILURE:
                sendmsg = (RESP_STATUS, {"topic": cid, "timestamp": timestampdt, "validated": False})
                # TODO remove from correlators when failure
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_TERMINATED:
                sendmsg = (RESP_STATUS, {"topic": cid, "timestamp": timestampdt, "terminated": True})
                # TODO remove from correlators when failure
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_STARTED:
                sendmsg = (RESP_STATUS, {"topic": cid, "timestamp": timestampdt, "validated": True})
            else:
                sendmsg = None
            if sendmsg:
                breakpoint()
            #    self.multisend(cid, sendmsg)

    def searchMsg(self, msg, fields):
        return [{"field": field, "value": msg[field]} 
                for field in fields if msg.hasElement(field)]

    def makeBarMessage(self, msg, msgtype, topic, interval):
        msgdict = {"msgtype": msgtype, "topic": topic, "interval": interval}
        for f, m in {"open": "OPEN", 
                     "high": "HIGH", 
                     "low": "LOW", 
                     "close": "CLOSE", 
                     "volume": "VOLUME", 
                     "numticks": "NUMBER_OF_TICKS",
                     "timestamp": "DATE_TIME"}.items():
            if msg.hasElement(m):
                msgdict[f] = msg[m]
            else:
                msgdict[f] = None

        return msgdict

    def processSubscriptionDataEvent(self, event):
        """ 
        process subsription data message and put on queue
        """
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        for msg in event:
            msgtype = msg.messageType()
            cid = msg.correlationId().value()
            # bars --->
            if msgtype in (blpapi.Name("MarketBarUpdate"),
                           blpapi.Name("MarketBarStart"),
                           blpapi.Name("MarketBarEnd"),
                           blpapi.Name("MarketBarIntervalEnd")):
                sendmsg = (RESP_BAR, self.makeBarMessage(msg, str(msgtype), 
                                                          topic, interval = 1))
                print(Fore.RED, Style.BRIGHT, sendmsg, Style.RESET_ALL)

            # subscription --->
            elif msgtype == blpapi.Name("MarketDataEvents"):
                # mktdata event type
                topic = Topic()
                topic.CopyFrom(self.parent.correlators[cid][1])
                topic.timestamp.FromDatetime(timestampdt)
                topic.msgtype = msgType.SUBDATA
                for f in topic.fields:
                    if msg.hasElement(f.name):
                        msgval = msg.getElement(f.name).toPy()
                        if isinstance(msgval, float) or isinstance(msgval, int):
                            f.value.number_value = msgval
                        elif isinstance(msgval, str):
                            f.value.string_value = msgval
                        else:
                            f.value.string_value = str(msgval)
                self.multisend(cid, topic)

            # something else --->
            else:
                logger.warning(f"Unknown message type {msgtype}")

    def processMiscEvents(self, event):
        for msg in event:
            sendmsg = (RESP_STATUS, str(msg.messageType()))


    def processEvent(self, event, _session):
        """ event processing selector """
        try:
            match event.eventType():
                case blpapi.Event.PARTIAL_RESPONSE:
                    self.processResponseEvent(event, True)
                case blpapi.Event.RESPONSE:
                    self.processResponseEvent(event, False)
                case blpapi.Event.REQUEST_STATUS:
                    for msg in event:
                        if msg.messageType == blpapi.Names.REQUEST_FAILURE:
                            reason=msg.getElement("reason")
                            print(f"Request failed: {reason}")
                            done = True
                        done = True
                case blpapi.Event.SUBSCRIPTION_DATA:
                    self.processSubscriptionDataEvent(event)
                case blpapi.Event.SUBSCRIPTION_STATUS:
                    self.processSubscriptionStatus(event)
                case _:
                    self.processMiscEvents(event)
        except blpapi.Exception as e:
            print(f"Failed to process event {event}: {e}")
        return False
