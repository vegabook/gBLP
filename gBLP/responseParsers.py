# colorscheme cobalt dark
from bloomberg_pb2 import (
    HistoricalDataResponse,
    HistoricalDataResponseItem,
    SecurityData,
    FieldData,
    IntradayBarResponse,
    IntradayBarResponseItem,
    IntradayBarData,
    Topic,
)



from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Value
from google.protobuf.struct_pb2 import Struct
import datetime

import logging
logger = logging.getLogger(__name__)


def buildIntradayBarResponse(data):
    """ see https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf p177"""
    response = IntradayBarResponse()
    for item in data:
        # althouth we might get a responseError _per item" (block of messages)
        # we're going to hoist such an error right into the top level response
        # and stop parsing the rest of the items. HistoricalDataRequest is 
        # different because responseErrors might happen per field or per security
        # but IntradaryBarReqests only have one security and one field
        if item.get('responseError'):
            response.responseError = item['responseError']
            break
        barItem = IntradayBarResponseItem()
        for bar in item["barData"]["barTickData"]:
            barData = IntradayBarData()
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
            barItem.bars.append(barData)
        response.items.append(barItem)
    return response



def buildHistoricalDataResponse(data):
    """ see https://data.bloomberglp.com/professional/sites/4/blpapi-developers-guide-2.54.pdf p170"""
    response = HistoricalDataResponse()
    for item in data:
        if item.get('responseError'):
            response.responseError = item['responseError']
            break
        securityDataDict = item['securityData']
        # Create SecurityData message
        securityDataMsg = SecurityData()
        if securityDataDict.get('responseError'):
            response.responseError = item['responseError']
            break # TODO experiment with where these response errors occur for each security
        securityDataMsg.security = securityDataDict['security']
        securityDataMsg.sequence_number = securityDataDict['sequenceNumber']
        
        # Handle fieldData
        if item.get("securityError"):
            fieldDataMsg = FieldData()

        for fieldDataItem in securityDataDict['fieldData']:
            fieldDataMsg = FieldData()
            
            # Convert date to Timestamp
            dateValue = fieldDataItem['date']
            datetimeObj = datetime.datetime.combine(dateValue, datetime.time.min)
            timestamp = Timestamp()
            timestamp.FromDatetime(datetimeObj)
            fieldDataMsg.date.CopyFrom(timestamp)
            
            # Add arbitrary fields
            for key, value in fieldDataItem.items():
                if key == 'date':
                    continue  # Skip the date field
                # Create a Value object based on the type of value
                if isinstance(value, (int, float)):
                    fieldDataMsg.fields[key].number_value = value
                elif isinstance(value, str):
                    fieldDataMsg.fields[key].string_value = value
                elif isinstance(value, bool):
                    fieldDataMsg.fields[key].bool_value = value
                else:
                    # Handle other types or raise an error
                    raise ValueError(f"Unsupported type for field '{key}': {type(value)}")
            
            # Append to fieldData
            securityDataMsg.field_data.append(fieldDataMsg)
        
        # Create HistoricalDataResponseItem
        responseItem = HistoricalDataResponseItem()
        responseItem.security_data.CopyFrom(securityDataMsg)
        
        # Append to items
        response.items.append(responseItem)
    return response




