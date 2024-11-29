# colorscheme blue dark

# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------

from gBLP.util.utils import makeName, printLicence, checkThreads, exitNotNT, printBeta

from rich.console import Console; console = Console()
from rich.pretty import pprint
from rich.logging import RichHandler
import logging
from multiprocessing import Manager

from rich.logging import RichHandler

# Set up the custom handler
class CustomRichHandler(RichHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

logger = logging.getLogger(__name__)  # Scoped to the current module
logger.setLevel(logging.DEBUG)  # Set logging level

if logger.hasHandlers():
    logger.handlers.clear()

custom_handler = CustomRichHandler()
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(processName)s | %(funcName)s | %(message)s"
)
custom_handler.setFormatter(formatter)
logger.addHandler(custom_handler)

# Example log
logger.debug("This is a debug message")


import os
os.environ["GRPC_VERBOSITY"] = "DEBUG"
os.environ["GRPC_TRACE"] = "secure_handshake,security"

import grpc; grpc.aio.init_grpc_aio()

# python imports

import asyncio
import string
import random
from collections import defaultdict
import json
import datetime as dt
import threading
import signal
import queue
import traceback
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes 

# gRPC imports
import grpc; grpc.aio.init_grpc_aio() # logging
from grpc.aio import ServerInterceptor

from bloomberg_pb2 import Ping, Pong, KeyRequestId, KeyResponse

from bloomberg_pb2_grpc import BbgServicer, KeyManagerServicer
from bloomberg_pb2_grpc import add_BbgServicer_to_server, \
    add_KeyManagerServicer_to_server

from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
from google.protobuf import empty_pb2

from argparse import ArgumentParser, RawTextHelpFormatter

from util.certMaker import get_conf_dir, make_client_certs, make_all_certs, check_for_certs
from util.utils import makeName, printLicence, checkThreads


# ----------------- global variables ----------------------

globalOptions = None

from gBLP.constants import DEFAULT_FIELDS

# ----------------- thread creation tracking ----------------------
def trace_function(frame, event, arg):
    """Trace function that will be called for every line of code in every thread."""
    if threading.current_thread().name != "asyncio_0":
        if event == 'call':
            console.print(f"[bold blue]Calling function: {frame.f_code.co_name} in {threading.current_thread().name}")
        elif event == 'line':
            console.print(f"[bold green]Line {frame.f_lineno} in {frame.f_code.co_name} in {threading.current_thread().name}")
        elif event == 'return':
            console.print(f"[bold red]Returning from {frame.f_code.co_name} in {threading.current_thread().name}")
        return trace_function  # Return itself to continue tracing

# Set this trace function to be used for all new threads
# threading.settrace(trace_function)
# ----------------- util functions ----------------------

def serialize_datetime(obj): 
    if isinstance(obj, dt.datetime) or isinstance(obj, dt.date):
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

# ----------------- parse the command line and session options ---------------

def parseCmdLine():
    """Parse command line arguments"""
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "--grpchost",
        dest="grpchost",
        help="Hostname that this gRPC will respond to.",
        type=str)
    parser.add_argument(
        "--grpcport",
        dest="grpcport",
        type=str,
        help="Bloomberg session grpc port",
        default="50051")
    parser.add_argument(
        "--grpckeyport",
        dest="grpckeyport",
        type=str,
        help="Key request grpc port (for client certificates)",
        default="50052")
    # add a boolean make-cert argument
    parser.add_argument(
        "--gencerts",
        dest="gencerts",
        help="Generate a self-signed certificate",
        action="store_true",
        default=False)
    parser.add_argument(
        "--delcerts",
        dest="delcerts",
        help="Delete all certificates",
        action="store_true",
        default=False)
    options = parser.parse_args()
    return options



# ----------------- keys manager for mTLS ----------------------

class KeyManager(KeyManagerServicer):
    # responds on an insecure port with client certificates
    # but only if authorised by the server. 

    def __init__(self):
        pass


    async def requestKey(self, 
                         request: KeyRequestId, 
                         context: grpc.aio.ServicerContext) -> KeyResponse:
        logging.info("Serving keyRequest request %s", request)
        await asyncio.sleep(1)
        key, cert, cacert = make_client_certs(globalOptions.grpchost, get_conf_dir())
        bcacert = cacert.public_bytes(serialization.Encoding.PEM)
        logger.info(f"Key request granted for {request.id} and {context.peer()}")
        return KeyResponse(key=key, cert=cert, cacert=bcacert, authorised=True)


