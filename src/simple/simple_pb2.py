# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: simple.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0csimple.proto\x12\x06simple\"3\n\x0cHelloRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x15\n\rnum_greetings\x18\x02 \x01(\t\"\x1d\n\nHelloReply\x12\x0f\n\x07message\x18\x01 \x01(\t\"(\n\nSumRequest\x12\x0c\n\x04num1\x18\x01 \x01(\x05\x12\x0c\n\x04num2\x18\x02 \x01(\x05\"\x1d\n\x0bSumResponse\x12\x0e\n\x06result\x18\x01 \x01(\x05\x32{\n\rsimpleService\x12\x38\n\x08sayHello\x12\x14.simple.HelloRequest\x1a\x12.simple.HelloReply\"\x00\x30\x01\x12\x30\n\x03sum\x12\x12.simple.SumRequest\x1a\x13.simple.SumResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'simple_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_HELLOREQUEST']._serialized_start=24
  _globals['_HELLOREQUEST']._serialized_end=75
  _globals['_HELLOREPLY']._serialized_start=77
  _globals['_HELLOREPLY']._serialized_end=106
  _globals['_SUMREQUEST']._serialized_start=108
  _globals['_SUMREQUEST']._serialized_end=148
  _globals['_SUMRESPONSE']._serialized_start=150
  _globals['_SUMRESPONSE']._serialized_end=179
  _globals['_SIMPLESERVICE']._serialized_start=181
  _globals['_SIMPLESERVICE']._serialized_end=304
# @@protoc_insertion_point(module_scope)