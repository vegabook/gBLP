# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: example.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rexample.proto\x12\x07\x65xample\"!\n\x0eMessageRequest\x12\x0f\n\x07message\x18\x01 \x01(\t\" \n\x0fMessageResponse\x12\r\n\x05reply\x18\x01 \x01(\t2R\n\x0e\x45xampleService\x12@\n\x0bSendMessage\x12\x17.example.MessageRequest\x1a\x18.example.MessageResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'example_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MESSAGEREQUEST']._serialized_start=26
  _globals['_MESSAGEREQUEST']._serialized_end=59
  _globals['_MESSAGERESPONSE']._serialized_start=61
  _globals['_MESSAGERESPONSE']._serialized_end=93
  _globals['_EXAMPLESERVICE']._serialized_start=95
  _globals['_EXAMPLESERVICE']._serialized_end=177
# @@protoc_insertion_point(module_scope)