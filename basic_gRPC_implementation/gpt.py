# colorscheme wood light

import grpc
from concurrent import futures
import example_pb2
import example_pb2_grpc
import threading

class ExampleService(example_pb2_grpc.ExampleServiceServicer):
    def SendMessage(self, request, context):
        print(f"Received message: {request.message}")
        return example_pb2.MessageResponse(reply=f"Replying to: {request.message}")

def serve():
    # gRPC named pipe address
    pipe_name = "localhost:49220"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    example_pb2_grpc.add_ExampleServiceServicer_to_server(ExampleService(), server)
    server.add_insecure_port(pipe_name)
    print(f"Server is running on named pipe: {pipe_name}")
    server.start()
    return server

def run_client():
    pipe_name = "localhost:49220"
    channel = grpc.insecure_channel(pipe_name)
    stub = example_pb2_grpc.ExampleServiceStub(channel)
    response = stub.SendMessage(example_pb2.MessageRequest(message="Hello, Server!"))
    print(f"Server replied: {response.reply}")

    import threading
import time

if __name__ == "__main__":
    # Start the server in a separate thread
    server = serve()
    server_thread = threading.Thread(target=server.wait_for_termination)
    server_thread.start()

    # Allow some time for the server to start
    time.sleep(1)

    # Run the client
    run_client()

    # Stop the server
    server.stop(0)
    server_thread.join()


