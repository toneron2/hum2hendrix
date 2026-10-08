"""
Audio-to-MIDI Conversion Module

Converts hummed audio into MIDI note events using deep learning pitch detection.
"""

from .converter import AudioToMIDIConverter
from .pitch_detection import (
    detect_notes_basic_pitch,
    detect_pitch_crepe,
    detect_pitch_librosa,
)

__all__ = [
    'AudioToMIDIConverter',
    'detect_notes_basic_pitch',
    'detect_pitch_crepe',
    'detect_pitch_librosa',
]

__version__ = '0.1.0'
