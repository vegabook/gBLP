import random
import threading
from multiprocessing import Process, active_children
from rich.console import Console; console = Console()
from rich.panel import Panel
from rich.box import SQUARE
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp
import logging; logger = logging.getLogger(__name__)
import os
import requests
import platform

def makeName(alphaLength, digitLength, alsoUserDetails = False):
    """Make a dummy name if none provided."""
    consonants = "bcdfghjklmnpqrstvwxyz"
    vowels = "aeiou"
    digits = "0123456789"
    word = ''.join(random.choice(consonants if i % 2 == 0 else vowels) 
                for i in range(alphaLength)) + \
                   ''.join(random.choice(digits) for i in range(digitLength))
    if alsoUserDetails:
        word += "|" + getUserName() + "|" + getPlatform() + "|" + getExternalIP()
    return word


def checkThreads(colour = "magenta", processes = True):
    print("------------- Threads -------------")
    for th in threading.enumerate(): 
        if not th.name == "MainThread":
            console.print(f"[{colour}]Thread {th.name} is still running[{colour}]")
    if processes:
        print("------------- Processes-------------")
        for proc in active_children():
            console.print((f"[bold {colour}]Name: {proc.name}, "
                           f"PID: {proc.pid}, Is Alive: {proc.is_alive()}[/bold {colour}]"))
    print("------------------------------------")


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
    title = f"[bold grey50]LICENCE AND DISCLAIMER[/bold grey50]"
    panel = Panel(licencetxt, title=title, box=SQUARE, style="grey50")
    console.print(panel)

def printBeta():
    betatxt = ("This software is currently in beta testing. Features may be unstable "
               "and undergoing ongoing testing. Please continuously monitor the repository "
               "https://github.com/vegabook/gBLP for updates and bug fixes. THE API REMAINS SUBJECT TO CHANGE.")
               
    title = f"[bold orange1]BETA[/bold orange1]"
    panel = Panel(betatxt, box=SQUARE, style="orange1", title=title)
    console.print(panel)


def exitNotNT():
    if os.name != "nt":
        console.print("gBLP server runs on Windows only.")
        exit(1)

def getExternalIP():
    try:
        ip = requests.get("https://api.ipify.org").text
        return ip
    except Exception as e:
        logger.error(f"Error getting external IP: {e}")
        return "failIP"

def getUserName():
    try: 
        return os.getlogin()
    except Exception as e:
        logger.error(f"Error getting username: {e}")
        return "failUserName"

def getPlatform():
    try:
        return platform.platform()
    except Exception as e:
        logger.error(f"Error getting platform: {e}")
        return "failPlatform"


if __name__ == "__main__":
    printLicence()
    printBeta()
    print(makeName(5, 5, True))
    print(getExternalIP())
    print(getUserName())
    print(getPlatform())
    checkThreads()
    checkThreads()
    checkThreads("green")
    print("Done")
    exit(0)


