"""
Timing Quantization

Snap MIDI note timings to a rhythmic grid, with optional swing.
"""

from pathlib import Path
from typing import Dict, List, Tuple

from mido import MidiFile, MidiTrack

# Swing values at or below this are treated as straight time.
STRAIGHT_SWING = 0.5
MAX_SWING = 0.9


class TimingQuantizer:
    """
    Quantizes MIDI note timings to a rhythmic grid.

    Corrects timing errors in recorded performances, snapping note onsets
    and offsets to the nearest grid position.

    Swing moves every other grid position (the offbeats) later. The `swing`
    value is where the offbeat lands as a fraction of the two-grid-unit pair:
    0.5 (or 0) is straight, 0.66 is triplet swing, 0.75 is dotted/heavy swing.
    """

    def __init__(
        self,
        grid_resolution: int = 16,  # 16th notes
        swing: float = 0.0,
        quantize_duration: bool = False,
    ):
        """
        Initialize timing quantizer.

        Args:
            grid_resolution: Beat subdivision (4=quarter, 8=eighth, 16=sixteenth)
            swing: Offbeat position within a grid pair. 0 or 0.5 = straight,
                0.66 = triplet swing, 0.75 = heavy swing. Capped at 0.9.
            quantize_duration: Whether to also quantize note durations
        """
        if grid_resolution <= 0:
            raise ValueError("grid_resolution must be positive")
        self.grid_resolution = grid_resolution
        self.swing = min(max(swing, 0.0), MAX_SWING)
        self.quantize_duration = quantize_duration

    def _ticks_per_grid(self, ticks_per_beat: int) -> float:
        return ticks_per_beat * 4 / self.grid_resolution

    def grid_positions(self, ticks_per_beat: int, up_to_tick: int) -> List[int]:
        """
        Grid positions in ticks from 0 up to and including the first one at or
        beyond `up_to_tick`. Useful for drawing grids and for tests.
        """
        positions = []
        pair_index = 0
        while True:
            for pos in self._pair_positions(pair_index, ticks_per_beat):
                positions.append(pos)
                if pos >= up_to_tick:
                    return positions
            pair_index += 1

    def _pair_positions(self, pair_index: int, ticks_per_beat: int) -> Tuple[int, int]:
        """The downbeat and (possibly swung) offbeat of grid pair `pair_index`."""
        pair_len = 2 * self._ticks_per_grid(ticks_per_beat)
        start = pair_index * pair_len
        offbeat_fraction = self.swing if self.swing > STRAIGHT_SWING else STRAIGHT_SWING
        return int(round(start)), int(round(start + offbeat_fraction * pair_len))

    def quantize_to_grid(self, tick: int, ticks_per_beat: int) -> int:
        """
        Quantize a tick value to the nearest grid position (swing aware).

        Ties resolve to the earlier position.

        Args:
            tick: Original tick value
            ticks_per_beat: MIDI ticks per quarter note

        Returns:
            Quantized tick value
        """
        tick = max(0, tick)
        pair_len = 2 * self._ticks_per_grid(ticks_per_beat)
        pair_index = int(tick // pair_len)

        down, off = self._pair_positions(pair_index, ticks_per_beat)
        next_down, _ = self._pair_positions(pair_index + 1, ticks_per_beat)

        candidates = (down, off, next_down)
        return min(candidates, key=lambda pos: (abs(pos - tick), pos))

    def quantize_duration_ticks(self, duration: int, ticks_per_beat: int) -> int:
        """Round a duration to a whole number of grid units (at least one)."""
        ticks_per_grid = self._ticks_per_grid(ticks_per_beat)
        units = max(1, round(duration / ticks_per_grid))
        return int(round(units * ticks_per_grid))

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
        mid = MidiFile(str(input_path))
        ticks_per_beat = mid.ticks_per_beat
        new_mid = MidiFile(type=mid.type, ticks_per_beat=ticks_per_beat)

        for track in mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            # Delta times -> absolute ticks
            events = []
            current_tick = 0
            for msg in track:
                current_tick += msg.time
                events.append((current_tick, msg))

            # Active notes: (channel, note) -> stack of quantized onset ticks,
            # so overlapping repeats of one pitch still pair up correctly.
            active: Dict[Tuple[int, int], List[int]] = {}
            quantized_events = []

            for order, (tick, msg) in enumerate(events):
                if msg.type == 'note_on' and msg.velocity > 0:
                    onset = self.quantize_to_grid(tick, ticks_per_beat)
                    active.setdefault((msg.channel, msg.note), []).append(onset)
                    quantized_events.append((onset, 1, order, msg))

                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if active.get(key):
                        onset = active[key].pop(0)
                        if self.quantize_duration:
                            offset = onset + self.quantize_duration_ticks(tick - onset, ticks_per_beat)
                        else:
                            offset = self.quantize_to_grid(tick, ticks_per_beat)
                        # Note off must come after note on
                        offset = max(offset, onset + 1)
                        quantized_events.append((offset, 0, order, msg))
                    else:
                        # Note off without matching note on: keep as is
                        quantized_events.append((tick, 0, order, msg))

                else:
                    # Non-note event (tempo, control change, meta, ...)
                    quantized_events.append((tick, 0, order, msg))

            # Sort by tick; note offs before note ons at the same tick;
            # original order otherwise.
            quantized_events.sort(key=lambda e: (e[0], e[1], e[2]))

            last_tick = 0
            for tick, _, _, msg in quantized_events:
                new_track.append(msg.copy(time=tick - last_tick))
                last_tick = tick

        new_mid.save(str(output_path))
        return new_mid


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
        swing: 0 or 0.5 = straight, 0.66 = triplet swing, 0.75 = heavy swing
    """
    quantizer = TimingQuantizer(
        grid_resolution=grid_resolution,
        swing=swing,
    )
    quantizer.quantize_midi_file(input_midi, output_midi)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python timing_quantizer.py input.mid output.mid [grid] [swing]")
        print("  grid: 4, 8, 16, or 32 (default: 16)")
        print("  swing: 0.5=straight, 0.66=triplet, 0.75=heavy (default: 0.0)")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    swing = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0

    print(f"Quantizing {input_path} to {grid}th note grid (swing: {swing})")
    quantize_to_grid(input_path, output_path, grid, swing)
    print(f"Saved to {output_path}")
