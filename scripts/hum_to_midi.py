#!/usr/bin/env python3
"""
Audio to MIDI Converter CLI

Convert audio file to MIDI without quantization.
"""

import click
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audio_to_midi import AudioToMIDIConverter


@click.command()
@click.argument('audio_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output MIDI file')
@click.option('--tempo', '-t', type=int, default=120, help='Tempo in BPM')
@click.option('--model', '-m', default='basic_pitch', help='Model (basic_pitch, crepe)')
@click.option('--confidence', '-c', type=float, default=0.5, help='Confidence threshold (0-1)')
def main(audio_file, output, tempo, model, confidence):
    """Convert audio file to MIDI."""
    audio_path = Path(audio_file)

    if output:
        output_path = Path(output)
    else:
        output_path = audio_path.with_suffix('.mid')

    print(f"Converting {audio_path} to MIDI...")
    print(f"Model: {model}, Confidence: {confidence}, Tempo: {tempo} BPM")

    converter = AudioToMIDIConverter(
        model=model,
        confidence_threshold=confidence,
    )

    converter.convert(audio_path, output_path, tempo=tempo)

    print(f"✓ Saved MIDI to {output_path}")


if __name__ == '__main__':
    main()
