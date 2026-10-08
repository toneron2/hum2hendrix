"""
Pitch Quantization

Snap MIDI notes to specified musical scales.
"""

from pathlib import Path
from typing import Iterable, Optional

from mido import MidiFile, MidiTrack

from .scales import (
    MIDI_MAX,
    MIDI_MIN,
    build_pitch_class_map,
    find_nearest_scale_note,
    get_scale_pitch_classes,
)


class PitchQuantizer:
    """
    Quantizes MIDI note pitches to a specified musical scale.

    Useful for correcting hummed melodies that may be slightly out of tune
    or for constraining improvisations to specific scales.

    Scales repeat every octave, so quantization is a constant-time lookup on
    the note's pitch class.
    """

    def __init__(
        self,
        scale_notes: Optional[Iterable[int]] = None,
        scale_name: Optional[str] = None,
        root: str = 'E',
    ):
        """
        Initialize pitch quantizer.

        Args:
            scale_notes: Explicit MIDI notes (or pitch classes) defining the
                scale. Their pitch classes are used in every octave.
            scale_name: Name of scale (e.g., 'minor_pentatonic', 'blues')
            root: Root note (e.g., 'E', 'A', 'C#')
        """
        if scale_notes is not None:
            pitch_classes = frozenset(int(n) % 12 for n in scale_notes)
        elif scale_name is not None:
            pitch_classes = get_scale_pitch_classes(scale_name, root)
        else:
            # Default: E minor pentatonic
            pitch_classes = get_scale_pitch_classes('minor_pentatonic', 'E')

        self.pitch_classes = pitch_classes
        self._offsets = build_pitch_class_map(pitch_classes)

    @property
    def scale_notes(self):
        """All MIDI notes (0-127) in the scale."""
        return [n for n in range(MIDI_MIN, MIDI_MAX + 1) if n % 12 in self.pitch_classes]

    def quantize_note(self, midi_note: int) -> int:
        """
        Quantize a single MIDI note to the nearest scale note.

        Ties resolve to the lower note.

        Args:
            midi_note: Original MIDI note number

        Returns:
            Quantized MIDI note number
        """
        quantized = midi_note + self._offsets[midi_note % 12]
        if quantized < MIDI_MIN or quantized > MIDI_MAX:
            # Fell off the end of the MIDI range: nearest in-range scale note
            quantized = find_nearest_scale_note(midi_note, self.scale_notes)
        return quantized

    def quantize_midi_file(
        self,
        input_path: Path,
        output_path: Path,
    ) -> MidiFile:
        """
        Quantize all notes in a MIDI file to the scale.

        Args:
            input_path: Input MIDI file path
            output_path: Output MIDI file path

        Returns:
            Quantized MidiFile object
        """
        mid = MidiFile(str(input_path))
        new_mid = MidiFile(type=mid.type, ticks_per_beat=mid.ticks_per_beat)

        for track in mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            for msg in track:
                if msg.type in ('note_on', 'note_off'):
                    new_track.append(msg.copy(note=self.quantize_note(msg.note)))
                else:
                    new_track.append(msg.copy())

        new_mid.save(str(output_path))
        return new_mid


def quantize_pitch_to_scale(
    input_midi: Path,
    output_midi: Path,
    scale_name: str = 'minor_pentatonic',
    root: str = 'E',
) -> None:
    """
    Convenience function to quantize MIDI file to a scale.

    Args:
        input_midi: Input MIDI file path
        output_midi: Output MIDI file path
        scale_name: Scale name (e.g., 'minor_pentatonic', 'blues')
        root: Root note (e.g., 'E', 'A')
    """
    quantizer = PitchQuantizer(scale_name=scale_name, root=root)
    quantizer.quantize_midi_file(input_midi, output_midi)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pitch_quantizer.py input.mid output.mid [scale] [root]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    scale = sys.argv[3] if len(sys.argv) > 3 else 'minor_pentatonic'
    root = sys.argv[4] if len(sys.argv) > 4 else 'E'

    print(f"Quantizing {input_path} to {scale} scale in {root}")
    quantize_pitch_to_scale(input_path, output_path, scale, root)
    print(f"Saved to {output_path}")
