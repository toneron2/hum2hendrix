"""
Piano Roll Visualization

Display MIDI data as piano roll (time vs pitch grid).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import mido
from mido import MidiFile
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np


def extract_notes_from_midi(midi_path: Path) -> List[Tuple[float, float, int, int]]:
    """
    Extract note events from MIDI file.

    Args:
        midi_path: Path to MIDI file

    Returns:
        List of (start_time, duration, pitch, velocity) tuples
    """
    mid = MidiFile(midi_path)
    notes = []
    note_ons = {}  # Track active notes

    current_time = 0.0

    for track in mid.tracks:
        track_time = 0.0

        for msg in track:
            track_time += mido.tick2second(msg.time, mid.ticks_per_beat, 500000)

            if msg.type == 'set_tempo':
                # Update tempo (affects tick2second conversion)
                pass

            elif msg.type == 'note_on' and msg.velocity > 0:
                # Note on
                key = (msg.channel, msg.note)
                note_ons[key] = (track_time, msg.velocity)

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Note off
                key = (msg.channel, msg.note)
                if key in note_ons:
                    start_time, velocity = note_ons[key]
                    duration = track_time - start_time
                    notes.append((start_time, duration, msg.note, velocity))
                    del note_ons[key]

    return sorted(notes, key=lambda x: x[0])


def plot_piano_roll(
    midi_path: Path,
    output_path: Optional[Path] = None,
    title: str = "Piano Roll",
    figsize: Tuple[int, int] = (14, 8),
    show_velocity: bool = True,
) -> None:
    """
    Plot MIDI file as piano roll.

    Args:
        midi_path: Path to MIDI file
        output_path: Optional path to save figure
        title: Plot title
        figsize: Figure size (width, height)
        show_velocity: Whether to color by velocity
    """
    notes = extract_notes_from_midi(midi_path)

    if not notes:
        print("No notes found in MIDI file")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot each note as a rectangle
    for start_time, duration, pitch, velocity in notes:
        if show_velocity:
            # Color by velocity (dynamics)
            color = plt.cm.viridis(velocity / 127.0)
        else:
            color = 'steelblue'

        rect = patches.Rectangle(
            (start_time, pitch - 0.4),
            duration,
            0.8,
            linewidth=1,
            edgecolor='black',
            facecolor=color,
            alpha=0.8,
        )
        ax.add_patch(rect)

    # Set axis labels and title
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('MIDI Pitch', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Set axis limits
    if notes:
        max_time = max(start + dur for start, dur, _, _ in notes)
        min_pitch = min(pitch for _, _, pitch, _ in notes)
        max_pitch = max(pitch for _, _, pitch, _ in notes)

        ax.set_xlim(0, max_time * 1.05)
        ax.set_ylim(min_pitch - 2, max_pitch + 2)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add note names to y-axis
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    if notes:
        y_ticks = range(int(min_pitch), int(max_pitch) + 1)
        y_labels = [f"{note_names[p % 12]}{p // 12 - 1}" for p in y_ticks]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, fontsize=8)

    # Add colorbar for velocity if shown
    if show_velocity:
        sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=0, vmax=127))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Velocity', fontsize=10)

    plt.tight_layout()

    # Save or show
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved piano roll to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_midi_comparison(
    original_path: Path,
    quantized_path: Path,
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (14, 12),
) -> None:
    """
    Plot before/after comparison of MIDI quantization.

    Args:
        original_path: Path to original MIDI file
        quantized_path: Path to quantized MIDI file
        output_path: Optional path to save figure
        figsize: Figure size (width, height)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)

    # Plot original
    notes_original = extract_notes_from_midi(original_path)
    for start_time, duration, pitch, velocity in notes_original:
        rect = patches.Rectangle(
            (start_time, pitch - 0.4),
            duration,
            0.8,
            linewidth=1,
            edgecolor='black',
            facecolor='steelblue',
            alpha=0.7,
        )
        ax1.add_patch(rect)

    ax1.set_title('Original (Before Quantization)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('MIDI Pitch', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # Plot quantized
    notes_quantized = extract_notes_from_midi(quantized_path)
    for start_time, duration, pitch, velocity in notes_quantized:
        rect = patches.Rectangle(
            (start_time, pitch - 0.4),
            duration,
            0.8,
            linewidth=1,
            edgecolor='black',
            facecolor='green',
            alpha=0.7,
        )
        ax2.add_patch(rect)

    ax2.set_title('Quantized (After Correction)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=10)
    ax2.set_ylabel('MIDI Pitch', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')

    # Set consistent axis limits
    all_notes = notes_original + notes_quantized
    if all_notes:
        max_time = max(start + dur for start, dur, _, _ in all_notes)
        min_pitch = min(pitch for _, _, pitch, _ in all_notes)
        max_pitch = max(pitch for _, _, pitch, _ in all_notes)

        for ax in [ax1, ax2]:
            ax.set_xlim(0, max_time * 1.05)
            ax.set_ylim(min_pitch - 2, max_pitch + 2)

    plt.tight_layout()

    # Save or show
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved comparison to {output_path}")
    else:
        plt.show()

    plt.close()


if __name__ == '__main__':
    # Demo
    import sys

    if len(sys.argv) < 2:
        print("Usage: python piano_roll.py input.mid [output.png]")
        sys.exit(1)

    midi_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    plot_piano_roll(midi_path, output_path)
