#!/usr/bin/env python3
"""
MIDI Visualization CLI

Generate piano roll and chord overlay visualizations.
"""

import click
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from visualization import plot_piano_roll, plot_midi_comparison, overlay_chords_on_pianoroll


@click.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output image file')
@click.option('--compare', '-c', type=click.Path(exists=True), help='Compare with another MIDI file')
@click.option('--chords', type=str, help='Chord progression (format: Em:0:2,G:2:2,...)')
def main(midi_file, output, compare, chords):
    """
    Visualize MIDI file as piano roll.

    Examples:

        visualize_midi solo.mid

        visualize_midi solo.mid --compare solo_original.mid

        visualize_midi solo.mid --chords "Em:0:2,G:2:2,Am:4:2"
    """
    midi_path = Path(midi_file)

    if output:
        output_path = Path(output)
    else:
        output_path = midi_path.with_suffix('.png')

    if compare:
        # Comparison mode
        print(f"Comparing {midi_path} with {compare}...")
        plot_midi_comparison(midi_path, Path(compare), output_path)
        print(f"✓ Saved comparison to {output_path}")

    elif chords:
        # Chord overlay mode
        print(f"Visualizing {midi_path} with chord progression...")

        # Parse chord string: "Em:0:2,G:2:2,Am:4:2"
        chord_list = []
        for chord_spec in chords.split(','):
            parts = chord_spec.strip().split(':')
            if len(parts) == 3:
                symbol, start, duration = parts
                chord_list.append((symbol, float(start), float(duration)))

        overlay_chords_on_pianoroll(midi_path, chord_list, output_path)
        print(f"✓ Saved visualization to {output_path}")

    else:
        # Simple piano roll
        print(f"Visualizing {midi_path}...")
        plot_piano_roll(midi_path, output_path)
        print(f"✓ Saved piano roll to {output_path}")


if __name__ == '__main__':
    main()
