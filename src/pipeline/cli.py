"""
Command-line entry points.

These back both the installed console scripts (see setup.py) and the thin
wrappers in scripts/. Each command exits non-zero on failure.
"""

import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import click

from .config import Config, load_config
from .orchestrator import HumToHendrixPipeline

MODELS = ('basic_pitch', 'crepe', 'librosa')
GRIDS = (4, 8, 16, 32)


def _grid_choice():
    return click.Choice([str(g) for g in GRIDS])


@click.command('hum2midi')
@click.argument('audio_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--output', '-o', type=click.Path(dir_okay=False, path_type=Path), help='Output MIDI file')
@click.option('--tempo', '-t', type=int, default=120, show_default=True, help='Tempo in BPM')
@click.option('--model', '-m', type=click.Choice(MODELS), default='basic_pitch', show_default=True,
              help='Pitch detection model')
@click.option('--confidence', '-c', type=float, default=0.5, show_default=True,
              help='Confidence threshold (0-1)')
@click.option('--min-note', type=float, default=0.1, show_default=True,
              help='Minimum note duration in seconds')
def audio_to_midi(audio_file: Path, output: Optional[Path], tempo: int, model: str,
                  confidence: float, min_note: float) -> None:
    """Convert AUDIO_FILE to MIDI without quantization."""
    from audio_to_midi import AudioToMIDIConverter

    output_path = output or audio_file.with_suffix('.mid')

    click.echo(f"Converting {audio_file} to MIDI...")
    click.echo(f"Model: {model}, Confidence: {confidence}, Tempo: {tempo} BPM")

    converter = AudioToMIDIConverter(
        model=model,
        confidence_threshold=confidence,
        min_note_duration=min_note,
    )
    try:
        converter.convert(audio_file, output_path, tempo=tempo)
    except Exception as e:
        raise click.ClickException(f"conversion failed: {e}")

    click.echo(f"✓ Saved MIDI to {output_path}")


@click.command('quantize-midi')
@click.argument('midi_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--output', '-o', type=click.Path(dir_okay=False, path_type=Path), help='Output MIDI file')
@click.option('--scale', '-s', default='minor_pentatonic', show_default=True, help='Scale name')
@click.option('--root', '-r', default='E', show_default=True, help='Root note')
@click.option('--grid', '-g', type=_grid_choice(), help='Timing grid (beat subdivision)')
@click.option('--swing', type=float, default=0.0, show_default=True,
              help='Swing: 0 or 0.5 straight, 0.66 triplet, 0.75 heavy')
@click.option('--pitch-only', is_flag=True, help='Quantize pitch only')
@click.option('--timing-only', is_flag=True, help='Quantize timing only (requires --grid)')
def quantize(midi_file: Path, output: Optional[Path], scale: str, root: str, grid: Optional[str],
             swing: float, pitch_only: bool, timing_only: bool) -> None:
    """Quantize MIDI_FILE pitch to a scale and/or timing to a grid."""
    from quantization import PitchQuantizer, TimingQuantizer

    if pitch_only and timing_only:
        raise click.UsageError("--pitch-only and --timing-only are mutually exclusive")

    do_pitch = not timing_only
    do_timing = not pitch_only and grid is not None
    if not do_pitch and not do_timing:
        raise click.UsageError("--timing-only needs --grid")

    output_path = output or midi_file.parent / f"{midi_file.stem}_quantized.mid"

    try:
        pitch_quantizer = PitchQuantizer(scale_name=scale, root=root) if do_pitch else None
        timing_quantizer = TimingQuantizer(grid_resolution=int(grid), swing=swing) if do_timing else None
    except ValueError as e:
        raise click.BadParameter(str(e))

    if pitch_quantizer and not timing_quantizer:
        click.echo(f"Quantizing pitch to {scale} scale (root: {root})...")
        pitch_quantizer.quantize_midi_file(midi_file, output_path)
    elif timing_quantizer and not pitch_quantizer:
        click.echo(f"Quantizing timing to {grid}th note grid (swing {swing})...")
        timing_quantizer.quantize_midi_file(midi_file, output_path)
    else:
        click.echo(f"Quantizing pitch to {scale} scale (root: {root})...")
        with tempfile.TemporaryDirectory() as tmp_dir:
            intermediate = Path(tmp_dir) / 'pitch_quantized.mid'
            pitch_quantizer.quantize_midi_file(midi_file, intermediate)
            click.echo(f"Quantizing timing to {grid}th note grid (swing {swing})...")
            timing_quantizer.quantize_midi_file(intermediate, output_path)

    click.echo(f"✓ Saved quantized MIDI to {output_path}")


