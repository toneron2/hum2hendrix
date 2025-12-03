"""
Timing Quantization

Snap MIDI note timings to rhythmic grid.
"""

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np


class TimingQuantizer:
    """
    Quantizes MIDI note timings to a rhythmic grid.

    Corrects timing errors in recorded performances, snapping note onsets
    and offsets to the nearest beat subdivision.
    """

    def __init__(
        self,
        grid_resolution: int = 16,  # 16th notes
        swing: float = 0.0,  # 0-1, where 0.5 = straight, 0.66 = triplet swing
        quantize_duration: bool = False,
    ):
        """
        Initialize timing quantizer.

        Args:
            grid_resolution: Beat subdivision (4=quarter, 8=eighth, 16=sixteenth)
            swing: Swing amount (0=straight, 0.5-0.75=swing)
            quantize_duration: Whether to also quantize note durations
        """
        self.grid_resolution = grid_resolution
        self.swing = swing
        self.quantize_duration = quantize_duration

    def quantize_to_grid(
        self,
        tick: int,
        ticks_per_beat: int,
        is_offbeat: bool = False,
    ) -> int:
        """
        Quantize a tick value to the nearest grid position.

        Args:
            tick: Original tick value
            ticks_per_beat: MIDI ticks per quarter note
            is_offbeat: Whether this is an offbeat (for swing)

        Returns:
            Quantized tick value
        """
        # Calculate ticks per grid unit
        ticks_per_grid = ticks_per_beat * 4 / self.grid_resolution

        # Apply swing to offbeat positions
        if is_offbeat and self.swing > 0:
            # Swing delays offbeat notes
            swing_offset = ticks_per_grid * self.swing
            tick += swing_offset

        # Snap to nearest grid position
        grid_position = round(tick / ticks_per_grid)
        quantized_tick = int(grid_position * ticks_per_grid)

        return max(0, quantized_tick)

    def quantize_midi_file(
        self,
        input_path: Path,
        output_path: Path,
    ) -> MidiFile:
        """
        Quantize all note timings in a MIDI file.

        Args:
            input_path: Input MIDI file path
            output_path: Output MIDI file path

        Returns:
            Quantized MidiFile object
        """
        # Load MIDI file
        mid = MidiFile(input_path)
        ticks_per_beat = mid.ticks_per_beat

        # Create new MIDI file
        new_mid = MidiFile(type=mid.type, ticks_per_beat=ticks_per_beat)

        # Process each track
        for track in mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            # Convert delta times to absolute ticks
            events = []
            current_tick = 0

            for msg in track:
                current_tick += msg.time
                events.append((current_tick, msg))

            # Quantize note events
            note_states = {}  # Track note on/off pairs
            quantized_events = []

            for tick, msg in events:
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Quantize note onset
                    quantized_tick = self.quantize_to_grid(
                        tick,
                        ticks_per_beat,
                        is_offbeat=self._is_offbeat(tick, ticks_per_beat),
                    )
                    note_states[(msg.channel, msg.note)] = quantized_tick
                    quantized_events.append((quantized_tick, msg))

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Quantize note offset
                    key = (msg.channel, msg.note)
                    if key in note_states:
                        onset_tick = note_states[key]

                        if self.quantize_duration:
                            # Quantize duration as well
                            duration = tick - onset_tick
                            quantized_duration = self.quantize_to_grid(
                                duration,
                                ticks_per_beat,
                            )
                            quantized_tick = onset_tick + quantized_duration
                        else:
                            # Just quantize the offset time
                            quantized_tick = self.quantize_to_grid(
                                tick,
                                ticks_per_beat,
                            )

                        # Ensure note off comes after note on
                        quantized_tick = max(quantized_tick, onset_tick + 1)

                        del note_states[key]
                        quantized_events.append((quantized_tick, msg))
                    else:
                        # Note off without matching note on (shouldn't happen)
                        quantized_events.append((tick, msg))

                else:
                    # Non-note event (tempo, control change, etc.)
                    quantized_events.append((tick, msg))

            # Sort by tick
            quantized_events.sort(key=lambda x: x[0])

            # Convert back to delta times
            last_tick = 0
            for tick, msg in quantized_events:
                delta = tick - last_tick
                new_track.append(msg.copy(time=delta))
                last_tick = tick

        # Save
        new_mid.save(output_path)

        return new_mid

    def _is_offbeat(self, tick: int, ticks_per_beat: int) -> bool:
        """
        Determine if a tick position is an offbeat (for swing).

        Args:
            tick: Tick value
            ticks_per_beat: Ticks per quarter note

        Returns:
            True if offbeat position
        """
        ticks_per_grid = ticks_per_beat * 4 / self.grid_resolution
        grid_position = round(tick / ticks_per_grid)

        # Odd grid positions are offbeats (for 8th/16th note grids)
        return grid_position % 2 == 1


def quantize_to_grid(
    input_midi: Path,
    output_midi: Path,
    grid_resolution: int = 16,
    swing: float = 0.0,
) -> None:
    """
    Convenience function to quantize MIDI timing to a grid.

    Args:
        input_midi: Input MIDI file path
        output_midi: Output MIDI file path
        grid_resolution: Beat subdivision (4, 8, 16, 32)
        swing: Swing amount (0-0.75)
    """
    quantizer = TimingQuantizer(
        grid_resolution=grid_resolution,
        swing=swing,
    )
    quantizer.quantize_midi_file(input_midi, output_midi)


if __name__ == '__main__':
    # Demo
    import sys

    if len(sys.argv) < 3:
        print("Usage: python timing_quantizer.py input.mid output.mid [grid] [swing]")
        print("  grid: 4, 8, 16, or 32 (default: 16)")
        print("  swing: 0.0-0.75 (default: 0.0)")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    swing = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0

    print(f"Quantizing {input_path} to {grid}th note grid (swing: {swing})")
    quantize_to_grid(input_path, output_path, grid, swing)
    print(f"Saved to {output_path}")
