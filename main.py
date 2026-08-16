"""Entrypoint for SmartFlow I²TMS Server."""
import sys
from server import run

import os

if __name__ == "__main__":
    env_port = os.environ.get("PORT")
    port = int(env_port) if env_port else (int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
    run(port)