def parse_chord_spec(spec: str) -> List[Tuple[str, float, float]]:
    """
    Parse "Em:0:2,G:2:2,..." into (symbol, start, duration) tuples.

    Raises click.BadParameter on malformed input.
    """
    from visualization import parse_chord

    chords = []
    for item in spec.split(','):
        item = item.strip()
        if not item:
            continue
        parts = item.split(':')
        if len(parts) != 3:
            raise click.BadParameter(f"'{item}' is not SYMBOL:START:DURATION")
        symbol, start, duration = parts
        try:
            parse_chord(symbol)
            chords.append((symbol, float(start), float(duration)))
        except ValueError as e:
            raise click.BadParameter(str(e))
    if not chords:
        raise click.BadParameter("no chords given")
    return chords


@click.command('visualize-midi')
@click.argument('midi_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--output', '-o', type=click.Path(dir_okay=False, path_type=Path), help='Output image file')
@click.option('--compare', '-c', 'original', type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help='Original (pre-quantization) MIDI to show above MIDI_FILE')
@click.option('--chords', type=str, help='Chord progression overlay, e.g. "Em:0:2,G:2:2"')
@click.option('--dpi', type=int, default=150, show_default=True, help='Image resolution')
def visualize(midi_file: Path, output: Optional[Path], original: Optional[Path],
              chords: Optional[str], dpi: int) -> None:
    """
    Visualize MIDI_FILE as a piano roll.

    \b
    Examples:
      visualize-midi solo.mid
      visualize-midi solo_quantized.mid --compare solo_raw.mid
      visualize-midi solo.mid --chords "Em:0:2,G:2:2,Am:4:2"
    """
    from visualization import overlay_chords_on_pianoroll, plot_midi_comparison, plot_piano_roll

    output_path = output or midi_file.with_suffix('.png')

    if original:
        click.echo(f"Comparing {original} (original) with {midi_file} (quantized)...")
        plot_midi_comparison(original, midi_file, output_path, dpi=dpi)
    elif chords:
        chord_list = parse_chord_spec(chords)
        click.echo(f"Visualizing {midi_file} with chord progression...")
        overlay_chords_on_pianoroll(midi_file, chord_list, output_path, dpi=dpi)
    else:
        click.echo(f"Visualizing {midi_file}...")
        plot_piano_roll(midi_file, output_path, dpi=dpi)

    if not output_path.exists():
        raise click.ClickException("nothing was drawn (no notes in file?)")
    click.echo(f"✓ Saved to {output_path}")


@click.command('h2h-pipeline')
@click.argument('audio_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--config', '-c', 'config_path', type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help='Configuration YAML file')
@click.option('--output-dir', '-o', type=click.Path(file_okay=False, path_type=Path), help='Output directory')
@click.option('--model', '-m', type=click.Choice(MODELS), help='Pitch detection model')
@click.option('--scale', '-s', help='Scale for pitch quantization [default: minor_pentatonic]')
@click.option('--root', '-r', help='Root note (e.g., E, A, C#) [default: E]')
@click.option('--tempo', '-t', type=int, help='Tempo in BPM [default: 72]')
@click.option('--grid', '-g', type=_grid_choice(), help='Timing grid [default: 16]')
@click.option('--swing', type=float, help='Swing: 0 or 0.5 straight, 0.66 triplet, 0.75 heavy [default: 0]')
@click.option('--no-visualize', is_flag=True, help='Disable visualization')
def full_pipeline(audio_file: Path, config_path: Optional[Path], output_dir: Optional[Path],
                  model: Optional[str], scale: Optional[str], root: Optional[str],
                  tempo: Optional[int], grid: Optional[str], swing: Optional[float],
                  no_visualize: bool) -> None:
    """
    Convert hummed AUDIO_FILE to quantized MIDI.

    Options given on the command line override the configuration file.

    \b
    Examples:
      h2h-pipeline my_solo.wav
      h2h-pipeline humming.mp3 --scale blues --root A --tempo 120
      h2h-pipeline melody.wav --config config/srv_blues.yaml --grid 16
    """
    config: Config = load_config(config_path) if config_path else Config()

    if model is not None:
        config.conversion.model = model
    if scale is not None:
        config.quantization.pitch.scale = scale
    if root is not None:
        config.quantization.pitch.root = root
    if tempo is not None:
        config.quantization.timing.tempo = tempo
    if grid is not None:
        config.quantization.timing.grid = int(grid)
    if swing is not None:
        config.quantization.timing.swing = swing

    try:
        pipeline = HumToHendrixPipeline(config)
    except ValueError as e:
        raise click.BadParameter(str(e))

    try:
        results = pipeline.process(audio_file, output_dir=output_dir, visualize=not no_visualize)
    except Exception as e:
        raise click.ClickException(f"audio-to-MIDI conversion failed: {e}")

    click.echo("=" * 60)
    click.echo("Generated Files:")
    click.echo("=" * 60)
    for key, path in results.items():
        if isinstance(path, Path) and path.exists():
            click.echo(f"  {key:20s}: {path}")
    click.echo()

    if results['errors']:
        raise click.ClickException("; ".join(results['errors']))
