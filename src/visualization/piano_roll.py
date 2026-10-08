"""
Piano Roll Visualization

Display MIDI data as piano roll (time vs pitch grid).
"""

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from mido import MidiFile

# (start_time, duration, pitch, velocity) in seconds
Note = Tuple[float, float, int, int]

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
DEFAULT_DPI = 150


def midi_note_name(pitch: int) -> str:
    """MIDI note number -> name with octave, using C4 = 60."""
    return f"{NOTE_NAMES[pitch % 12]}{pitch // 12 - 1}"


def extract_notes_from_midi(midi_path: Path) -> List[Note]:
    """
    Extract note events from a MIDI file, in seconds.

    Tempo changes anywhere in the file are honoured (mido merges the tracks
    and converts delta ticks to seconds using the running tempo).

    Args:
        midi_path: Path to MIDI file

    Returns:
        List of (start_time, duration, pitch, velocity) tuples sorted by start
    """
    mid = MidiFile(str(midi_path))
    notes: List[Note] = []
    active: Dict[Tuple[int, int], List[Tuple[float, int]]] = {}
    now = 0.0

    for msg in mid:  # yields messages with .time in seconds
        now += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            active.setdefault((msg.channel, msg.note), []).append((now, msg.velocity))

        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if active.get(key):
                start_time, velocity = active[key].pop(0)
                notes.append((start_time, now - start_time, msg.note, velocity))

    return sorted(notes, key=lambda n: (n[0], n[2]))


def draw_notes(
    ax: plt.Axes,
    notes: Sequence[Note],
    color: Optional[str] = None,
    alpha: float = 0.8,
    height: float = 0.8,
) -> None:
    """
    Draw notes as rectangles on `ax` in a single collection.

    Args:
        ax: Target axes
        notes: (start, duration, pitch, velocity) tuples
        color: Fixed colour, or None to colour by velocity (viridis)
        alpha: Opacity
        height: Rectangle height in semitones
    """
    if not notes:
        return

    rects = [
        Rectangle((start, pitch - height / 2), duration, height)
        for start, duration, pitch, _ in notes
    ]
    if color is None:
        facecolors = [plt.cm.viridis(velocity / 127.0) for _, _, _, velocity in notes]
    else:
        facecolors = color

    ax.add_collection(PatchCollection(
        rects,
        facecolors=facecolors,
        edgecolors='black',
        linewidths=0.8,
        alpha=alpha,
    ))


def note_bounds(notes: Sequence[Note]) -> Tuple[float, int, int]:
    """(end_time, min_pitch, max_pitch) over a non-empty note list."""
    end_time = max(start + duration for start, duration, _, _ in notes)
    pitches = [pitch for _, _, pitch, _ in notes]
    return end_time, min(pitches), max(pitches)


def style_piano_axes(
    ax: plt.Axes,
    end_time: float,
    min_pitch: int,
    max_pitch: int,
    xlabel: Optional[str] = 'Time (seconds)',
) -> None:
    """Apply limits, grid and note-name ticks to a piano-roll axes."""
    ax.set_xlim(0, max(end_time, 1e-3) * 1.05)
    ax.set_ylim(min_pitch - 2, max_pitch + 2)

    y_ticks = list(range(int(min_pitch), int(max_pitch) + 1))
    # Keep labels readable on wide ranges
    step = 1 if len(y_ticks) <= 30 else 2 if len(y_ticks) <= 60 else 12
    y_ticks = y_ticks[::step]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([midi_note_name(p) for p in y_ticks], fontsize=8)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel('MIDI Pitch', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')


def add_velocity_colorbar(fig: plt.Figure, ax: plt.Axes) -> None:
    """Attach a viridis velocity colour bar to `ax`."""
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=0, vmax=127))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label('Velocity', fontsize=10)


def finish_figure(fig: plt.Figure, output_path: Optional[Path], dpi: int, what: str) -> None:
    """Save to `output_path` (or show), then close the figure."""
    fig.tight_layout()
    if output_path:
        fig.savefig(str(output_path), dpi=dpi, bbox_inches='tight')
        print(f"Saved {what} to {output_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_piano_roll(
    midi_path: Path,
    output_path: Optional[Path] = None,
    title: str = "Piano Roll",
    figsize: Tuple[int, int] = (14, 8),
    show_velocity: bool = True,
    dpi: int = DEFAULT_DPI,
) -> None:
    """
    Plot MIDI file as piano roll.

    Args:
        midi_path: Path to MIDI file
        output_path: Optional path to save figure
        title: Plot title
        figsize: Figure size (width, height)
        show_velocity: Whether to colour by velocity
        dpi: Output resolution when saving
    """
    notes = extract_notes_from_midi(midi_path)

    if not notes:
        print("No notes found in MIDI file")
        return

    fig, ax = plt.subplots(figsize=figsize)
    draw_notes(ax, notes, color=None if show_velocity else 'steelblue')
    style_piano_axes(ax, *note_bounds(notes))
    ax.set_title(title, fontsize=14, fontweight='bold')

    if show_velocity:
        add_velocity_colorbar(fig, ax)

    finish_figure(fig, output_path, dpi, 'piano roll')


def plot_midi_comparison(
    original_path: Path,
    quantized_path: Path,
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 12),
    dpi: int = DEFAULT_DPI,
) -> None:
    """
    Plot before/after comparison of MIDI quantization.

    Args:
        original_path: Path to original MIDI file
        quantized_path: Path to quantized MIDI file
        output_path: Optional path to save figure
        figsize: Figure size (width, height)
        dpi: Output resolution when saving
    """
    notes_original = extract_notes_from_midi(original_path)
    notes_quantized = extract_notes_from_midi(quantized_path)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    draw_notes(ax1, notes_original, color='steelblue', alpha=0.7)
    ax1.set_title('Original (Before Quantization)', fontsize=12, fontweight='bold')

    draw_notes(ax2, notes_quantized, color='green', alpha=0.7)
    ax2.set_title('Quantized (After Correction)', fontsize=12, fontweight='bold')

    all_notes = notes_original + notes_quantized
    if all_notes:
        end_time, min_pitch, max_pitch = note_bounds(all_notes)
        style_piano_axes(ax1, end_time, min_pitch, max_pitch, xlabel=None)
        style_piano_axes(ax2, end_time, min_pitch, max_pitch)

    finish_figure(fig, output_path, dpi, 'comparison')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python piano_roll.py input.mid [output.png]")
        sys.exit(1)

    plot_piano_roll(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
