#!/usr/bin/env python3
"""
MIDI Quantization CLI

Quantize pitch and/or timing in MIDI file.
"""

import click
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from quantization import PitchQuantizer, TimingQuantizer


@click.command()
@click.argument('midi_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output MIDI file')
@click.option('--scale', '-s', default='minor_pentatonic', help='Scale name')
@click.option('--root', '-r', default='E', help='Root note')
@click.option('--grid', '-g', type=int, help='Timing grid (4, 8, 16, 32)')
@click.option('--pitch-only', is_flag=True, help='Quantize pitch only')
@click.option('--timing-only', is_flag=True, help='Quantize timing only')
def main(midi_file, output, scale, root, grid, pitch_only, timing_only):
    """Quantize MIDI file pitch and/or timing."""
    midi_path = Path(midi_file)

    if output:
        output_path = Path(output)
    else:
        output_path = midi_path.parent / f"{midi_path.stem}_quantized.mid"

    # Determine what to quantize
    quantize_pitch = not timing_only
    quantize_timing = not pitch_only and grid is not None

    current_file = midi_path

    # Pitch quantization
    if quantize_pitch:
        print(f"Quantizing pitch to {scale} scale (root: {root})...")
        pitch_quantizer = PitchQuantizer(scale_name=scale, root=root)

        if quantize_timing:
            temp_path = midi_path.parent / f"{midi_path.stem}_temp.mid"
            pitch_quantizer.quantize_midi_file(current_file, temp_path)
            current_file = temp_path
            print(f"  ✓ Pitch quantized")
        else:
            pitch_quantizer.quantize_midi_file(current_file, output_path)
            print(f"  ✓ Pitch quantized: {output_path}")
            return

    # Timing quantization
    if quantize_timing:
        print(f"Quantizing timing to {grid}th note grid...")
        timing_quantizer = TimingQuantizer(grid_resolution=grid)
        timing_quantizer.quantize_midi_file(current_file, output_path)
        print(f"  ✓ Timing quantized: {output_path}")

        # Clean up temp file
        if current_file != midi_path:
            current_file.unlink()

    if not quantize_pitch and not quantize_timing:
        print("Nothing to quantize. Specify --scale and/or --grid.")


if __name__ == '__main__':
    main()
