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
from bloomberg_pb2 import FieldVal, FieldVals, Status
from google.protobuf.struct_pb2 import Value
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp

from rich.console import Console; console = Console() 


class EventRouter(object):

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
            sendmsg = ("ref", {"cid": cid, "partial": partial, "data": msg.toPy()})
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
            msgtype = str(msg.messageType())
            topic = Topic()
            topic.CopyFrom(self.parent.correlators[cid][1])
            status = Status()
            status.timestamp.FromDatetime(timestampdt)
            status.message = msgtype
            topic.status.CopyFrom(status)
            self.multisend(cid, topic)

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
                sendmsg = ("bar", self.makeBarMessage(msg, str(msgtype), 
                                                          topic, interval = 1))
                print(Fore.RED, Style.BRIGHT, sendmsg, Style.RESET_ALL)

            # subscription --->
            elif msgtype == blpapi.Name("MarketDataEvents"):
                # make a copy of the topic
                topic = Topic()
                topic.CopyFrom(self.parent.correlators[cid][1])
                # create a FieldVals array and set its timestamp
                fieldVals = FieldVals()
                fieldVals.timestamp.FromDatetime(timestampdt)
                # now iterate over the msg fields and add to the FieldVals
                for field in topic.fields:
                    if msg.hasElement(field):
                        fieldVal = FieldVal(name=field)
                        msgval = msg.getElement(field).toPy()
                        if isinstance(msgval, float) or isinstance(msgval, int):
                            fieldVal.val.number_value = msgval
                            fieldVal.valtype = "number"
                        elif isinstance(msgval, str):
                            fieldVal.val.string_value = msgval
                            fieldVal.valtype = "string"
                        elif isinstance(msgval, bool):
                            fieldVal.val.bool_value = msgval
                            fieldVal.valtype = "bool"
                        elif isinstance(msgval, dt.datetime):
                            timestamp = protoTimestamp()
                            timestamp.FromDatetime(msgval)
                            fieldVal.valtype = "datetime"
                        elif isinstance(msgval, dt.date):
                            timestamp = protoTimestamp()
                            timestamp.FromDatetime(dt.datetime.combine(msgval, dt.time(0, 0)))
                            fieldVal.valtype = "date_zero_time_added"
                        elif isinstance(msgval, dt.time):
                            today = dt.date.today()
                            timestamp = protoTimestamp()
                            timestamp.FromDatetime(dt.datetime.combine(today, msgval))
                            fieldVal.valtype = "time_today_date_added"
                        else:
                            fieldVal.val.string_value = str(msgval)
                        if msgval is not None:
                            fieldVals.vals.append(fieldVal)
                # add the FieldVals to the topic
                topic.fieldvals.CopyFrom(fieldVals)
                self.multisend(cid, topic)

            # something else --->
            else:
                logger.warning(f"Unknown message type {msgtype}")

    def processMiscEvents(self, event):
        for msg in event:
            sendmsg = ("status", str(msg.messageType()))


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
