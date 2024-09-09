# colorscheme iceberg dark

# Copyright 2021 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging

import grpc
import simple_pb2
import simple_pb2_grpc

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--message', default='hello!')
parser.add_argument('--grpchost', default='localhost')
parser.add_argument('--grpcport', default='50051')
parser.add_argument('--insecure', action='store_true', default=False)
from pathlib import Path
import datetime as dt
import time
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp

args = parser.parse_args()

CERT_LOCATION_RELATIVE = Path('../../certs/out').resolve()

async def run() -> None:
    certfile = Path(CERT_LOCATION_RELATIVE, 'client.crt')
    with open(certfile, 'rb') as f:
        client_cert = f.read()

    keyfile = Path(CERT_LOCATION_RELATIVE, 'client.key')
    with open(keyfile, 'rb') as f:
        client_key = f.read()

    CAfile = Path(CERT_LOCATION_RELATIVE, 'zombieCA.crt')
    with open(certfile, 'rb') as f:
        ca_cert = f.read()

    # Create client credentials
    credentials = grpc.ssl_channel_credentials(
        root_certificates=ca_cert,
        private_key=client_key,
        certificate_chain=client_cert)

    hostport = f"{args.grpchost}:{args.grpcport}"

    if args.insecure:
        async with grpc.aio.insecure_channel(hostport) as channel:
            stub = simple_pb2_grpc.simpleServiceStub(channel)
    else:
        async with grpc.aio.secure_channel(hostport, credentials) as channel:
            stub = simple_pb2_grpc.simpleServiceStub(channel)

    # Read from an async generator
    async for response in stub.sayHello(
        simple_pb2.HelloRequest(name=args.message)
    ):
        print(
            "Greeter client received from async generator: "
            + response.message
        )

    # Direct read from the stub
    hello_stream = stub.sayHello(
        simple_pb2.HelloRequest(name=str(args.message))
    )
    while True:
        response = await hello_stream.read()
        if response == grpc.aio.EOF:
            break
        print(
            "Greeter client received from direct read: " + response.message
            )



if __name__ == "__main__":
    logging.basicConfig()
    asyncio.run(run())
