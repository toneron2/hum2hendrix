#!/usr/bin/env python3
"""
MIDI Visualization CLI

Thin wrapper around pipeline.cli.visualize so the tool runs from a checkout
without installing the package. Installed users get the same command from
the console script in setup.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pipeline.cli import visualize  # noqa: E402

if __name__ == '__main__':
    visualize()
