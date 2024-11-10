# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import bloomberg_pb2 as bloomberg__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

GRPC_GENERATED_VERSION = '1.65.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.66.0'
SCHEDULED_RELEASE_DATE = 'August 6, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in bloomberg_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class KeyManagerStub(object):
    """Key management
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.requestKey = channel.unary_unary(
                '/bloomberg.KeyManager/requestKey',
                request_serializer=bloomberg__pb2.KeyRequestId.SerializeToString,
                response_deserializer=bloomberg__pb2.KeyResponse.FromString,
                _registered_method=True)


class KeyManagerServicer(object):
    """Key management
    """

    def requestKey(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_KeyManagerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'requestKey': grpc.unary_unary_rpc_method_handler(
                    servicer.requestKey,
                    request_deserializer=bloomberg__pb2.KeyRequestId.FromString,
                    response_serializer=bloomberg__pb2.KeyResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bloomberg.KeyManager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bloomberg.KeyManager', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class KeyManager(object):
    """Key management
    """

    @staticmethod
    def requestKey(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.KeyManager/requestKey',
            bloomberg__pb2.KeyRequestId.SerializeToString,
            bloomberg__pb2.KeyResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class BbgStub(object):
    """Bloomberg API session management
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ping = channel.unary_unary(
                '/bloomberg.Bbg/ping',
                request_serializer=bloomberg__pb2.Ping.SerializeToString,
                response_deserializer=bloomberg__pb2.Pong.FromString,
                _registered_method=True)
        self.pong = channel.unary_unary(
                '/bloomberg.Bbg/pong',
                request_serializer=bloomberg__pb2.Pong.SerializeToString,
                response_deserializer=bloomberg__pb2.Ping.FromString,
                _registered_method=True)
        self.sub = channel.unary_stream(
                '/bloomberg.Bbg/sub',
                request_serializer=bloomberg__pb2.TopicList.SerializeToString,
                response_deserializer=bloomberg__pb2.Topic.FromString,
                _registered_method=True)
        self.unsub = channel.unary_unary(
                '/bloomberg.Bbg/unsub',
                request_serializer=bloomberg__pb2.TopicList.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                _registered_method=True)
        self.subscriptionInfo = channel.unary_unary(
                '/bloomberg.Bbg/subscriptionInfo',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=bloomberg__pb2.TopicList.FromString,
                _registered_method=True)
        self.historicalDataRequest = channel.unary_unary(
                '/bloomberg.Bbg/historicalDataRequest',
                request_serializer=bloomberg__pb2.HistoricalDataRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.HistoricalDataResponse.FromString,
                _registered_method=True)
        self.intradayBarRequest = channel.unary_unary(
                '/bloomberg.Bbg/intradayBarRequest',
                request_serializer=bloomberg__pb2.IntradayBarRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.IntradayBarResponse.FromString,
                _registered_method=True)


class BbgServicer(object):
    """Bloomberg API session management
    """

    def ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def pong(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def sub(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def unsub(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def subscriptionInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def historicalDataRequest(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def intradayBarRequest(self, request, context):
        """rpc intradayTickRequest. maybe "tick" or "gblpTick"
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BbgServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ping': grpc.unary_unary_rpc_method_handler(
                    servicer.ping,
                    request_deserializer=bloomberg__pb2.Ping.FromString,
                    response_serializer=bloomberg__pb2.Pong.SerializeToString,
            ),
            'pong': grpc.unary_unary_rpc_method_handler(
                    servicer.pong,
                    request_deserializer=bloomberg__pb2.Pong.FromString,
                    response_serializer=bloomberg__pb2.Ping.SerializeToString,
            ),
            'sub': grpc.unary_stream_rpc_method_handler(
                    servicer.sub,
                    request_deserializer=bloomberg__pb2.TopicList.FromString,
                    response_serializer=bloomberg__pb2.Topic.SerializeToString,
            ),
            'unsub': grpc.unary_unary_rpc_method_handler(
                    servicer.unsub,
                    request_deserializer=bloomberg__pb2.TopicList.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'subscriptionInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.subscriptionInfo,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=bloomberg__pb2.TopicList.SerializeToString,
            ),
            'historicalDataRequest': grpc.unary_unary_rpc_method_handler(
                    servicer.historicalDataRequest,
                    request_deserializer=bloomberg__pb2.HistoricalDataRequest.FromString,
                    response_serializer=bloomberg__pb2.HistoricalDataResponse.SerializeToString,
            ),
            'intradayBarRequest': grpc.unary_unary_rpc_method_handler(
                    servicer.intradayBarRequest,
                    request_deserializer=bloomberg__pb2.IntradayBarRequest.FromString,
                    response_serializer=bloomberg__pb2.IntradayBarResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bloomberg.Bbg', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bloomberg.Bbg', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Bbg(object):
    """Bloomberg API session management
    """

    @staticmethod
    def ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/ping',
            bloomberg__pb2.Ping.SerializeToString,
            bloomberg__pb2.Pong.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def pong(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/pong',
            bloomberg__pb2.Pong.SerializeToString,
            bloomberg__pb2.Ping.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def sub(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/bloomberg.Bbg/sub',
            bloomberg__pb2.TopicList.SerializeToString,
            bloomberg__pb2.Topic.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def unsub(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/unsub',
            bloomberg__pb2.TopicList.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def subscriptionInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/subscriptionInfo',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            bloomberg__pb2.TopicList.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def historicalDataRequest(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/historicalDataRequest',
            bloomberg__pb2.HistoricalDataRequest.SerializeToString,
            bloomberg__pb2.HistoricalDataResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def intradayBarRequest(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/bloomberg.Bbg/intradayBarRequest',
            bloomberg__pb2.IntradayBarRequest.SerializeToString,
            bloomberg__pb2.IntradayBarResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
