"""
Chord Progression Overlay

Display chord progressions alongside melodies on piano roll.
"""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from quantization.scales import ROOT_NOTES

from .piano_roll import (
    DEFAULT_DPI,
    add_velocity_colorbar,
    draw_notes,
    extract_notes_from_midi,
    finish_figure,
    note_bounds,
    style_piano_axes,
)

# (chord_symbol, start_time, duration) in seconds
Chord = Tuple[str, float, float]

# Chord qualities as semitones from root
CHORD_TEMPLATES = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    '7': [0, 4, 7, 10],  # Dominant 7
    'min7b5': [0, 3, 6, 10],  # Half-diminished
    'dim': [0, 3, 6],
    'dim7': [0, 3, 6, 9],
    'aug': [0, 4, 8],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
    '6': [0, 4, 7, 9],
    'min6': [0, 3, 7, 9],
    '9': [0, 4, 7, 10, 14],
    'maj9': [0, 4, 7, 11, 14],
    'min9': [0, 3, 7, 10, 14],
}

# Chord-symbol suffix -> template name. Case matters: 'M' is major, 'm' is minor.
QUALITY_ALIASES = {
    '': 'major', 'M': 'major', 'maj': 'major', 'Maj': 'major',
    'm': 'minor', 'min': 'minor', '-': 'minor',
    'maj7': 'maj7', 'Maj7': 'maj7', 'M7': 'maj7',
    'm7': 'min7', 'min7': 'min7', '-7': 'min7',
    '7': '7', 'dom7': '7',
    'm7b5': 'min7b5', 'min7b5': 'min7b5', 'ø': 'min7b5', 'ø7': 'min7b5',
    'dim': 'dim', 'o': 'dim', '°': 'dim',
    'dim7': 'dim7', 'o7': 'dim7', '°7': 'dim7',
    'aug': 'aug', '+': 'aug',
    'sus4': 'sus4', 'sus': 'sus4',
    'sus2': 'sus2',
    '6': '6', 'M6': '6', 'maj6': '6',
    'm6': 'min6', 'min6': 'min6',
    '9': '9', 'dom9': '9',
    'maj9': 'maj9', 'Maj9': 'maj9', 'M9': 'maj9',
    'm9': 'min9', 'min9': 'min9',
}


def parse_chord(chord_symbol: str, octave: int = 4) -> Tuple[str, List[int]]:
    """
    Parse chord symbol into MIDI notes.

    Args:
        chord_symbol: Chord symbol (e.g., 'Em7', 'Gmaj7', 'Am', 'Bbm7b5')
        octave: Octave of the root, with C4 = MIDI 60

    Returns:
        (chord_symbol, list of MIDI notes)

    Raises:
        ValueError: on an unknown root or chord quality

    Examples:
        >>> parse_chord('Em7', 4)
        ('Em7', [64, 67, 71, 74])  # E, G, B, D
    """
    symbol = chord_symbol.strip()
    if not symbol:
        raise ValueError("Empty chord symbol")

    if len(symbol) > 1 and symbol[1] in ('#', 'b'):
        root_str, quality_str = symbol[:2], symbol[2:]
    else:
        root_str, quality_str = symbol[:1], symbol[1:]

    if root_str not in ROOT_NOTES:
        raise ValueError(f"Unknown root note in chord {chord_symbol!r}: {root_str!r}")
    if quality_str not in QUALITY_ALIASES:
        raise ValueError(
            f"Unknown chord quality in {chord_symbol!r}: {quality_str!r}. "
            f"Known: {', '.join(sorted(k for k in QUALITY_ALIASES if k))}"
        )

    intervals = CHORD_TEMPLATES[QUALITY_ALIASES[quality_str]]
    root_midi = (octave + 1) * 12 + ROOT_NOTES[root_str]
    return chord_symbol, [root_midi + interval for interval in intervals]


def chord_pitch_classes(chord_symbol: str) -> List[int]:
    """Pitch classes (0-11) of a chord symbol, root first."""
    _, notes = parse_chord(chord_symbol)
    return [n % 12 for n in notes]


def draw_chords(ax: plt.Axes, chords: Sequence[Chord], fontsize: int = 12) -> None:
    """Draw a chord timeline as labelled coloured blocks on `ax`."""
    cmap = plt.cm.Set3
    rects = [Rectangle((start, 0), duration, 1) for _, start, duration in chords]
    colors = [cmap(i % cmap.N) for i in range(len(chords))]
    ax.add_collection(PatchCollection(
        rects, facecolors=colors, edgecolors='black', linewidths=2, alpha=0.7,
    ))

    for symbol, start, duration in chords:
        ax.text(
            start + duration / 2, 0.5, symbol,
            ha='center', va='center', fontsize=fontsize, fontweight='bold',
        )

    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(True, axis='x', alpha=0.3)


