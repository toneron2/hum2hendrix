"""
MIDI Visualization Module

Piano roll displays, chord overlays, and comparison views.
"""

from .piano_roll import extract_notes_from_midi, plot_midi_comparison, plot_piano_roll
from .chord_overlay import overlay_chords_on_pianoroll, parse_chord, plot_chord_progression

__all__ = [
    'extract_notes_from_midi',
    'plot_piano_roll',
    'plot_midi_comparison',
    'parse_chord',
    'plot_chord_progression',
    'overlay_chords_on_pianoroll',
]

__version__ = '0.2.0'
