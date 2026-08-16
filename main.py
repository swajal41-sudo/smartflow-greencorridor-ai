"""Entrypoint for SmartFlow I²TMS Server."""
import sys
from server import run

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(port)