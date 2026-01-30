#!/usr/bin/env python3
"""Entry point for python -m claude_note."""
from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
