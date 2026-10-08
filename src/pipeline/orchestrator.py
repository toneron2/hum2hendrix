"""
Pipeline Orchestrator

Main controller for the hum-to-hendrix processing pipeline.
"""

from pathlib import Path
from typing import Dict, List, Optional

from audio_to_midi import AudioToMIDIConverter
from quantization import PitchQuantizer, TimingQuantizer

from .config import Config, load_config


class HumToHendrixPipeline:
    """
    Complete pipeline orchestrator for hum-to-guitar conversion.

    Coordinates:
    1. Audio input
    2. Audio-to-MIDI conversion
    3. Pitch quantization
    4. Timing quantization
    5. Visualization
    6. Audio rendering (future)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize pipeline with configuration.

        Args:
            config: Configuration object (defaults if None)
        """
        self.config = config or Config()

        self.audio_to_midi = AudioToMIDIConverter(
            model=self.config.conversion.model,
            sample_rate=self.config.audio_input.sample_rate,
            confidence_threshold=self.config.conversion.confidence_threshold,
            min_note_duration=self.config.conversion.min_note_duration,
            onset_threshold=self.config.conversion.onset_threshold,
            normalize=self.config.audio_input.normalize,
        )

        self.pitch_quantizer: Optional[PitchQuantizer] = None
        if self.config.quantization.pitch.enabled:
            self.pitch_quantizer = PitchQuantizer(
                scale_name=self.config.quantization.pitch.scale,
                root=self.config.quantization.pitch.root,
            )

        self.timing_quantizer: Optional[TimingQuantizer] = None
        if self.config.quantization.timing.enabled:
            self.timing_quantizer = TimingQuantizer(
                grid_resolution=self.config.quantization.timing.grid,
                swing=self.config.quantization.timing.swing,
            )

    def process(
        self,
        audio_path: Path,
        output_dir: Optional[Path] = None,
        visualize: bool = True,
    ) -> dict:
        """
        Run complete pipeline on audio file.

        Audio-to-MIDI failure raises, since nothing downstream can run
        without it. Later stages fall back to the previous stage's output and
        record the problem in ``results['errors']`` so callers can report a
        non-zero exit status.

        Args:
            audio_path: Input audio file (hummed melody)
            output_dir: Output directory (uses config default if None)
            visualize: Whether to generate visualization plots

        Returns:
            Dictionary with paths to generated files and an 'errors' list
        """
        audio_path = Path(audio_path)
        if output_dir is None:
            output_dir = Path(self.config.output.directory)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = audio_path.stem
        raw_midi_path = output_dir / f"{stem}_raw.mid"
        pitch_quantized_path = output_dir / f"{stem}_pitch_quantized.mid"
        final_midi_path = output_dir / f"{stem}_final.mid"

        errors: List[str] = []
        results: Dict[str, object] = {
            'input_audio': audio_path,
            'output_dir': output_dir,
            'errors': errors,
        }

        print(f"\n{'=' * 60}")
        print("Hum-to-Hendrix Pipeline")
        print(f"{'=' * 60}\n")
        print(f"Input: {audio_path}")
        print(f"Output Directory: {output_dir}\n")

        # Stage 1: Audio to MIDI (fatal on failure)
        print("[1/5] Converting audio to MIDI...")
        self.audio_to_midi.convert(
            audio_path,
            raw_midi_path,
            tempo=self.config.quantization.timing.tempo,
        )
        results['raw_midi'] = raw_midi_path
        print(f"      ✓ Raw MIDI saved: {raw_midi_path}")
        current_midi = raw_midi_path

        # Stage 2: Pitch Quantization
        if self.pitch_quantizer:
            print(f"[2/5] Quantizing pitch to {self.config.quantization.pitch.scale} scale...")
            try:
                self.pitch_quantizer.quantize_midi_file(current_midi, pitch_quantized_path)
                results['pitch_quantized_midi'] = pitch_quantized_path
                current_midi = pitch_quantized_path
                print(f"      ✓ Pitch quantized: {pitch_quantized_path}")
            except Exception as e:  # keep going with the unquantized file
                errors.append(f"pitch quantization: {e}")
                print(f"      ✗ Error: {e}")
        else:
            print("[2/5] Pitch quantization disabled")

        # Stage 3: Timing Quantization
        if self.timing_quantizer:
            print(f"[3/5] Quantizing timing to {self.config.quantization.timing.grid}th note grid...")
            try:
                self.timing_quantizer.quantize_midi_file(current_midi, final_midi_path)
                current_midi = final_midi_path
                print(f"      ✓ Timing quantized: {final_midi_path}")
            except Exception as e:
                errors.append(f"timing quantization: {e}")
                print(f"      ✗ Error: {e}")
        else:
            print("[3/5] Timing quantization disabled")

        results['final_midi'] = current_midi

        # Stage 4: Visualization
        if visualize:
            print("[4/5] Generating visualizations...")
            try:
                # matplotlib is slow to import; only pay for it when plotting
                from visualization import plot_midi_comparison, plot_piano_roll

                piano_roll_path = output_dir / f"{stem}_pianoroll.png"
                plot_piano_roll(current_midi, piano_roll_path)
                results['piano_roll'] = piano_roll_path
                print(f"      ✓ Piano roll: {piano_roll_path}")

                if current_midi != raw_midi_path:
                    comparison_path = output_dir / f"{stem}_comparison.png"
                    plot_midi_comparison(raw_midi_path, current_midi, comparison_path)
                    results['comparison'] = comparison_path
                    print(f"      ✓ Comparison: {comparison_path}")
            except Exception as e:
                errors.append(f"visualization: {e}")
                print(f"      ✗ Visualization error: {e}")
        else:
            print("[4/5] Visualization disabled")

        # Stage 5: Audio Rendering (future)
        print("[5/5] Audio rendering (not yet implemented)")

        print(f"\n{'=' * 60}")
        print("Pipeline complete!" if not errors else f"Pipeline finished with {len(errors)} error(s)")
        print(f"{'=' * 60}\n")

        return results

    @classmethod
    def from_config_file(cls, config_path: Path) -> 'HumToHendrixPipeline':
        """
        Create pipeline from configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Initialized pipeline
        """
        config = load_config(config_path)
        return cls(config)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py input_audio.wav [config.yaml]")
        sys.exit(1)

    audio_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if config_path:
        pipeline = HumToHendrixPipeline.from_config_file(config_path)
    else:
        pipeline = HumToHendrixPipeline()

    results = pipeline.process(audio_path)

    print("\nGenerated files:")
    for key, path in results.items():
        if isinstance(path, Path):
            print(f"  {key}: {path}")
    sys.exit(1 if results['errors'] else 0)
