# colorscheme greenvision dark

import blpapi
import datetime as dt
import time
import sys
import logging; logger = logging.getLogger(__name__)
from gBLP.bloomberg_pb2 import Topic
from gBLP.bloomberg_pb2 import FieldVal, FieldVals, Status
from gBLP.bloomberg_pb2 import BarVals, barType
from gBLP.bloomberg_pb2 import Status, statusType
from google.protobuf.struct_pb2 import Value
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from gBLP.responseParsers import makeBarMessage, makeStatusMessage, makeTickMessage


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
        q.put(sendmsg)


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
                self.parent.correlators.pop(cid)


    def processSubscriptionStatus(self, event):
        for msg in event:
            cid, topic = makeStatusMessage(msg, self.parent.correlators)
            if topic.status.statustype == statusType.SubscriptionTerminated:
                self.parent.correlators.pop(cid)
                # send messages to all connected clients on subscription
            self.simplesend(cid, ("status", topic.SerializeToString()))


    def processMiscEvents(self, event):
        timestampdt = dt.datetime.strptime(self.getTimeStamp(), '%Y-%m-%d %H:%M:%S')
        for msg in event:
            cid, topic = makeStatusMessage(msg, self.parent.correlators)
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



    def processSubscriptionDataEvent(self, event):
        """ 
        process subsription data message and put on queue
        """
        for msg in event:
            # bars --->
            msgtype = msg.messageType()
            if msgtype in (blpapi.Name("MarketBarUpdate"),
                           blpapi.Name("MarketBarStart"),
                           blpapi.Name("MarketBarEnd"),
                           blpapi.Name("MarketBarIntervalEnd")):
                cid, topic = makeBarMessage(msg, self.parent.correlators)
                self.simplesend(cid, ("bar", topic.SerializeToString()))

            # subscription --->
            elif msgtype == blpapi.Name("MarketDataEvents"):
                cid, yesfoundfields, topic = makeTickMessage(msg, self.parent.correlators)
                if yesfoundfields:
                    self.simplesend(cid, ("tick", topic.SerializeToString()))
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
