"""
Chord Progression Overlay

Display chord progressions alongside melodies on piano roll.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from .piano_roll import extract_notes_from_midi


# Common chord definitions (semitones from root)
CHORD_TEMPLATES = {
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    '7': [0, 4, 7, 10],  # Dominant 7
    'min7b5': [0, 3, 6, 10],  # Half-diminished
    'dim': [0, 3, 6],
    'dim7': [0, 3, 6, 9],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
    '6': [0, 4, 7, 9],
    'min6': [0, 3, 7, 9],
    '9': [0, 4, 7, 10, 14],
    'maj9': [0, 4, 7, 11, 14],
}

# MIDI note name mapping
ROOT_NOTES = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11,
}


def parse_chord(chord_symbol: str, octave: int = 4) -> Tuple[str, List[int]]:
    """
    Parse chord symbol into MIDI notes.

    Args:
        chord_symbol: Chord symbol (e.g., 'Em7', 'Gmaj7', 'Am')
        octave: Base octave for chord

    Returns:
        (chord_name, list of MIDI notes)

    Examples:
        >>> parse_chord('Em7', 4)
        ('Em7', [64, 67, 71, 74])  # E, G, B, D
    """
    # Extract root note
    if len(chord_symbol) > 1 and chord_symbol[1] in ('#', 'b'):
        root_str = chord_symbol[:2]
        quality_str = chord_symbol[2:]
    else:
        root_str = chord_symbol[0]
        quality_str = chord_symbol[1:]

    if root_str not in ROOT_NOTES:
        raise ValueError(f"Unknown root note: {root_str}")

    root_pitch_class = ROOT_NOTES[root_str]

    # Determine chord quality
    quality_str = quality_str.lower()

    # Map common abbreviations
    if quality_str == 'm':
        quality = 'minor'
    elif quality_str in ('', 'M'):
        quality = 'major'
    elif quality_str in ('m7', 'min7'):
        quality = 'min7'
    elif quality_str in ('maj7', 'M7'):
        quality = 'maj7'
    elif quality_str == '7':
        quality = '7'
    else:
        quality = quality_str

    if quality not in CHORD_TEMPLATES:
        # Default to major if unknown
        quality = 'major'

    # Build MIDI notes
    intervals = CHORD_TEMPLATES[quality]
    root_midi = octave * 12 + root_pitch_class
    midi_notes = [root_midi + interval for interval in intervals]

    return chord_symbol, midi_notes


def plot_chord_progression(
    chords: List[Tuple[str, float, float]],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 6),
) -> None:
    """
    Plot chord progression as a timeline.

    Args:
        chords: List of (chord_symbol, start_time, duration) tuples
        output_path: Optional path to save figure
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot each chord as a colored block
    colors = plt.cm.Set3(range(len(chords)))

    for i, (chord_symbol, start_time, duration) in enumerate(chords):
        rect = patches.Rectangle(
            (start_time, 0),
            duration,
            1,
            linewidth=2,
            edgecolor='black',
            facecolor=colors[i % len(colors)],
            alpha=0.7,
        )
        ax.add_patch(rect)

        # Add chord label
        ax.text(
            start_time + duration / 2,
            0.5,
            chord_symbol,
            ha='center',
            va='center',
            fontsize=14,
            fontweight='bold',
        )

    # Set axis properties
    ax.set_xlim(0, max(start + dur for _, start, dur in chords) * 1.05)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_title('Chord Progression', fontsize=14, fontweight='bold')
    ax.set_yticks([])
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved chord progression to {output_path}")
    else:
        plt.show()

    plt.close()


def overlay_chords_on_pianoroll(
    midi_path: Path,
    chords: List[Tuple[str, float, float]],
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 10),
) -> None:
    """
    Plot piano roll with chord progression overlay.

    Args:
        midi_path: Path to MIDI file (melody)
        chords: List of (chord_symbol, start_time, duration) tuples
        output_path: Optional path to save figure
        figsize: Figure size
    """
    fig, (ax_chords, ax_piano) = plt.subplots(
        2, 1,
        figsize=figsize,
        gridspec_kw={'height_ratios': [1, 4]},
    )

    # Plot chord progression on top
    colors = plt.cm.Set3(range(len(chords)))
    for i, (chord_symbol, start_time, duration) in enumerate(chords):
        rect = patches.Rectangle(
            (start_time, 0),
            duration,
            1,
            linewidth=2,
            edgecolor='black',
            facecolor=colors[i % len(colors)],
            alpha=0.7,
        )
        ax_chords.add_patch(rect)

        # Add chord label
        ax_chords.text(
            start_time + duration / 2,
            0.5,
            chord_symbol,
            ha='center',
            va='center',
            fontsize=12,
            fontweight='bold',
        )

    ax_chords.set_xlim(0, max(start + dur for _, start, dur in chords) * 1.05)
    ax_chords.set_ylim(0, 1)
    ax_chords.set_title('Chord Progression', fontsize=12, fontweight='bold')
    ax_chords.set_yticks([])
    ax_chords.grid(True, axis='x', alpha=0.3)

    # Plot melody notes on bottom
    notes = extract_notes_from_midi(midi_path)

    for start_time, duration, pitch, velocity in notes:
        color = plt.cm.viridis(velocity / 127.0)
        rect = patches.Rectangle(
            (start_time, pitch - 0.4),
            duration,
            0.8,
            linewidth=1,
            edgecolor='black',
            facecolor=color,
            alpha=0.8,
        )
        ax_piano.add_patch(rect)

    # Highlight chord tones
    for chord_symbol, start_time, duration in chords:
        try:
            _, chord_notes = parse_chord(chord_symbol, octave=4)
            # Highlight chord tones across all octaves
            for octave in range(0, 10):
                for interval in CHORD_TEMPLATES.get('major', [0, 4, 7]):
                    pitch = octave * 12 + (chord_notes[0] % 12) + interval
                    if 0 <= pitch <= 127:
                        rect = patches.Rectangle(
                            (start_time, pitch - 0.5),
                            duration,
                            1.0,
                            linewidth=0,
                            facecolor='yellow',
                            alpha=0.1,
                        )
                        ax_piano.add_patch(rect)
        except:
            pass

    ax_piano.set_xlabel('Time (seconds)', fontsize=12)
    ax_piano.set_ylabel('MIDI Pitch', fontsize=12)
    ax_piano.set_title('Melody (Piano Roll)', fontsize=12, fontweight='bold')

    if notes:
        max_time = max(start + dur for start, dur, _, _ in notes)
        min_pitch = min(pitch for _, _, pitch, _ in notes)
        max_pitch = max(pitch for _, _, pitch, _ in notes)

        ax_piano.set_xlim(0, max_time * 1.05)
        ax_piano.set_ylim(min_pitch - 2, max_pitch + 2)

    ax_piano.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved overlay to {output_path}")
    else:
        plt.show()

    plt.close()


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
    # Demo
    print("Testing chord parsing:")
    for chord_sym in ['Em', 'Gmaj7', 'Am7', 'Bm', 'C', 'D7']:
        name, notes = parse_chord(chord_sym)
        print(f"{name}: {notes}")
