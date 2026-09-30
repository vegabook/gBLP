# colorscheme cobalt dark
""
# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------

import bloomberg_pb2 as bbpb2
from rich.pretty import pprint

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Value
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
import datetime as dt
import time
import json
import blpapi
from loguru import logger


def getTimeStamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")



def makeBarMessage(msg, correlators):
    """ make a bar message """
    cid = msg.correlationId().value() # 
    topic = bbpb2.Topic()
    topic.CopyFrom(correlators[cid]["topic"])
    barvals = bbpb2.BarVals()
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
        barvals.bartype = bbpb2.barType.MARKETBARUPDATE
    elif msgtype == blpapi.Name("MarketBarStart"):
        barvals.bartype = bbpb2.barType.MARKETBARSTART
    elif msgtype == blpapi.Name("MarketBarEnd"):
        barvals.bartype = bbpb2.barType.MARKETBAREND
    elif msgtype == blpapi.Name("MarketBarIntervalEnd"):
        barvals.bartype = bbpb2.barType.MARKETBARINTERVALEND
    topic.barvals.CopyFrom(barvals)
    return cid, topic


def makeTickMessage(msg, correlators):
    cid = msg.correlationId().value()
    timestampdt = dt.datetime.strptime(getTimeStamp(), '%Y-%m-%d %H:%M:%S')
    topic = bbpb2.Topic()
    topic.CopyFrom(correlators[cid]["topic"])
    fieldVals = bbpb2.FieldVals()
    fieldVals.servertimestamp.FromDatetime(timestampdt)
    # now iterate over the msg fields and add to the FieldVals
    yesfoundfields = False
    for field in topic.fields:
        if msg.hasElement(field):
            yesfoundfields = True
            fieldVal = bbpb2.FieldVal(name=field)
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
    topic.fieldvals.CopyFrom(fieldVals)
    return (cid, yesfoundfields, topic)
    # add the FieldVals to the topic


def makeTopicString(topic):
    fields = "|".join(topic.fields)
    subtype = bbpb2.topicType.Name(topic.subtype)
    topictype = bbpb2.topicType.Name(topic.topictype)
    topicstr = f"{topic.topic=} {topictype=} {subtype=} {fields=} {topic.interval=} "
    return topicstr


def makeStatusMessage(msg, correlators):
    cid = msg.correlationId().value()
    timestampdt = dt.datetime.strptime(getTimeStamp(), '%Y-%m-%d %H:%M:%S')
    topic = bbpb2.Topic()
    # now erase from correlators if there was a subscription failure
    status = bbpb2.Status()
    status.statustype = bbpb2.statusType.Value(str(msg.messageType()))
    status.servertimestamp.FromDatetime(timestampdt)
    status.jsondetails = json.dumps(msg.toPy())
    if cid in correlators:
        topic.CopyFrom(correlators[cid]["topic"])
        topicstr = makeTopicString(topic)
        match topic.status.statustype:
            case bbpb2.statusType.SubscriptionFailure:
                del correlators[cid]
            case bbpb2.statusType.SubscriptionTerminated:
                del correlators[cid]
    else:
        topicstr = None 
    fieldVals = bbpb2.FieldVals()
    fieldVals.servertimestamp.FromDatetime(timestampdt)
    topic.status.CopyFrom(status)
    return cid, topic, topicstr


def createValue(value):
    val =bbpb2.Value()
    if isinstance(value, float):
        val.doublevalue = value
    elif isinstance(value, int):
        val.intvalue = value
    elif isinstance(value, str):
        val.stringvalue = value
    elif isinstance(value, dt.datetime):
        timestamp = Timestamp()
        timestamp.FromDatetime(value)
        val.timevalue.CopyFrom(timestamp)
    elif isinstance(value, dt.date):
        timestamp = Timestamp()
        timestamp.FromDatetime(dt.datetime.combine(value, dt.time(0, 0)))
        val.timevalue.CopyFrom(timestamp)
    elif isinstance(value, dt.time):
        today = dt.date.today()
        timestamp = Timestamp()
        timestamp.FromDatetime(dt.datetime.combine(today, value))
        val.timevalue.CopyFrom(timestamp)
    elif isinstance(value, dict):
        # Assuming nested map
        mapValue = val.mapvalue
        for k, v in value.items():
            mapValue.fields[k].CopyFrom(createValue(v))
    elif isinstance(value, list):
        listValue = val.listvalue
        for item in value:
            # Handle list of dicts
            if isinstance(item, dict):
                mapVal =bbpb2.Value()
                for k, v in item.items():
                    mapVal.mapvalue.fields[k].CopyFrom(createValue(v))
                listValue.values.append(mapVal)
            else:
                listValue.values.append(createValue(item))
    else:
        pass  # Handle other types if necessary
    return val

