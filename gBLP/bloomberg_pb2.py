# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: bloomberg.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x62loomberg.proto\x12\tbloomberg\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\x1bgoogle/protobuf/empty.proto\"N\n\x08\x46ieldVal\x12\x0c\n\x04name\x18\x01 \x01(\t\x12#\n\x03val\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value\x12\x0f\n\x07valtype\x18\x03 \x01(\t\"c\n\tFieldVals\x12!\n\x04vals\x18\x01 \x03(\x0b\x32\x13.bloomberg.FieldVal\x12\x33\n\x0fservertimestamp\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"\xfc\x01\n\x07\x42\x61rVals\x12\x0c\n\x04open\x18\x01 \x01(\x02\x12\x0c\n\x04high\x18\x02 \x01(\x02\x12\x0b\n\x03low\x18\x03 \x01(\x02\x12\r\n\x05\x63lose\x18\x04 \x01(\x02\x12\x0e\n\x06volume\x18\x05 \x01(\x05\x12\x11\n\tnumEvents\x18\x06 \x01(\x05\x12\r\n\x05value\x18\x07 \x01(\x02\x12-\n\ttimestamp\x18\x08 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x33\n\x0fservertimestamp\x18\t \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12#\n\x07\x62\x61rtype\x18\n \x01(\x0e\x32\x12.bloomberg.barType\"}\n\x06Status\x12)\n\nstatustype\x18\x01 \x01(\x0e\x32\x15.bloomberg.statusType\x12\x33\n\x0fservertimestamp\x18\x02 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x13\n\x0bjsondetails\x18\x03 \x01(\t\"\x8e\x02\n\x05Topic\x12\r\n\x05topic\x18\x01 \x01(\t\x12\'\n\ttopictype\x18\x02 \x01(\x0e\x32\x14.bloomberg.topicType\x12,\n\x07subtype\x18\x03 \x01(\x0e\x32\x1b.bloomberg.subscriptionType\x12\x10\n\x08interval\x18\x04 \x01(\x05\x12\x0e\n\x06\x66ields\x18\x05 \x03(\t\x12)\n\tfieldvals\x18\x06 \x01(\x0b\x32\x14.bloomberg.FieldValsH\x00\x12%\n\x07\x62\x61rvals\x18\x07 \x01(\x0b\x32\x12.bloomberg.BarValsH\x00\x12#\n\x06status\x18\x08 \x01(\x0b\x32\x11.bloomberg.StatusH\x00\x42\x06\n\x04\x64\x61ta\";\n\tTopicList\x12\x0c\n\x04tlid\x18\x01 \x01(\t\x12 \n\x06topics\x18\x02 \x03(\x0b\x32\x10.bloomberg.Topic\"\x9a\x02\n\x14ReferenceDataRequest\x12\x0e\n\x06topics\x18\x01 \x03(\t\x12\x0e\n\x06\x66ields\x18\x02 \x03(\t\x12=\n\x07options\x18\x03 \x03(\x0b\x32,.bloomberg.ReferenceDataRequest.OptionsEntry\x12\x41\n\toverrides\x18\x04 \x03(\x0b\x32..bloomberg.ReferenceDataRequest.OverridesEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1a\x30\n\x0eOverridesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"s\n\x15ReferenceDataResponse\x12+\n\rresponseError\x18\x01 \x01(\x0b\x32\x14.bloomberg.ErrorInfo\x12-\n\x0csecurityData\x18\x02 \x03(\x0b\x32\x17.bloomberg.SecurityData\"9\n\x08Response\x12-\n\x0csecurityData\x18\x01 \x03(\x0b\x32\x17.bloomberg.SecurityData\"\x8f\x02\n\x0cSecurityData\x12\x10\n\x08security\x18\x01 \x01(\t\x12#\n\x07\x65idData\x18\x02 \x03(\x0b\x32\x12.bloomberg.EIDData\x12\x32\n\x0f\x66ieldExceptions\x18\x03 \x03(\x0b\x32\x19.bloomberg.FieldException\x12\x16\n\x0esequenceNumber\x18\x04 \x01(\x05\x12\'\n\tfieldData\x18\x05 \x01(\x0b\x32\x14.bloomberg.FieldData\x12&\n\x08timeData\x18\x06 \x03(\x0b\x32\x14.bloomberg.FieldData\x12+\n\rsecurityError\x18\x07 \x01(\x0b\x32\x14.bloomberg.ErrorInfo\"\t\n\x07\x45IDData\"J\n\x0e\x46ieldException\x12\x0f\n\x07\x66ieldId\x18\x01 \x01(\t\x12\'\n\terrorInfo\x18\x02 \x01(\x0b\x32\x14.bloomberg.ErrorInfo\"a\n\tErrorInfo\x12\x0e\n\x06source\x18\x01 \x01(\t\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\x12\x10\n\x08\x63\x61tegory\x18\x03 \x01(\t\x12\x0f\n\x07message\x18\x04 \x01(\t\x12\x13\n\x0bsubcategory\x18\x05 \x01(\t\"~\n\tFieldData\x12\x30\n\x06\x66ields\x18\x01 \x03(\x0b\x32 .bloomberg.FieldData.FieldsEntry\x1a?\n\x0b\x46ieldsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1f\n\x05value\x18\x02 \x01(\x0b\x32\x10.bloomberg.Value:\x02\x38\x01\"\xd6\x01\n\x05Value\x12\x15\n\x0b\x64oublevalue\x18\x01 \x01(\x01H\x00\x12\x12\n\x08intvalue\x18\x02 \x01(\x03H\x00\x12\x15\n\x0bstringvalue\x18\x03 \x01(\tH\x00\x12\'\n\x08mapvalue\x18\x04 \x01(\x0b\x32\x13.bloomberg.MapValueH\x00\x12)\n\tlistvalue\x18\x05 \x01(\x0b\x32\x14.bloomberg.ListValueH\x00\x12/\n\ttimevalue\x18\x06 \x01(\x0b\x32\x1a.google.protobuf.TimestampH\x00\x42\x06\n\x04kind\"|\n\x08MapValue\x12/\n\x06\x66ields\x18\x01 \x03(\x0b\x32\x1f.bloomberg.MapValue.FieldsEntry\x1a?\n\x0b\x46ieldsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1f\n\x05value\x18\x02 \x01(\x0b\x32\x10.bloomberg.Value:\x02\x38\x01\"-\n\tListValue\x12 \n\x06values\x18\x01 \x03(\x0b\x32\x10.bloomberg.Value\"\xf6\x01\n\x12IntradayBarRequest\x12\r\n\x05topic\x18\x02 \x01(\t\x12)\n\x05start\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\'\n\x03\x65nd\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x10\n\x08interval\x18\x05 \x01(\x05\x12;\n\x07options\x18\x06 \x03(\x0b\x32*.bloomberg.IntradayBarRequest.OptionsEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"l\n\x13IntradayBarResponse\x12+\n\rresponseError\x18\x01 \x01(\x0b\x32\x14.bloomberg.ErrorInfo\x12(\n\x04\x62\x61rs\x18\x02 \x03(\x0b\x32\x1a.bloomberg.IntradayBarData\"\xa5\x01\n\x0fIntradayBarData\x12\x0c\n\x04open\x18\x01 \x01(\x02\x12\x0c\n\x04high\x18\x02 \x01(\x02\x12\x0b\n\x03low\x18\x03 \x01(\x02\x12\r\n\x05\x63lose\x18\x04 \x01(\x02\x12\x0e\n\x06volume\x18\x05 \x01(\x05\x12\x11\n\tnumEvents\x18\x06 \x01(\x05\x12\r\n\x05value\x18\x07 \x01(\x02\x12(\n\x04time\x18\x08 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\"\xf1\x02\n\x15HistoricalDataRequest\x12\x0e\n\x06topics\x18\x02 \x03(\t\x12\x0e\n\x06\x66ields\x18\x03 \x03(\t\x12)\n\x05start\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\'\n\x03\x65nd\x18\x05 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12>\n\x07options\x18\x06 \x03(\x0b\x32-.bloomberg.HistoricalDataRequest.OptionsEntry\x12\x42\n\toverrides\x18\x07 \x03(\x0b\x32/.bloomberg.HistoricalDataRequest.OverridesEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1a\x30\n\x0eOverridesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"t\n\x16HistoricalDataResponse\x12+\n\rresponseError\x18\x01 \x01(\x0b\x32\x14.bloomberg.ErrorInfo\x12-\n\x0csecurityData\x18\x02 \x03(\x0b\x32\x17.bloomberg.SecurityData\"!\n\x13ServicesInfoRequest\x12\n\n\x02id\x18\x01 \x01(\t\"@\n\x14ServicesInfoResponse\x12(\n\x08services\x18\x01 \x03(\x0b\x32\x16.bloomberg.ServiceInfo\">\n\x0bServiceInfo\x12\x13\n\x0bserviceName\x18\x01 \x01(\t\x12\x1a\n\x12serviceDescription\x18\x02 \x01(\t\"\x1a\n\x0cKeyRequestId\x12\n\n\x02id\x18\x01 \x01(\t\"\\\n\x0bKeyResponse\x12\x0b\n\x03key\x18\x01 \x01(\x0c\x12\x0c\n\x04\x63\x65rt\x18\x02 \x01(\x0c\x12\x0e\n\x06\x63\x61\x63\x65rt\x18\x03 \x01(\x0c\x12\x12\n\nauthorised\x18\x04 \x01(\x08\x12\x0e\n\x06reason\x18\x05 \x01(\t\"\x17\n\x04Ping\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x17\n\x04Pong\x12\x0f\n\x07message\x18\x01 \x01(\t*8\n\ttopicType\x12\x08\n\x04NONE\x10\x00\x12\n\n\x06TICKER\x10\x01\x12\n\n\x06SEDOL1\x10\x02\x12\t\n\x05\x43USIP\x10\x03*.\n\x10subscriptionType\x12\x07\n\x03\x41NY\x10\x00\x12\x08\n\x04TICK\x10\x01\x12\x07\n\x03\x42\x41R\x10\x02*i\n\x07\x62\x61rType\x12\t\n\x05OTHER\x10\x00\x12\x13\n\x0fMARKETBARUPDATE\x10\x01\x12\x12\n\x0eMARKETBARSTART\x10\x02\x12\x10\n\x0cMARKETBAREND\x10\x03\x12\x18\n\x14MARKETBARINTERVALEND\x10\x04*\xec\x1c\n\x0c\x61llBbgFields\x12\x16\n\x12MKTDATA_EVENT_TYPE\x10\x00\x12\x19\n\x15MKTDATA_EVENT_SUBTYPE\x10\x01\x12\x15\n\x11\x41PI_RULES_VERSION\x10\x02\x12!\n\x1dLAST_PRICE_ALL_SESSION_DIR_RT\x10\x03\x12 \n\x1cSIMP_LAST_PX_ALL_SESS_DIR_RT\x10\x04\x12\"\n\x1ePX_OPEN_ALL_WITH_SWITCHOVER_RT\x10\x05\x12#\n\x1fPX_CLOSE_ALL_WITH_SWITCHOVER_RT\x10\x06\x12\x16\n\x12\x43URRENT_SESSION_RT\x10\x07\x12\x12\n\x0e\x43HG_NET_MTD_RT\x10\x08\x12\x12\n\x0e\x43HG_PCT_MTD_RT\x10\t\x12\x12\n\x0e\x43HG_NET_QTD_RT\x10\n\x12\x12\n\x0e\x43HG_PCT_QTD_RT\x10\x0b\x12\x12\n\x0e\x43HG_NET_YTD_RT\x10\x0c\x12\x12\n\x0e\x43HG_PCT_YTD_RT\x10\r\x12\x11\n\rCHG_NET_1M_RT\x10\x0e\x12\x11\n\rCHG_PCT_1M_RT\x10\x0f\x12\x11\n\rCHG_NET_3M_RT\x10\x10\x12\x11\n\rCHG_PCT_3M_RT\x10\x11\x12\x1d\n\x19REALTIME_2_DAY_CHANGE_NET\x10\x12\x12!\n\x1dREALTIME_2_DAY_CHANGE_PERCENT\x10\x13\x12\x1d\n\x19REALTIME_5_DAY_CHANGE_NET\x10\x14\x12!\n\x1dREALTIME_5_DAY_CHANGE_PERCENT\x10\x15\x12\x1f\n\x1bRT_PX_AS_PCT_INTRADAY_RANGE\x10\x16\x12#\n\x1fREALTIME_PERCENT_BID_ASK_SPREAD\x10\x17\x12\"\n\x1e\x43HG_NET_1D_ALL_FROM_REGULAR_RT\x10\x18\x12\"\n\x1e\x43HG_PCT_1D_ALL_FROM_REGULAR_RT\x10\x19\x12#\n\x1fPX_CHG_NET_1D_ALL_SWITCHOVER_RT\x10\x1a\x12#\n\x1fPX_CHG_PCT_1D_ALL_SWITCHOVER_RT\x10\x1b\x12$\n CHG_NET_REG_SES_PRV_RG_SES_CL_RT\x10\x1c\x12$\n CHG_PCT_REG_SES_PRV_RG_SES_CL_RT\x10\x1d\x12$\n SMART_FIELDS_METADATA_VERSION_RT\x10\x1e\x12\x15\n\x11IS_DELAYED_STREAM\x10\x1f\x12\x15\n\x11ID_BB_SEC_NUM_SRC\x10 \x12\x07\n\x03\x42ID\x10\"\x12\x07\n\x03\x41SK\x10#\x12\x08\n\x04HIGH\x10$\x12\x07\n\x03LOW\x10%\x12\x0c\n\x08\x42\x45ST_BID\x10&\x12\x0c\n\x08\x42\x45ST_ASK\x10\'\x12\x07\n\x03MID\x10(\x12\x08\n\x04OPEN\x10)\x12\x19\n\x15RT_EXCH_MARKET_STATUS\x10*\x12\x15\n\x11LAST_ALL_SESSIONS\x10+\x12\x1d\n\x19PREV_CLOSE_VALUE_REALTIME\x10,\x12\x13\n\x0f\x42ID_ALL_SESSION\x10-\x12\x13\n\x0f\x41SK_ALL_SESSION\x10.\x12\x17\n\x13TRADING_DT_REALTIME\x10/\x12\x1c\n\x18PREV_TRADING_DT_REALTIME\x10\x30\x12\x1b\n\x17\x42\x42_STANDARD_CC_AVAIL_RT\x10\x31\x12\x1a\n\x16PRICE_CHANGE_1Y_NET_RT\x10\x32\x12\x1a\n\x16PRICE_CHANGE_1Y_PCT_RT\x10\x33\x12\x1b\n\x17\x43LOSING_PRICE_1Y_AGO_RT\x10\x34\x12\x11\n\rNUM_TRADES_RT\x10\x35\x12\x1f\n\x1bZERO_BID_PRICE_INDICATOR_RT\x10\x36\x12\x1f\n\x1bZERO_ASK_PRICE_INDICATOR_RT\x10\x37\x12\x18\n\x14SHORTENED_BID_ASK_RT\x10\x38\x12\x11\n\rPX_LOW_BID_RT\x10\x39\x12\x12\n\x0ePX_HIGH_ASK_RT\x10:\x12\x12\n\x0ePX_HIGH_BID_RT\x10;\x12\x11\n\rPX_LOW_ASK_RT\x10<\x12\x12\n\x0eRT_API_MACHINE\x10=\x12\r\n\tALL_PRICE\x10>\x12\x0b\n\x07MID_TDY\x10?\x12\x08\n\x04MID2\x10@\x12\x0b\n\x07MID_DIR\x10\x41\x12\x10\n\x0cIND_BID_FLAG\x10\x42\x12\x10\n\x0cIND_ASK_FLAG\x10\x43\x12\x0c\n\x08OPEN_TDY\x10\x44\x12\x12\n\x0eLAST_PRICE_TDY\x10\x45\x12\x0b\n\x07\x42ID_TDY\x10\x46\x12\x0b\n\x07\x41SK_TDY\x10G\x12\x0c\n\x08HIGH_TDY\x10H\x12\x0b\n\x07LOW_TDY\x10I\x12\x0f\n\x0bLAST2_TRADE\x10J\x12\x0b\n\x07\x42ID_DIR\x10K\x12\x0b\n\x07\x41SK_DIR\x10L\x12\x08\n\x04\x42ID2\x10M\x12\x08\n\x04\x41SK2\x10N\x12\x15\n\x11RT_PRICING_SOURCE\x10O\x12\x0e\n\nASK_CHANGE\x10P\x12\x0e\n\nBID_CHANGE\x10Q\x12\r\n\tSPREAD_BA\x10R\x12\x1a\n\x16\x42ID_ALL_SESSION_TDY_RT\x10S\x12\x1a\n\x16\x41SK_ALL_SESSION_TDY_RT\x10T\x12\x1a\n\x16PRICE_CHANGE_ON_DAY_RT\x10U\x12\x1f\n\x1bPREVIOUS_CLOSE_BID_PRICE_RT\x10V\x12\x1f\n\x1bPREVIOUS_CLOSE_ASK_PRICE_RT\x10W\x12\x1e\n\x1aLAST_TRADE_CANCELED_IND_RT\x10X\x12!\n\x1dUNADJUSTED_PREV_LAST_PRICE_RT\x10Y\x12\x1f\n\x1b\x41\x44JUSTED_PREV_LAST_PRICE_RT\x10Z\x12\x1d\n\x19\x42LOOMBERG_CLOSE_METHOD_RT\x10[\x12\x1a\n\x16LAST_TICK_DIRECTION_RT\x10\\\x12\x19\n\x15\x42\x41SE_PRICE_ENABLED_RT\x10]\x12\"\n\x1ePERCENT_CHANGE_ON_DAY_TODAY_RT\x10^\x12\x1e\n\x1aNET_CHANGE_ON_DAY_TODAY_RT\x10_\x12\x19\n\x15PRICE_52_WEEK_HIGH_RT\x10`\x12\x1e\n\x1aPRICE_52_WEEK_HIGH_DATE_RT\x10\x61\x12\x18\n\x14PRICE_52_WEEK_LOW_RT\x10\x62\x12\x1d\n\x19PRICE_52_WEEK_LOW_DATE_RT\x10\x63\x12\x15\n\x11PRICE_LAST_ASK_RT\x10\x64\x12\x15\n\x11PRICE_LAST_BID_RT\x10\x65\x12\x11\n\rPRICE_HIGH_RT\x10\x66\x12\x10\n\x0cPRICE_LOW_RT\x10g\x12\x11\n\rPRICE_OPEN_RT\x10h\x12\x11\n\rPRICE_LAST_RT\x10i\x12\x1b\n\x17PRICE_PREVIOUS_CLOSE_RT\x10j\x12\x16\n\x12\x45VT_DELTA_TIMES_RT\x10k\x12\"\n\x1ePRICE_PCT_CHG_LAST_24_HOURS_RT\x10l\x12\x14\n\x10\x41LT_BOOK_NAME_RT\x10m\x12\x16\n\x12IMBALANCE_INDIC_RT\x10n\x12\x15\n\x11PRICE_24_HOURS_RT\x10o\x12\x19\n\x15ORDER_IMB_SELL_VOLUME\x10p\x12$\n ALT_BOOK_BEST_ASK_NUM_OF_ORDR_RT\x10q\x12\x13\n\x0fINDICATIVE_NEAR\x10r\x12$\n ALT_BOOK_BEST_BID_NUM_OF_ORDR_RT\x10s\x12\x1f\n\x1bRT_EVAL_JAPANESE_CHG_ON_DAY\x10t\x12\x1b\n\x17UNDL_PX_AT_OPT_TRADE_RT\x10u\x12!\n\x1d\x41LT_JAPANESE_EVALUATION_PX_RT\x10v\x12\x11\n\rIMBALANCE_BUY\x10w\x12#\n\x1fSETTLMNT_PX_ALT_NOTTN_METHOD_RT\x10x\x12\x1a\n\x16PX_ASK_LME_OFFICIAL_RT\x10y\x12\x12\n\x0eIMBALANCE_SELL\x10z\x12\x18\n\x14ORDER_IMB_BUY_VOLUME\x10{\x12\x1b\n\x17\x41LT_BOOK_BEST_ASK_CC_RT\x10|\x12\x1d\n\x19REGIONAL_CLOSE_PX_DATE_RT\x10}\x12\x1f\n\x1bMIN_CROSS_ORDER_QUANTITY_RT\x10~\x12 \n\x1cMIN_NEGOTIATED_TRADE_SIZE_RT\x10\x7f\x12\"\n\x1dSETTLMNT_PX_ALTRNTVE_NOTTN_RT\x10\x80\x01\x12\x1b\n\x16\x45\x42S_TOUCH_LOW_REALTIME\x10\x81\x01\x12\x1c\n\x17\x41LT_BOOK_BEST_BID_CC_RT\x10\x82\x01\x12\x19\n\x14REGIONAL_CLOSE_PX_RT\x10\x83\x01\x12\x1c\n\x17\x45\x42S_TOUCH_HIGH_REALTIME\x10\x84\x01\x12#\n\x1ePRICE_NET_CHG_LAST_24_HOURS_RT\x10\x85\x01\x12\x18\n\x13PREV_SES_LAST_PRICE\x10\x86\x01\x12\x15\n\x10RT_PX_CHG_NET_1D\x10\x87\x01\x12\x15\n\x10RT_PX_CHG_PCT_1D\x10\x88\x01\x12\x1a\n\x15LAST_UPDATE_CHG_1D_RT\x10\x89\x01\x12\t\n\x04TIME\x10\x8a\x01\x12\x17\n\x12LAST_UPDATE_BID_RT\x10\x8b\x01\x12\x17\n\x12LAST_UPDATE_ASK_RT\x10\x8c\x01\x12\x11\n\x0c\x42ID_ASK_TIME\x10\x8d\x01\x12\x0e\n\tSES_START\x10\x8e\x01\x12\x0c\n\x07SES_END\x10\x8f\x01\x12\x17\n\x12PRICE_LAST_TIME_RT\x10\x90\x01\x12 \n\x1bLAST_UPDATE_ALL_SESSIONS_RT\x10\x91\x01\x12!\n\x1cLAST_BID_TIME_TODAY_REALTIME\x10\x92\x01\x12!\n\x1cLAST_ASK_TIME_TODAY_REALTIME\x10\x93\x01\x12#\n\x1eLAST_PRICE_TIME_TODAY_REALTIME\x10\x94\x01*\xd0\x08\n\nstatusType\x12\x18\n\x14\x41uthorizationFailure\x10\x00\x12\x18\n\x14\x41uthorizationRevoked\x10\x01\x12\x18\n\x14\x41uthorizationSuccess\x10\x02\x12\x0c\n\x08\x44\x61taLoss\x10\x03\x12\x15\n\x11PermissionRequest\x10\x04\x12\x16\n\x12PermissionResponse\x10\x05\x12\x12\n\x0eRequestFailure\x10\x06\x12\x1c\n\x18RequestTemplateAvailable\x10\x07\x12\x1a\n\x16RequestTemplatePending\x10\x08\x12\x1d\n\x19RequestTemplateTerminated\x10\t\x12\x15\n\x11ResolutionFailure\x10\n\x12\x15\n\x11ResolutionSuccess\x10\x0b\x12\x1b\n\x17ServiceAvailabilityInfo\x10\x0c\x12\x17\n\x13ServiceDeregistered\x10\r\x12\x0f\n\x0bServiceDown\x10\x0e\x12\x11\n\rServiceOpened\x10\x0f\x12\x16\n\x12ServiceOpenFailure\x10\x10\x12\x15\n\x11ServiceRegistered\x10\x11\x12\x1a\n\x16ServiceRegisterFailure\x10\x12\x12\r\n\tServiceUp\x10\x13\x12\x16\n\x12SessionClusterInfo\x10\x14\x12\x18\n\x14SessionClusterUpdate\x10\x15\x12\x19\n\x15SessionConnectionDown\x10\x16\x12\x17\n\x13SessionConnectionUp\x10\x17\x12\x12\n\x0eSessionStarted\x10\x18\x12\x19\n\x15SessionStartupFailure\x10\x19\x12\x15\n\x11SessionTerminated\x10\x1a\x12\x17\n\x13SlowConsumerWarning\x10\x1b\x12\x1e\n\x1aSlowConsumerWarningCleared\x10\x1c\x12\x17\n\x13SubscriptionFailure\x10\x1d\x12\x17\n\x13SubscriptionStarted\x10\x1e\x12 \n\x1cSubscriptionStreamsActivated\x10\x1f\x12\"\n\x1eSubscriptionStreamsDeactivated\x10 \x12\x1a\n\x16SubscriptionTerminated\x10!\x12\x1a\n\x16TokenGenerationFailure\x10\"\x12\x1a\n\x16TokenGenerationSuccess\x10#\x12\x12\n\x0eTopicActivated\x10$\x12\x10\n\x0cTopicCreated\x10%\x12\x16\n\x12TopicCreateFailure\x10&\x12\x14\n\x10TopicDeactivated\x10\'\x12\x10\n\x0cTopicDeleted\x10(\x12\x0e\n\nTopicRecap\x10)\x12\x15\n\x11TopicResubscribed\x10*\x12\x13\n\x0fTopicSubscribed\x10+\x12\x15\n\x11TopicUnsubscribed\x10,2M\n\nKeyManager\x12?\n\nrequestKey\x12\x17.bloomberg.KeyRequestId\x1a\x16.bloomberg.KeyResponse\"\x00\x32\xc7\x04\n\x03\x42\x62g\x12\x31\n\x03sub\x12\x14.bloomberg.TopicList\x1a\x10.bloomberg.Topic\"\x00\x30\x01\x12\x37\n\x05unsub\x12\x14.bloomberg.TopicList\x1a\x16.google.protobuf.Empty\"\x00\x12\x42\n\x10subscriptionInfo\x12\x16.google.protobuf.Empty\x1a\x14.bloomberg.TopicList\"\x00\x12^\n\x15historicalDataRequest\x12 .bloomberg.HistoricalDataRequest\x1a!.bloomberg.HistoricalDataResponse\"\x00\x12U\n\x12intradayBarRequest\x12\x1d.bloomberg.IntradayBarRequest\x1a\x1e.bloomberg.IntradayBarResponse\"\x00\x12[\n\x14referenceDataRequest\x12\x1f.bloomberg.ReferenceDataRequest\x1a .bloomberg.ReferenceDataResponse\"\x00\x12P\n\x13servicesInfoRequest\x12\x16.google.protobuf.Empty\x1a\x1f.bloomberg.ServicesInfoResponse\"\x00\x12*\n\x04ping\x12\x0f.bloomberg.Ping\x1a\x0f.bloomberg.Pong\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bloomberg_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REFERENCEDATAREQUEST_OPTIONSENTRY']._loaded_options = None
  _globals['_REFERENCEDATAREQUEST_OPTIONSENTRY']._serialized_options = b'8\001'
  _globals['_REFERENCEDATAREQUEST_OVERRIDESENTRY']._loaded_options = None
  _globals['_REFERENCEDATAREQUEST_OVERRIDESENTRY']._serialized_options = b'8\001'
  _globals['_FIELDDATA_FIELDSENTRY']._loaded_options = None
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_options = b'8\001'
  _globals['_MAPVALUE_FIELDSENTRY']._loaded_options = None
  _globals['_MAPVALUE_FIELDSENTRY']._serialized_options = b'8\001'
  _globals['_INTRADAYBARREQUEST_OPTIONSENTRY']._loaded_options = None
  _globals['_INTRADAYBARREQUEST_OPTIONSENTRY']._serialized_options = b'8\001'
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._loaded_options = None
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_options = b'8\001'
  _globals['_HISTORICALDATAREQUEST_OVERRIDESENTRY']._loaded_options = None
  _globals['_HISTORICALDATAREQUEST_OVERRIDESENTRY']._serialized_options = b'8\001'
  _globals['_TOPICTYPE']._serialized_start=3812
  _globals['_TOPICTYPE']._serialized_end=3868
  _globals['_SUBSCRIPTIONTYPE']._serialized_start=3870
  _globals['_SUBSCRIPTIONTYPE']._serialized_end=3916
  _globals['_BARTYPE']._serialized_start=3918
  _globals['_BARTYPE']._serialized_end=4023
  _globals['_ALLBBGFIELDS']._serialized_start=4026
  _globals['_ALLBBGFIELDS']._serialized_end=7718
  _globals['_STATUSTYPE']._serialized_start=7721
  _globals['_STATUSTYPE']._serialized_end=8825
  _globals['_FIELDVAL']._serialized_start=122
  _globals['_FIELDVAL']._serialized_end=200
  _globals['_FIELDVALS']._serialized_start=202
  _globals['_FIELDVALS']._serialized_end=301
  _globals['_BARVALS']._serialized_start=304
  _globals['_BARVALS']._serialized_end=556
  _globals['_STATUS']._serialized_start=558
  _globals['_STATUS']._serialized_end=683
  _globals['_TOPIC']._serialized_start=686
  _globals['_TOPIC']._serialized_end=956
  _globals['_TOPICLIST']._serialized_start=958
  _globals['_TOPICLIST']._serialized_end=1017
  _globals['_REFERENCEDATAREQUEST']._serialized_start=1020
  _globals['_REFERENCEDATAREQUEST']._serialized_end=1302
  _globals['_REFERENCEDATAREQUEST_OPTIONSENTRY']._serialized_start=1206
  _globals['_REFERENCEDATAREQUEST_OPTIONSENTRY']._serialized_end=1252
  _globals['_REFERENCEDATAREQUEST_OVERRIDESENTRY']._serialized_start=1254
  _globals['_REFERENCEDATAREQUEST_OVERRIDESENTRY']._serialized_end=1302
  _globals['_REFERENCEDATARESPONSE']._serialized_start=1304
  _globals['_REFERENCEDATARESPONSE']._serialized_end=1419
  _globals['_RESPONSE']._serialized_start=1421
  _globals['_RESPONSE']._serialized_end=1478
  _globals['_SECURITYDATA']._serialized_start=1481
  _globals['_SECURITYDATA']._serialized_end=1752
  _globals['_EIDDATA']._serialized_start=1754
  _globals['_EIDDATA']._serialized_end=1763
  _globals['_FIELDEXCEPTION']._serialized_start=1765
  _globals['_FIELDEXCEPTION']._serialized_end=1839
  _globals['_ERRORINFO']._serialized_start=1841
  _globals['_ERRORINFO']._serialized_end=1938
  _globals['_FIELDDATA']._serialized_start=1940
  _globals['_FIELDDATA']._serialized_end=2066
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_start=2003
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_end=2066
  _globals['_VALUE']._serialized_start=2069
  _globals['_VALUE']._serialized_end=2283
  _globals['_MAPVALUE']._serialized_start=2285
  _globals['_MAPVALUE']._serialized_end=2409
  _globals['_MAPVALUE_FIELDSENTRY']._serialized_start=2003
  _globals['_MAPVALUE_FIELDSENTRY']._serialized_end=2066
  _globals['_LISTVALUE']._serialized_start=2411
  _globals['_LISTVALUE']._serialized_end=2456
  _globals['_INTRADAYBARREQUEST']._serialized_start=2459
  _globals['_INTRADAYBARREQUEST']._serialized_end=2705
  _globals['_INTRADAYBARREQUEST_OPTIONSENTRY']._serialized_start=1206
  _globals['_INTRADAYBARREQUEST_OPTIONSENTRY']._serialized_end=1252
  _globals['_INTRADAYBARRESPONSE']._serialized_start=2707
  _globals['_INTRADAYBARRESPONSE']._serialized_end=2815
  _globals['_INTRADAYBARDATA']._serialized_start=2818
  _globals['_INTRADAYBARDATA']._serialized_end=2983
  _globals['_HISTORICALDATAREQUEST']._serialized_start=2986
  _globals['_HISTORICALDATAREQUEST']._serialized_end=3355
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_start=1206
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_end=1252
  _globals['_HISTORICALDATAREQUEST_OVERRIDESENTRY']._serialized_start=1254
  _globals['_HISTORICALDATAREQUEST_OVERRIDESENTRY']._serialized_end=1302
  _globals['_HISTORICALDATARESPONSE']._serialized_start=3357
  _globals['_HISTORICALDATARESPONSE']._serialized_end=3473
  _globals['_SERVICESINFOREQUEST']._serialized_start=3475
  _globals['_SERVICESINFOREQUEST']._serialized_end=3508
  _globals['_SERVICESINFORESPONSE']._serialized_start=3510
  _globals['_SERVICESINFORESPONSE']._serialized_end=3574
  _globals['_SERVICEINFO']._serialized_start=3576
  _globals['_SERVICEINFO']._serialized_end=3638
  _globals['_KEYREQUESTID']._serialized_start=3640
  _globals['_KEYREQUESTID']._serialized_end=3666
  _globals['_KEYRESPONSE']._serialized_start=3668
  _globals['_KEYRESPONSE']._serialized_end=3760
  _globals['_PING']._serialized_start=3762
  _globals['_PING']._serialized_end=3785
  _globals['_PONG']._serialized_start=3787
  _globals['_PONG']._serialized_end=3810
  _globals['_KEYMANAGER']._serialized_start=8827
  _globals['_KEYMANAGER']._serialized_end=8904
  _globals['_BBG']._serialized_start=8907
  _globals['_BBG']._serialized_end=9490
# @@protoc_insertion_point(module_scope)
