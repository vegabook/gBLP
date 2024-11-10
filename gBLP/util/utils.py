import random
import threading
from rich.console import Console; console = Console()

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