def createFieldData(fieldDataDict):
    fieldData =bbpb2.FieldData()
    for key, value in fieldDataDict.items():
        fieldValue = createValue(value)
        fieldData.fields[key].CopyFrom(fieldValue)
    return fieldData

def createErrorInfo(errorInfoDict):
    errorInfo =bbpb2.ErrorInfo()
    errorInfo.source = errorInfoDict.get("source", "")
    errorInfo.code = errorInfoDict.get("code", 0)
    errorInfo.category = errorInfoDict.get("category", "")
    errorInfo.message = errorInfoDict.get("message", "")
    errorInfo.subcategory = errorInfoDict.get("subcategory", "")
    return errorInfo

def createFieldException(fieldExceptionDict):
    fieldException = bbpb2.FieldException()
    fieldException.fieldId = fieldExceptionDict.get("fieldId", "")
    errorInfo = createErrorInfo(fieldExceptionDict.get("errorInfo", {}))
    fieldException.errorInfo.CopyFrom(errorInfo)
    return fieldException

def createSecurityData(securityDataDict):
    securityData = bbpb2.SecurityData()
    securityData.security = securityDataDict.get("security", "")
    securityData.sequenceNumber = securityDataDict.get("sequenceNumber", 0)
    # Handle fieldData
    fieldDataIter = securityDataDict.get("fieldData", {})
    if isinstance(fieldDataIter, dict):
        fieldData = createFieldData(fieldDataIter)
        securityData.fieldData.CopyFrom(fieldData)
    elif isinstance(fieldDataIter, list):
        for fieldDataDict in fieldDataIter:
            fieldData = createFieldData(fieldDataDict)
            securityData.timeData.append(fieldData)
    # Handle fieldExceptions
    fieldExceptionsList = securityDataDict.get("fieldExceptions", [])
    for fieldExceptionDict in fieldExceptionsList:
        fieldException = createFieldException(fieldExceptionDict)
        securityData.fieldExceptions.append(fieldException)
    # Handle securityError
    if "securityError" in securityDataDict:
        securityError = createErrorInfo(securityDataDict["securityError"])
        securityData.securityError.CopyFrom(securityError)
    return securityData

def createResponse(dataList):
    response =bbpb2.Response()
    for item in dataList:
        securityData = createSecurityData(item)
        response.securityData.append(securityData)
    return response


def buildReferenceDataResponse(data):
    """
    https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=164
    """
    response =bbpb2.ReferenceDataResponse()
    # may be multiple items if we had partial fills 
    for item in data:
        if item.get('responseError'):
            err = createErrorInfo(item["responseError"])
            response.responseError.CopyFrom(err)
            break
        for sec in item["securityData"]:
            if sec.get('securityError'):
                err = createErrorInfo(sec["securityError"])
                response.responseError.CopyFrom(err)
            else:
                response.securityData.append(createSecurityData(sec))
    return response


def buildHistoricalDataResponse(data):
    """
    https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=170
    """
    response =bbpb2.HistoricalDataResponse()
    for sec in data:
        if sec.get('responseError'):
            err = createErrorInfo(sec["responseError"])
            response.responseError.CopyFrom(err)
            break
        response.securityData.append(createSecurityData(sec["securityData"]))
        if sec.get('securityError'):
            err = createErrorInfo(sec["securityError"])
            response.securityError.CopyFrom(err)
    return response


def buildIntradayBarResponse(data):
    """
    https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=177
    """
    response =bbpb2.IntradayBarResponse()
    for item in data:
        # althouth we might get a responseError _per item" (block of messages)
        # we're going to hoist such an error right into the top level response
        # and stop parsing the rest of the items. HistoricalDataRequest is 
        # different because responseErrors might happen per field or per security
        # but IntradaryBarReqests only have one security and one field
        if item.get('responseError'):
            err = createErrorInfo(item["responseError"])
            response.responseError.CopyFrom(err)
            break
        for bar in item["barData"]["barTickData"]:
            barData =bbpb2.IntradayBarData()
            barData.open = bar["open"]
            barData.high = bar["high"]
            barData.low = bar["low"]
            barData.close = bar["close"]
            barData.volume = bar["volume"]
            barData.numEvents = bar["numEvents"]
            barData.value = bar["value"]
            timestamp = Timestamp()
            timestamp.FromDatetime(bar["time"])
            barData.time.CopyFrom(timestamp)
            response.bars.append(barData)
    return response
