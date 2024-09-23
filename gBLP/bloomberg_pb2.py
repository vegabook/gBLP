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
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0f\x62loomberg.proto\x12\tbloomberg\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a\x19google/protobuf/any.proto\"K\n\x0eSessionOptions\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x10\n\x08interval\x18\x02 \x01(\x05\x12\x19\n\x11maxEventQueueSize\x18\x03 \x01(\x05\"\xc5\x01\n\x05Topic\x12\x0c\n\x04name\x18\x01 \x01(\t\x12(\n\x04type\x18\x02 \x01(\x0e\x32\x1a.bloomberg.Topic.topicType\x12\x0e\n\x06\x66ields\x18\x03 \x03(\t\x12\x10\n\x08interval\x18\x04 \x01(\x05\x12\x11\n\tvalidated\x18\x05 \x01(\x08\x12\x12\n\nterminated\x18\x06 \x01(\x08\";\n\ttopicType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\n\n\x06TICKER\x10\x01\x12\n\n\x06SEDOL1\x10\x02\x12\t\n\x05\x43USIP\x10\x03\"4\n\x10SubscriptionList\x12 \n\x06topics\x18\x01 \x03(\x0b\x32\x10.bloomberg.Topic\"\xb9\x01\n\x18SubscriptionDataResponse\x12\x0f\n\x07msgtype\x18\x01 \x01(\t\x12\r\n\x05topic\x18\x02 \x01(\t\x12-\n\ttimestamp\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\'\n\x06\x66ields\x18\x04 \x03(\x0b\x32\x17.bloomberg.SubFieldData\x12\x11\n\tvalidated\x18\x05 \x01(\x08\x12\x12\n\nterminated\x18\x06 \x01(\x08\"D\n\x0cSubFieldData\x12\r\n\x05\x66ield\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value\"o\n\x07Session\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x10\n\x08services\x18\x02 \x03(\t\x12\x35\n\x10subscriptionList\x18\x03 \x01(\x0b\x32\x1b.bloomberg.SubscriptionList\x12\r\n\x05\x61live\x18\x04 \x01(\x08\"\xa0\x02\n\x15HistoricalDataRequest\x12#\n\x07session\x18\x01 \x01(\x0b\x32\x12.bloomberg.Session\x12\x0e\n\x06topics\x18\x02 \x03(\t\x12\x0e\n\x06\x66ields\x18\x03 \x03(\t\x12)\n\x05start\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\'\n\x03\x65nd\x18\x05 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12>\n\x07options\x18\x06 \x03(\x0b\x32-.bloomberg.HistoricalDataRequest.OptionsEntry\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"N\n\x16HistoricalDataResponse\x12\x34\n\x05items\x18\x01 \x03(\x0b\x32%.bloomberg.HistoricalDataResponseItem\"L\n\x1aHistoricalDataResponseItem\x12.\n\rsecurity_data\x18\x01 \x01(\x0b\x32\x17.bloomberg.SecurityData\"\xbb\x01\n\x0cSecurityData\x12\x10\n\x08security\x18\x01 \x01(\t\x12&\n\x08\x65id_data\x18\x02 \x03(\x0b\x32\x14.google.protobuf.Any\x12\x17\n\x0fsequence_number\x18\x03 \x01(\x05\x12.\n\x10\x66ield_exceptions\x18\x04 \x03(\x0b\x32\x14.google.protobuf.Any\x12(\n\nfield_data\x18\x05 \x03(\x0b\x32\x14.bloomberg.FieldData\"\xae\x01\n\tFieldData\x12(\n\x04\x64\x61te\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x30\n\x06\x66ields\x18\x02 \x03(\x0b\x32 .bloomberg.FieldData.FieldsEntry\x1a\x45\n\x0b\x46ieldsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value:\x02\x38\x01\"\x1a\n\x0cKeyRequestId\x12\n\n\x02id\x18\x01 \x01(\t\"8\n\x0bKeyResponse\x12\x0b\n\x03key\x18\x01 \x01(\x0c\x12\x0c\n\x04\x63\x65rt\x18\x02 \x01(\x0c\x12\x0e\n\x06\x63\x61\x63\x65rt\x18\x03 \x01(\x0c\x32M\n\nKeyManager\x12?\n\nrequestKey\x12\x17.bloomberg.KeyRequestId\x1a\x16.bloomberg.KeyResponse\"\x00\x32\xb1\x04\n\x0fSessionsManager\x12H\n\x11getDefaultOptions\x12\x16.google.protobuf.Empty\x1a\x19.bloomberg.SessionOptions\"\x00\x12>\n\x0bopenSession\x12\x19.bloomberg.SessionOptions\x1a\x12.bloomberg.Session\"\x00\x12Q\n\x12subscriptionStream\x12\x12.bloomberg.Session\x1a#.bloomberg.SubscriptionDataResponse\"\x00\x30\x01\x12\x35\n\tsubscribe\x12\x12.bloomberg.Session\x1a\x12.bloomberg.Session\"\x00\x12\x37\n\x0bunsubscribe\x12\x12.bloomberg.Session\x1a\x12.bloomberg.Session\"\x00\x12\x37\n\x0bsessionInfo\x12\x12.bloomberg.Session\x1a\x12.bloomberg.Session\"\x00\x12\x38\n\x0c\x63loseSession\x12\x12.bloomberg.Session\x1a\x12.bloomberg.Session\"\x00\x12^\n\x15historicalDataRequest\x12 .bloomberg.HistoricalDataRequest\x1a!.bloomberg.HistoricalDataResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bloomberg_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._loaded_options = None
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_options = b'8\001'
  _globals['_FIELDDATA_FIELDSENTRY']._loaded_options = None
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_options = b'8\001'
  _globals['_SESSIONOPTIONS']._serialized_start=149
  _globals['_SESSIONOPTIONS']._serialized_end=224
  _globals['_TOPIC']._serialized_start=227
  _globals['_TOPIC']._serialized_end=424
  _globals['_TOPIC_TOPICTYPE']._serialized_start=365
  _globals['_TOPIC_TOPICTYPE']._serialized_end=424
  _globals['_SUBSCRIPTIONLIST']._serialized_start=426
  _globals['_SUBSCRIPTIONLIST']._serialized_end=478
  _globals['_SUBSCRIPTIONDATARESPONSE']._serialized_start=481
  _globals['_SUBSCRIPTIONDATARESPONSE']._serialized_end=666
  _globals['_SUBFIELDDATA']._serialized_start=668
  _globals['_SUBFIELDDATA']._serialized_end=736
  _globals['_SESSION']._serialized_start=738
  _globals['_SESSION']._serialized_end=849
  _globals['_HISTORICALDATAREQUEST']._serialized_start=852
  _globals['_HISTORICALDATAREQUEST']._serialized_end=1140
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_start=1094
  _globals['_HISTORICALDATAREQUEST_OPTIONSENTRY']._serialized_end=1140
  _globals['_HISTORICALDATARESPONSE']._serialized_start=1142
  _globals['_HISTORICALDATARESPONSE']._serialized_end=1220
  _globals['_HISTORICALDATARESPONSEITEM']._serialized_start=1222
  _globals['_HISTORICALDATARESPONSEITEM']._serialized_end=1298
  _globals['_SECURITYDATA']._serialized_start=1301
  _globals['_SECURITYDATA']._serialized_end=1488
  _globals['_FIELDDATA']._serialized_start=1491
  _globals['_FIELDDATA']._serialized_end=1665
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_start=1596
  _globals['_FIELDDATA_FIELDSENTRY']._serialized_end=1665
  _globals['_KEYREQUESTID']._serialized_start=1667
  _globals['_KEYREQUESTID']._serialized_end=1693
  _globals['_KEYRESPONSE']._serialized_start=1695
  _globals['_KEYRESPONSE']._serialized_end=1751
  _globals['_KEYMANAGER']._serialized_start=1753
  _globals['_KEYMANAGER']._serialized_end=1830
  _globals['_SESSIONSMANAGER']._serialized_start=1833
  _globals['_SESSIONSMANAGER']._serialized_end=2394
# @@protoc_insertion_point(module_scope)
