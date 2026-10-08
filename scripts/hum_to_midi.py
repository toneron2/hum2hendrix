#!/usr/bin/env python3
"""
Audio to MIDI Converter CLI

Thin wrapper around pipeline.cli.audio_to_midi so the tool runs from a checkout
without installing the package. Installed users get the same command from
the console script in setup.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from pipeline.cli import audio_to_midi  # noqa: E402

if __name__ == '__main__':
    audio_to_midi()
