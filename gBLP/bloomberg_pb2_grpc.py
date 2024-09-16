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
        self.sayHello = channel.unary_stream(
                '/bloomberg.KeyManager/sayHello',
                request_serializer=bloomberg__pb2.HelloRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.HelloReply.FromString,
                _registered_method=True)
        self.sum = channel.unary_unary(
                '/bloomberg.KeyManager/sum',
                request_serializer=bloomberg__pb2.SumRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.SumResponse.FromString,
                _registered_method=True)


class KeyManagerServicer(object):
    """Key management
    """

    def requestKey(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def sayHello(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def sum(self, request, context):
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
            'sayHello': grpc.unary_stream_rpc_method_handler(
                    servicer.sayHello,
                    request_deserializer=bloomberg__pb2.HelloRequest.FromString,
                    response_serializer=bloomberg__pb2.HelloReply.SerializeToString,
            ),
            'sum': grpc.unary_unary_rpc_method_handler(
                    servicer.sum,
                    request_deserializer=bloomberg__pb2.SumRequest.FromString,
                    response_serializer=bloomberg__pb2.SumResponse.SerializeToString,
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

    @staticmethod
    def sayHello(request,
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
            '/bloomberg.KeyManager/sayHello',
            bloomberg__pb2.HelloRequest.SerializeToString,
            bloomberg__pb2.HelloReply.FromString,
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
    def sum(request,
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
            '/bloomberg.KeyManager/sum',
            bloomberg__pb2.SumRequest.SerializeToString,
            bloomberg__pb2.SumResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class SessionManagerStub(object):
    """Bloomberg API session management
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.sayHello = channel.unary_stream(
                '/bloomberg.SessionManager/sayHello',
                request_serializer=bloomberg__pb2.HelloRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.HelloReply.FromString,
                _registered_method=True)
        self.sum = channel.unary_unary(
                '/bloomberg.SessionManager/sum',
                request_serializer=bloomberg__pb2.SumRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.SumResponse.FromString,
                _registered_method=True)
        self.getDefaultOptions = channel.unary_unary(
                '/bloomberg.SessionManager/getDefaultOptions',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=bloomberg__pb2.SessionOptions.FromString,
                _registered_method=True)
        self.openSession = channel.unary_unary(
                '/bloomberg.SessionManager/openSession',
                request_serializer=bloomberg__pb2.SessionOptions.SerializeToString,
                response_deserializer=bloomberg__pb2.Session.FromString,
                _registered_method=True)
        self.makeStream = channel.unary_stream(
                '/bloomberg.SessionManager/makeStream',
                request_serializer=bloomberg__pb2.SubscriptionList.SerializeToString,
                response_deserializer=bloomberg__pb2.SubscriptionMessage.FromString,
                _registered_method=True)
        self.sessionInfo = channel.unary_unary(
                '/bloomberg.SessionManager/sessionInfo',
                request_serializer=bloomberg__pb2.Session.SerializeToString,
                response_deserializer=bloomberg__pb2.Session.FromString,
                _registered_method=True)
        self.unsubscribe = channel.unary_unary(
                '/bloomberg.SessionManager/unsubscribe',
                request_serializer=bloomberg__pb2.Session.SerializeToString,
                response_deserializer=bloomberg__pb2.Session.FromString,
                _registered_method=True)
        self.closeSession = channel.unary_unary(
                '/bloomberg.SessionManager/closeSession',
                request_serializer=bloomberg__pb2.Session.SerializeToString,
                response_deserializer=bloomberg__pb2.Session.FromString,
                _registered_method=True)
        self.historicalDataRequest = channel.unary_unary(
                '/bloomberg.SessionManager/historicalDataRequest',
                request_serializer=bloomberg__pb2.HistoricalDataRequest.SerializeToString,
                response_deserializer=bloomberg__pb2.HistoricalDataResponse.FromString,
                _registered_method=True)


class SessionManagerServicer(object):
    """Bloomberg API session management
    """

    def sayHello(self, request, context):
        """basic examples TODO delete later
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def sum(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def getDefaultOptions(self, request, context):
        """Bloomberg
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def openSession(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def makeStream(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def sessionInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def unsubscribe(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def closeSession(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def historicalDataRequest(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SessionManagerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'sayHello': grpc.unary_stream_rpc_method_handler(
                    servicer.sayHello,
                    request_deserializer=bloomberg__pb2.HelloRequest.FromString,
                    response_serializer=bloomberg__pb2.HelloReply.SerializeToString,
            ),
            'sum': grpc.unary_unary_rpc_method_handler(
                    servicer.sum,
                    request_deserializer=bloomberg__pb2.SumRequest.FromString,
                    response_serializer=bloomberg__pb2.SumResponse.SerializeToString,
            ),
            'getDefaultOptions': grpc.unary_unary_rpc_method_handler(
                    servicer.getDefaultOptions,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=bloomberg__pb2.SessionOptions.SerializeToString,
            ),
            'openSession': grpc.unary_unary_rpc_method_handler(
                    servicer.openSession,
                    request_deserializer=bloomberg__pb2.SessionOptions.FromString,
                    response_serializer=bloomberg__pb2.Session.SerializeToString,
            ),
            'makeStream': grpc.unary_stream_rpc_method_handler(
                    servicer.makeStream,
                    request_deserializer=bloomberg__pb2.SubscriptionList.FromString,
                    response_serializer=bloomberg__pb2.SubscriptionMessage.SerializeToString,
            ),
            'sessionInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.sessionInfo,
                    request_deserializer=bloomberg__pb2.Session.FromString,
                    response_serializer=bloomberg__pb2.Session.SerializeToString,
            ),
            'unsubscribe': grpc.unary_unary_rpc_method_handler(
                    servicer.unsubscribe,
                    request_deserializer=bloomberg__pb2.Session.FromString,
                    response_serializer=bloomberg__pb2.Session.SerializeToString,
            ),
            'closeSession': grpc.unary_unary_rpc_method_handler(
                    servicer.closeSession,
                    request_deserializer=bloomberg__pb2.Session.FromString,
                    response_serializer=bloomberg__pb2.Session.SerializeToString,
            ),
            'historicalDataRequest': grpc.unary_unary_rpc_method_handler(
                    servicer.historicalDataRequest,
                    request_deserializer=bloomberg__pb2.HistoricalDataRequest.FromString,
                    response_serializer=bloomberg__pb2.HistoricalDataResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'bloomberg.SessionManager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bloomberg.SessionManager', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class SessionManager(object):
    """Bloomberg API session management
    """

    @staticmethod
    def sayHello(request,
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
            '/bloomberg.SessionManager/sayHello',
            bloomberg__pb2.HelloRequest.SerializeToString,
            bloomberg__pb2.HelloReply.FromString,
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
    def sum(request,
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
            '/bloomberg.SessionManager/sum',
            bloomberg__pb2.SumRequest.SerializeToString,
            bloomberg__pb2.SumResponse.FromString,
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
    def getDefaultOptions(request,
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
            '/bloomberg.SessionManager/getDefaultOptions',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            bloomberg__pb2.SessionOptions.FromString,
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
    def openSession(request,
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
            '/bloomberg.SessionManager/openSession',
            bloomberg__pb2.SessionOptions.SerializeToString,
            bloomberg__pb2.Session.FromString,
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
    def makeStream(request,
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
            '/bloomberg.SessionManager/makeStream',
            bloomberg__pb2.SubscriptionList.SerializeToString,
            bloomberg__pb2.SubscriptionMessage.FromString,
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
    def sessionInfo(request,
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
            '/bloomberg.SessionManager/sessionInfo',
            bloomberg__pb2.Session.SerializeToString,
            bloomberg__pb2.Session.FromString,
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
    def unsubscribe(request,
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
            '/bloomberg.SessionManager/unsubscribe',
            bloomberg__pb2.Session.SerializeToString,
            bloomberg__pb2.Session.FromString,
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
    def closeSession(request,
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
            '/bloomberg.SessionManager/closeSession',
            bloomberg__pb2.Session.SerializeToString,
            bloomberg__pb2.Session.FromString,
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
            '/bloomberg.SessionManager/historicalDataRequest',
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
