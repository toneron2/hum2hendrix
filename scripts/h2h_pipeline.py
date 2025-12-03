#!/usr/bin/env python3
"""
Hum-to-Hendrix CLI Tool

Complete pipeline: audio → MIDI → quantization → visualization
"""

import click
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pipeline import HumToHendrixPipeline, load_config


@click.command()
@click.argument('audio_file', type=click.Path(exists=True))
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration YAML file')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--scale', '-s', default='minor_pentatonic', help='Scale for pitch quantization')
@click.option('--root', '-r', default='E', help='Root note (e.g., E, A, C#)')
@click.option('--tempo', '-t', type=int, default=72, help='Tempo in BPM')
@click.option('--grid', '-g', type=int, default=16, help='Timing grid (4, 8, 16, 32)')
@click.option('--no-visualize', is_flag=True, help='Disable visualization')
def main(audio_file, config, output_dir, scale, root, tempo, grid, no_visualize):
    """
    Convert hummed audio to quantized MIDI.

    AUDIO_FILE: Input audio file (WAV, MP3, FLAC)

    Examples:

        h2h_pipeline my_solo.wav

        h2h_pipeline humming.mp3 --scale blues --root A --tempo 120

        h2h_pipeline melody.wav --config my_config.yaml
    """
    audio_path = Path(audio_file)

    # Load configuration
    if config:
        pipeline_config = load_config(Path(config))
    else:
        from pipeline.config import Config, QuantizationConfig, PitchQuantizationConfig, TimingQuantizationConfig

        # Override defaults with CLI args
        pipeline_config = Config()
        pipeline_config.quantization.pitch.scale = scale
        pipeline_config.quantization.pitch.root = root
        pipeline_config.quantization.timing.tempo = tempo
        pipeline_config.quantization.timing.grid = grid

    # Create pipeline
    pipeline = HumToHendrixPipeline(pipeline_config)

    # Run pipeline
    output_path = Path(output_dir) if output_dir else None
    results = pipeline.process(
        audio_path,
        output_dir=output_path,
        visualize=not no_visualize,
    )

    # Print summary
    print("\n" + "="*60)
    print("Generated Files:")
    print("="*60)
    for key, path in results.items():
        if isinstance(path, Path) and path.exists():
            print(f"  {key:20s}: {path}")
    print()


if __name__ == '__main__':
    main()
