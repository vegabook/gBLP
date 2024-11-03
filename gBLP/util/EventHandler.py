# colorscheme greenvision dark

import blpapi
import datetime as dt
import time
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from rich.console import Console; console = Console() 

from constants import (RESP_INFO, RESP_REF, RESP_SUB, RESP_BAR,
        RESP_STATUS, RESP_ERROR, RESP_ACK, DEFAULT_FIELDS)

class EventHandler(object):

    def __init__(self, parent):
        self.parent = parent

    def multisend(self, correlid, sendmsg):
        queues = [x[1] for x in self.parent.correlators[correlid]] 
        for q in queues:
            self.parent.loop.call_soon_threadsafe(q.put_nowait, sendmsg)

    def getTimeStamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def processResponseEvent(self, event, partial):
        for msg in event:
            correlid = msg.correlationId().value()
            logger.info((f"Received response to request {msg.getRequestId()} "
                        f"partial {partial}"))
            sendmsg = (RESP_REF, {"correlid": correlid, "partial": partial, "data": msg.toPy()})
            # now put message into correct asyncio queue. Ceremony here is because we're calling async from sync
            self.multisend(correlid, sendmsg)
            if not partial:   # then we're done with this so deleate the correlator entry
                del self.parent.correlators[correlid]


    def processSubscriptionStatus(self, event):
        timestamp = self.getTimeStamp()
        timestampdt = dt.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        
        for msg in event:
            pymsg = msg.toPy()
            correlid = msg.correlationId().value()
            if msg.messageType() == blpapi.Names.SUBSCRIPTION_FAILURE:
                sendmsg = (RESP_STATUS, {"topic": correlid, "timestamp": timestampdt, "validated": False})
                # TODO remove from correlators when failure
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_TERMINATED:
                sendmsg = (RESP_STATUS, {"topic": correlid, "timestamp": timestampdt, "terminated": True})
                # TODO remove from correlators when failure
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_STARTED:
                sendmsg = (RESP_STATUS, {"topic": correlid, "timestamp": timestampdt, "validated": True})
            else:
                sendmsg = None
            if sendmsg:
                self.multisend(correlid, sendmsg)

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
            correlid = msg.correlationId().value()
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
                sendmsg = (RESP_SUB, 
                       {"timestamp": timestampdt, 
                       "topic": correlid,
                       "prices": self.searchMsg(msg, DEFAULT_FIELDS)})
                # now get all the queues that needs this message
                self.multisend(correlid, sendmsg)

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
