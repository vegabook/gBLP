import random
import threading
from rich.console import Console; console = Console()
from rich.panel import Panel
from rich.box import SQUARE
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp

def makeName(alphaLength, digitLength):
    """Make a dummy name if none provided."""
    consonants = "bcdfghjklmnpqrstvwxyz"
    vowels = "aeiou"
    digits = "0123456789"
    word = ''.join(random.choice(consonants if i % 2 == 0 else vowels) 
                for i in range(alphaLength)) + \
                   ''.join(random.choice(digits) for i in range(digitLength))
    return word


def checkThreads():
    for th in threading.enumerate(): 
        if not th.name == "MainThread":
            console.print(f"[bold magenta]Thread {th.name} is still running[/bold magenta]")

def printLicence():
    licencetxt = ("This software is provided 'as is', without warranty of any kind, express "
                  "or implied. The developer of this software assumes no responsibility or "
                  "liability for any use of the software by any party. It is the sole "
                  "responsibility of the user to ensure that their use of this software "
                  "complies with all applicable laws, regulations, and the terms and conditions "
                  "of the Bloomberg API. By using this software, you acknowledge and agree that "
                  "the developer shall not be held liable for any consequences arising from the "
                  "use of this software, including but not limited to, any violations of the "
                  "Bloomberg API terms. This software is licensed under the GPLv3, which means you "
                  "can use, modify, and share it freely, but any distributed modifications must "
                  "also remain open source under the same license.")
    console.print(Panel(licencetxt, title="Licence and Disclaimer", box=SQUARE))

