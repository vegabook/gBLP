#!/bin/sh
python -m grpc_tools.protoc -I. --python_out=../gBLP --grpc_python_out=../gBLP bloomberg.proto
sed -i 's/^import bloomberg_pb2 as/import gBLP.bloomberg_pb2 as/' ../gBLP/bloomberg_pb2_grpc.py

