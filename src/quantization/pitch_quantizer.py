"""
Pitch Quantization

Snap MIDI notes to specified musical scales.
"""

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from pathlib import Path
from typing import List, Optional
from .scales import get_scale, find_nearest_scale_note, SCALES


class PitchQuantizer:
    """
    Quantizes MIDI note pitches to a specified musical scale.

    Useful for correcting hummed melodies that may be slightly out of tune
    or for constraining improvisations to specific scales.
    """

    def __init__(
        self,
        scale_notes: Optional[List[int]] = None,
        scale_name: Optional[str] = None,
        root: str = 'E',
        octave: int = 4,
    ):
        """
        Initialize pitch quantizer.

        Args:
            scale_notes: Explicit list of MIDI notes to quantize to
            scale_name: Name of scale (e.g., 'minor_pentatonic', 'blues')
            root: Root note (e.g., 'E', 'A', 'C#')
            octave: Base octave for scale
        """
        if scale_notes is not None:
            self.scale_notes = sorted(scale_notes)
        elif scale_name is not None:
            self.scale_notes = get_scale(scale_name, root, octave)
        else:
            # Default: E minor pentatonic
            self.scale_notes = get_scale('minor_pentatonic', 'E', 4)

    def quantize_note(self, midi_note: int) -> int:
        """
        Quantize a single MIDI note to the nearest scale note.

        Args:
            midi_note: Original MIDI note number

        Returns:
            Quantized MIDI note number
        """
        return find_nearest_scale_note(midi_note, self.scale_notes)

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
        # Load MIDI file
        mid = MidiFile(input_path)

        # Create new MIDI file with same settings
        new_mid = MidiFile(type=mid.type, ticks_per_beat=mid.ticks_per_beat)

        # Process each track
        for track in mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            for msg in track:
                if msg.type in ('note_on', 'note_off'):
                    # Quantize pitch
                    new_note = self.quantize_note(msg.note)
                    new_msg = msg.copy(note=new_note)
                    new_track.append(new_msg)
                else:
                    # Copy non-note messages as-is
                    new_track.append(msg.copy())

        # Save
        new_mid.save(output_path)

        return new_mid


def quantize_pitch_to_scale(
    input_midi: Path,
    output_midi: Path,
    scale_name: str = 'minor_pentatonic',
    root: str = 'E',
    octave: int = 4,
) -> None:
    """
    Convenience function to quantize MIDI file to a scale.

    Args:
        input_midi: Input MIDI file path
        output_midi: Output MIDI file path
        scale_name: Scale name (e.g., 'minor_pentatonic', 'blues')
        root: Root note (e.g., 'E', 'A')
        octave: Base octave
    """
    quantizer = PitchQuantizer(scale_name=scale_name, root=root, octave=octave)
    quantizer.quantize_midi_file(input_midi, output_midi)


if __name__ == '__main__':
    # Demo
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
