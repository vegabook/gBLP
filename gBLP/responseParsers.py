# colorscheme cobalt dark
import bloomberg_pb2 as bb
from rich.pretty import pprint

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Value
from google.protobuf.struct_pb2 import Struct
import datetime as dt

import logging
logger = logging.getLogger(__name__)


def buildIntradayBarResponse(data):
    """ see https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=177"""
    response = bb.IntradayBarResponse()
    for item in data:
        # althouth we might get a responseError _per item" (block of messages)
        # we're going to hoist such an error right into the top level response
        # and stop parsing the rest of the items. HistoricalDataRequest is 
        # different because responseErrors might happen per field or per security
        # but IntradaryBarReqests only have one security and one field
        if item.get('responseError'):
            response.responseError = item['responseError']
            break
        for bar in item["barData"]["barTickData"]:
            barData = bb.IntradayBarData()
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


def createValue(value):
    val = bb.Value()
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
                mapVal = bb.Value()
                for k, v in item.items():
                    mapVal.mapvalue.fields[k].CopyFrom(createValue(v))
                listValue.values.append(mapVal)
            else:
                listValue.values.append(createValue(item))
    else:
        pass  # Handle other types if necessary
    return val

def createFieldData(fieldDataDict):
    fieldData = bb.FieldData()
    print("yaaaaaaaaaaaaaa1")
    for key, value in fieldDataDict.items():
        print("yaaaaaaaaaaaaaa2")
        fieldValue = createValue(value)
        fieldData.fields[key].CopyFrom(fieldValue)
    return fieldData

def createErrorInfo(errorInfoDict):
    errorInfo = bb.ErrorInfo()
    errorInfo.source = errorInfoDict.get("source", "")
    errorInfo.code = errorInfoDict.get("code", 0)
    errorInfo.category = errorInfoDict.get("category", "")
    errorInfo.message = errorInfoDict.get("message", "")
    errorInfo.subcategory = errorInfoDict.get("subcategory", "")
    return errorInfo

def createFieldException(fieldExceptionDict):
    fieldException = bb.FieldException()
    fieldException.fieldId = fieldExceptionDict.get("fieldId", "")
    errorInfo = createErrorInfo(fieldExceptionDict.get("errorInfo", {}))
    fieldException.errorInfo.CopyFrom(errorInfo)
    return fieldException

def createSecurityError(securityErrorDict):
    securityError = bb.SecurityError()
    securityError.source = securityErrorDict.get("source", "")
    securityError.code = securityErrorDict.get("code", 0)
    securityError.category = securityErrorDict.get("category", "")
    securityError.message = securityErrorDict.get("message", "")
    securityError.subcategory = securityErrorDict.get("subcategory", "")
    return securityError

def createSecurityData(securityDataDict):
    securityData = bb.SecurityData()
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
        securityError = createSecurityError(securityDataDict["securityError"])
        securityData.securityError.CopyFrom(securityError)
    return securityData

def createResponse(dataList):
    response = bb.Response()
    for item in dataList:
        breakpoint()
        securityData = createSecurityData(item)
        response.securitydata.append(securityData)
    return response


def buildReferenceDataResponse(data):
    """ see https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=164"""
    response = bb.ReferenceDataResponse()
    # may be multiple items if we had partial fills 
    for item in data:
        for sec in item["securityData"]:
            response.securitydata.append(createSecurityData(sec))
        if item.get('responseError'):
            response.responseError = createErrorInfo(item['responseError'])
    return response


def buildHistoricalDataResponse(data):
    """ see https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf#page=170"""
    response = bb.HistoricalDataResponse()
    for sec in data:
        response.securitydata.append(createSecurityData(sec["securityData"]))
    if sec.get('responseError'):
        response.responseError = createErrorInfo(sec['responseError'])
    return response

