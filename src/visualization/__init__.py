"""
MIDI Visualization Module

Piano roll displays, chord overlays, and comparison views.
"""

from .piano_roll import plot_piano_roll, plot_midi_comparison
from .chord_overlay import plot_chord_progression, overlay_chords_on_pianoroll

__all__ = [
    'plot_piano_roll',
    'plot_midi_comparison',
    'plot_chord_progression',
    'overlay_chords_on_pianoroll',
]

__version__ = '0.1.0'
