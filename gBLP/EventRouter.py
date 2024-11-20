# colorscheme greenvision dark

import blpapi
import datetime as dt
import time
import logging
import sys
import json
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from bloomberg_pb2 import IntradayBarResponse
from bloomberg_pb2 import Topic
from bloomberg_pb2 import FieldVal, FieldVals, Status
from bloomberg_pb2 import BarVals, barType
from bloomberg_pb2 import Status, statusType
from google.protobuf.struct_pb2 import Value
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp

from rich.console import Console; console = Console() 


class EventRouter(object):

    def __init__(self, parent):
        self.parent = parent

    def simplesend(self, cid, sendmsg):
        # send to one queue
        correlator = self.parent.correlators.get(cid)
        if not correlator:
            logger.warning(f"Correlator {cid} not found")
            return
        q = correlator["q"]
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
            self.simplesend(cid, sendmsg)
            if not partial:   # then we're done with this so deleate the correlator entry
                del self.parent.correlators[cid]


    def makeStatusMessage(self, msg, topic):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        fieldVals = FieldVals()
        fieldVals.servertimestamp.FromDatetime(timestampdt)
        status = Status()
        status.statustype = statusType.Value(str(msg.messageType()))
        status.servertimestamp.FromDatetime(timestampdt)
        status.jsondetails = json.dumps(msg.toPy())
        return status
            

    def processSubscriptionStatus(self, event):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        for msg in event:
            cid = msg.correlationId().value() # TODO put topic into makeStatusMessage (same for others
            topic = Topic()
            topic.CopyFrom(self.parent.correlators[cid]["topic"])
            topic.status.CopyFrom(self.makeStatusMessage(msg, topic))
            # now erase from correlators if there was a subscription failure
            match topic.status.statustype:
                case statusType.SubscriptionFailure:
                    del self.parent.correlators[cid]
                case statusType.SubscriptionTerminated:
                    del self.parent.correlators[cid]
            logger.info(f"Received subscription status: {topic.topic} {statusType.Name(topic.status.statustype)}")
            self.simplesend(cid, topic)


    def processMiscEvents(self, event):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        for msg in event:
            topic = Topic()
            topic.status.CopyFrom(self.makeStatusMessage(msg, topic))
            statusstr = statusType.Name(topic.status.statustype)
            if statusstr ==statusType.Name(statusType.SessionTerminated):
                console.print(f"[bold red]{statusstr}[/bold red]", end = " ")
                logger.info(f"Received session termination status: {statusstr}")
                # TODO clear correlators
                # send messages to all connected clients on subscription
                # TODO: send reconnection message to session
            else:
                logger.info(f"Received miscellaneous status: {statusstr}")
            console.print(f"[bold green]{statusstr}[/bold green]", end = " ")
            logger.info(f"Received miscellaneous status: {statusstr}")



    def makeBarMessage(self, msg):
        """ make a bar message """
        barvals = BarVals()
        if msg.hasElement("OPEN"):
            barvals.open = msg["OPEN"]
        if msg.hasElement("HIGH"):
            barvals.high = msg["HIGH"]
        if msg.hasElement("LOW"):
            barvals.low = msg["LOW"]
        if msg.hasElement("CLOSE"):
            barvals.close = msg["CLOSE"]
        if msg.hasElement("VOLUME"):
            barvals.volume = msg["VOLUME"]
        if msg.hasElement("NUMBER_OF_TICKS"):
            barvals.numEvents = msg["NUMBER_OF_TICKS"]
        if msg.hasElement("VALUE"):
            barvals.value = msg["VALUE"]
        if msg.hasElement("DATE_TIME"):
            timestamp = protoTimestamp()
            timestamp.FromDatetime(msg["DATE_TIME"])
            barvals.timestamp.CopyFrom(timestamp)
        servertimestamp = protoTimestamp()
        servertimestamp.FromDatetime(dt.datetime.now())
        barvals.servertimestamp.CopyFrom(servertimestamp)
        msgtype = msg.messageType()
        if msgtype == blpapi.Name("MarketBarUpdate"):
            barvals.bartype = barType.MARKETBARUPDATE
        elif msgtype == blpapi.Name("MarketBarStart"):
            barvals.bartype = barType.MARKETBARSTART
        elif msgtype == blpapi.Name("MarketBarEnd"):
            barvals.bartype = barType.MARKETBAREND
        elif msgtype == blpapi.Name("MarketBarIntervalEnd"):
            barvals.bartype = barType.MARKETBARINTERVALEND
        return barvals

    def makeTickMessage(self, msg, topic):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        fieldVals = FieldVals()
        fieldVals.servertimestamp.FromDatetime(timestampdt)
        # now iterate over the msg fields and add to the FieldVals
        yesfoundfields = False
        for field in topic.fields:
            if msg.hasElement(field):
                yesfoundfields = True
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
                    fieldVal.val.number_value = timestamp.ToSeconds()
                elif isinstance(msgval, dt.date):
                    timestamp = protoTimestamp()
                    timestamp.FromDatetime(dt.datetime.combine(msgval, dt.time(0, 0)))
                    fieldVal.valtype = "date_zero_time_added"
                    fieldVal.val.number_value = timestamp.ToSeconds()
                elif isinstance(msgval, dt.time):
                    today = dt.date.today()
                    timestamp = protoTimestamp()
                    timestamp.FromDatetime(dt.datetime.combine(today, msgval))
                    fieldVal.valtype = "time_today_date_added"
                    fieldVal.val.number_value = timestamp.ToSeconds()
                else:
                    fieldVal.val.string_value = str(msgval)
                if msgval is not None:
                    fieldVals.vals.append(fieldVal)
        return (yesfoundfields, fieldVals)
        # add the FieldVals to the topic


    def processSubscriptionDataEvent(self, event):
        """ 
        process subsription data message and put on queue
        """
        for msg in event:
            cid = msg.correlationId().value()
            # bars --->
            msgtype = msg.messageType()
            if msgtype in (blpapi.Name("MarketBarUpdate"),
                           blpapi.Name("MarketBarStart"),
                           blpapi.Name("MarketBarEnd"),
                           blpapi.Name("MarketBarIntervalEnd")):
                topic = Topic()
                topic.CopyFrom(self.parent.correlators[cid]["topic"])
                barvals = self.makeBarMessage(msg) 
                topic.barvals.CopyFrom(barvals)
                self.simplesend(cid, topic)

            # subscription --->
            elif msgtype == blpapi.Name("MarketDataEvents"):
                # make a copy of the topic
                topic = Topic()
                topic.CopyFrom(self.parent.correlators[cid]["topic"])
                # create a FieldVals array and set its timestamp
                yesfoundfields, fieldVals = self.makeTickMessage(msg, topic)
                if yesfoundfields:
                    topic.fieldvals.CopyFrom(fieldVals)
                    self.simplesend(cid, topic)
            # something else --->
            else:
                logger.warning(f"!!!!!!!!!!!!!!!! Unknown message type {msgtype}") # DEBUG


    def processEvent(self, event, _session):
        """ event processing selector """
        try:
            sys.stdout.flush()
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