async def serveBbgSession(bbgAioServer, bbgManager) -> None:

    listenAddr = f"{globalOptions.grpchost}:{globalOptions.grpcport}"
    add_BbgServicer_to_server(bbgManager, bbgAioServer)

    confdir = get_conf_dir()

    # Load server's certificate and private key
    with open(confdir / "server_certificate.pem", "rb") as f:
        serverCert = f.read()
    with open(confdir / "server_private_key.pem", "rb") as f:
        serverKey = f.read()
    # Load CA certificate to verify clients
    with open(confdir / "ca_certificate.pem", "rb") as f:
        CAcert = f.read()


    serverCredentials = grpc.ssl_server_credentials(
        [(serverKey, serverCert)],
        root_certificates=CAcert,
        require_client_auth=True,  # Require clients to provide valid certificates
    )
    bbgAioServer.add_secure_port(listenAddr, serverCredentials) 

    await bbgAioServer.start()
    logging.info(f"Starting session server on {listenAddr}")
    await bbgAioServer.wait_for_termination()
    await bbgManager.close()
    logging.info("Sessions server stopped.")
    #raise # propagate


async def serveKeySession(keyAioServer) -> None:

    keyListenAddr = f"{globalOptions.grpchost}:{globalOptions.grpckeyport}"
    add_KeyManagerServicer_to_server(KeyManager(), keyAioServer)
    keyAioServer.add_insecure_port(keyListenAddr) # this listens without credentials

    await keyAioServer.start()
    logging.info(f"Starting key server on {keyListenAddr}")
    await keyAioServer.wait_for_termination()

            
# ----------------- gRPC method implementations ----------------------

class ConnectionLoggingInterceptor(ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        console.print(f"[cyan]Incoming connection: {handler_call_details.method}")
        # Proceed with the normal handling of the RPC
        return await continuation(handler_call_details)



class Bbg(BbgServicer):
    # implements all the gRPC methods for the session manager
    # and communicates with the SessionRunner(s)

    def __init__(self, options, comq, done, manager):
        self.options = options
        self.done = done

    def makeClientID(self, context):
        client = dict(context.invocation_metadata())["client"]
        ip = context.peer().split(":")[1]
        return f"{client}:{ip}"

    async def closeSession(self):
        await self.session.close()


    async def Ping(self, request: Ping, context: grpc.aio.ServicerContext) -> Pong:
        clientid = self.makeClientID(context)
        logger.info(f"Received ping from {clientid}")
        timestamp = google.protobuf.timestamp_pb2.Timestamp()
        timestamp.GetCurrentTime()
        message = request.message + " Pong"
        pong = Pong(timestamp=timestamp, message=message)
        return pong

# ----------------- mains ----------------------


async def asyncMain(globalOptions):
    bbgAioServer = grpc.aio.server(interceptors=(ConnectionLoggingInterceptor(),))
    keyAioServer = grpc.aio.server()
    manager = Manager()
    comq = manager.Queue() # communication queue
    #done = manager.Event()
    done = manager.Event()
    bbgManager = Bbg(globalOptions, comq, done, manager)
    bbgTask = asyncio.create_task(serveBbgSession(bbgAioServer, bbgManager))
    keyTask = asyncio.create_task(serveKeySession(keyAioServer))
    console.print("[bold blue]--------------------------")
    console.print("[bold red on white blink]Press Q to stop the server")
    console.print("[bold blue]--------------------------")
    await asyncio.to_thread(done.wait)
    logger.info("done waiting for. Stopping gRPC servers...")
    await bbgAioServer.stop(grace=3)
    logger.info("gRPC server stopped.") 
    await keyAioServer.stop(grace=3)
    logger.info("Key server stopped.")
    logger.info("Gathering asyncio gRPC task wrappers...")
    await asyncio.gather(bbgTask, keyTask)
    logger.info("All tasks stopped. Exiting.")
    os._exit(0)


def main():
    global globalOptions
    logging.basicConfig(level=logging.DEBUG)
    globalOptions = parseCmdLine()
    if globalOptions.gencerts:
        if not globalOptions.grpchost:
            print(("Must specify --grpchost xxxx where xxx is server hostname or IP address "
                   "when using --gencerts."))
            return
        else:
            confdir = get_conf_dir()
            make_all_certs(str(globalOptions.grpchost), confdir)
    elif not check_for_certs():
        print(("Secure TLS/SSL credentials not found. to create them: "
              "server_gblp --gencerts --grpchost xxxx "
              "where xxxx is the server hostname or IP address."))
        return
    elif globalOptions.delcerts:
        confdir = get_conf_dir()
        for f in confdir.glob("*.pem"):
            f.unlink()
        print("Deleted all certificates. Run --gencerts to make new ones.")
    elif not globalOptions.grpchost:
        console.print("[bold red]Must specify --grpchost xxxx where xxxx is server hostname or IP address.")
    else:
        printBeta()
        printLicence()
        try:
            asyncio.run(asyncMain(globalOptions))
            logger.debug("asyncio main() exited")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            console.print("[bold magenta on white]You should press <Enter> to stop the server.")
            console.print("[bold white on red] Killing all threads and processes.")
            done.set()
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Caught exception {e}")
        finally:
            for th in threading.enumerate(): 
                if not th.name == "MainThread":
                    console.print(f"[bold magenta]Thread {th.name} is still running[/bold magenta]")
            console.print("[bold green on white]os._exit(0)")
            os._exit(1)


if __name__ == "__main__":
    main()