def chords_end_time(chords: Sequence[Chord]) -> float:
    return max((start + duration for _, start, duration in chords), default=0.0)


def plot_chord_progression(
    chords: List[Chord],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 6),
    dpi: int = DEFAULT_DPI,
) -> None:
    """
    Plot chord progression as a timeline.

    Args:
        chords: List of (chord_symbol, start_time, duration) tuples
        output_path: Optional path to save figure
        figsize: Figure size
        dpi: Output resolution when saving
    """
    fig, ax = plt.subplots(figsize=figsize)
    draw_chords(ax, chords, fontsize=14)
    ax.set_xlim(0, chords_end_time(chords) * 1.05)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_title('Chord Progression', fontsize=14, fontweight='bold')
    finish_figure(fig, output_path, dpi, 'chord progression')


def draw_chord_tones(
    ax: plt.Axes,
    chords: Sequence[Chord],
    min_pitch: int,
    max_pitch: int,
) -> None:
    """Shade the chord tones of each chord across the visible pitch range."""
    rects = []
    for symbol, start, duration in chords:
        tones = set(chord_pitch_classes(symbol))
        for pitch in range(min_pitch, max_pitch + 1):
            if pitch % 12 in tones:
                rects.append(Rectangle((start, pitch - 0.5), duration, 1.0))
    if rects:
        ax.add_collection(PatchCollection(rects, facecolors='gold', linewidths=0, alpha=0.18))


def overlay_chords_on_pianoroll(
    midi_path: Path,
    chords: List[Chord],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 10),
    dpi: int = DEFAULT_DPI,
) -> None:
    """
    Plot piano roll with chord progression overlay.

    Chord tones are shaded on the piano roll so you can see which melody
    notes sit inside the harmony.

    Args:
        midi_path: Path to MIDI file (melody)
        chords: List of (chord_symbol, start_time, duration) tuples
        output_path: Optional path to save figure
        figsize: Figure size
        dpi: Output resolution when saving
    """
    # Validate every chord before drawing anything
    for symbol, _, _ in chords:
        parse_chord(symbol)

    notes = extract_notes_from_midi(midi_path)

    fig, (ax_chords, ax_piano) = plt.subplots(
        2, 1,
        figsize=figsize,
        gridspec_kw={'height_ratios': [1, 4]},
        sharex=True,
    )

    draw_chords(ax_chords, chords)
    ax_chords.set_title('Chord Progression', fontsize=12, fontweight='bold')

    end_time = chords_end_time(chords)
    if notes:
        notes_end, min_pitch, max_pitch = note_bounds(notes)
        end_time = max(end_time, notes_end)
    else:
        min_pitch, max_pitch = 52, 76  # E3 to E5 by default

    min_pitch, max_pitch = min_pitch - 2, max_pitch + 2
    draw_chord_tones(ax_piano, chords, min_pitch, max_pitch)
    draw_notes(ax_piano, notes)
    style_piano_axes(ax_piano, end_time, min_pitch + 2, max_pitch - 2)
    ax_piano.set_title('Melody (Piano Roll)', fontsize=12, fontweight='bold')
    if notes:
        add_velocity_colorbar(fig, ax_piano)

    finish_figure(fig, output_path, dpi, 'overlay')


# Example: Little Wing chord progression
LITTLE_WING_CHORDS = [
    ('Em', 0.0, 2.0),
    ('G', 2.0, 2.0),
    ('Am', 4.0, 2.0),
    ('Em', 6.0, 2.0),
    ('Bm', 8.0, 1.0),
    ('Bbm', 9.0, 1.0),
    ('Am', 10.0, 1.0),
    ('C', 11.0, 1.0),
    ('G', 12.0, 2.0),
    ('F', 14.0, 1.0),
    ('C', 15.0, 1.0),
    ('D', 16.0, 2.0),
]


if __name__ == '__main__':
    print("Testing chord parsing:")
    for chord_sym in ['Em', 'Gmaj7', 'Am7', 'Bm', 'C', 'D7', 'Bbm7b5']:
        name, notes = parse_chord(chord_sym)
        print(f"{name}: {notes}")
