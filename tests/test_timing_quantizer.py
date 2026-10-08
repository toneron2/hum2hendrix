"""Tests for timing quantization."""

import mido
import pytest

from quantization import TimingQuantizer

TPB = 480  # ticks per beat; an 8th-note grid unit is 240 ticks


@pytest.mark.parametrize('swing', [0.0, 0.5])
def test_straight_eighths_snap_to_nearest_grid(swing):
    q = TimingQuantizer(grid_resolution=8, swing=swing)
    assert q.quantize_to_grid(0, TPB) == 0
    assert q.quantize_to_grid(230, TPB) == 240
    assert q.quantize_to_grid(250, TPB) == 240
    assert q.quantize_to_grid(480, TPB) == 480
    assert q.quantize_to_grid(700, TPB) == 720
    assert q.quantize_to_grid(120, TPB) == 0     # tie -> earlier


def test_triplet_swing_delays_offbeats_only():
    q = TimingQuantizer(grid_resolution=8, swing=0.66)
    swung_offbeat = round(0.66 * 2 * 240)  # 317 ticks into the pair
    assert q.quantize_to_grid(0, TPB) == 0
    assert q.quantize_to_grid(480, TPB) == 480          # downbeats unchanged
    assert q.quantize_to_grid(240, TPB) == swung_offbeat  # the "and" of 1 is swung, not pushed to beat 2
    assert q.quantize_to_grid(230, TPB) == swung_offbeat
    assert q.quantize_to_grid(330, TPB) == swung_offbeat
    assert q.quantize_to_grid(700, TPB) == 480 + swung_offbeat
    assert q.quantize_to_grid(420, TPB) == 480           # closer to beat 2 than to the swung offbeat


def test_grid_positions_sequence():
    q = TimingQuantizer(grid_resolution=8, swing=0.75)
    assert q.grid_positions(TPB, 960) == [0, 360, 480, 840, 960]


def test_sixteenth_grid_and_invalid_resolution():
    q = TimingQuantizer(grid_resolution=16)
    assert q.quantize_to_grid(130, TPB) == 120
    with pytest.raises(ValueError):
        TimingQuantizer(grid_resolution=0)


def _midi_with(events, tpb=TPB):
    """events: list of (abs_tick, type, note, velocity)."""
    mid = mido.MidiFile(ticks_per_beat=tpb)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=500000))
    last = 0
    for tick, kind, note, vel in sorted(events, key=lambda e: e[0]):
        track.append(mido.Message(kind, note=note, velocity=vel, time=tick - last))
        last = tick
    return mid


def _abs_notes(path):
    mid = mido.MidiFile(str(path))
    now = 0
    out = []
    for msg in mid.tracks[0]:
        now += msg.time
        if msg.type in ('note_on', 'note_off'):
            out.append((now, msg.type, msg.note))
    return out


def test_quantize_midi_file_moves_onsets_and_offsets(tmp_path):
    src = tmp_path / 'in.mid'
    _midi_with([(10, 'note_on', 60, 100), (250, 'note_off', 60, 0),
                (470, 'note_on', 62, 100), (730, 'note_off', 62, 0)]).save(str(src))
    out = tmp_path / 'out.mid'
    TimingQuantizer(grid_resolution=8).quantize_midi_file(src, out)
    assert _abs_notes(out) == [(0, 'note_on', 60), (240, 'note_off', 60),
                               (480, 'note_on', 62), (720, 'note_off', 62)]


def test_short_note_lasts_one_grid_step(tmp_path):
    src = tmp_path / 'in.mid'
    # a 20-tick note starting just before a grid line: both ends snap to 240
    _midi_with([(230, 'note_on', 60, 100), (250, 'note_off', 60, 0)]).save(str(src))
    out = tmp_path / 'out.mid'
    TimingQuantizer(grid_resolution=8).quantize_midi_file(src, out)
    assert _abs_notes(out) == [(240, 'note_on', 60), (480, 'note_off', 60)]
    # with triplet swing the next position after a downbeat is the swung offbeat
    TimingQuantizer(grid_resolution=8, swing=0.66).quantize_midi_file(src, out)
    assert _abs_notes(out) == [(317, 'note_on', 60), (480, 'note_off', 60)]


def test_quantize_duration_option(tmp_path):
    src = tmp_path / 'in.mid'
    _midi_with([(0, 'note_on', 60, 100), (300, 'note_off', 60, 0)]).save(str(src))
    out = tmp_path / 'out.mid'
    TimingQuantizer(grid_resolution=8, quantize_duration=True).quantize_midi_file(src, out)
    assert _abs_notes(out) == [(0, 'note_on', 60), (240, 'note_off', 60)]


def test_overlapping_repeats_of_one_pitch_pair_in_order(tmp_path):
    src = tmp_path / 'in.mid'
    _midi_with([(0, 'note_on', 60, 100), (470, 'note_on', 60, 100),
                (490, 'note_off', 60, 0), (960, 'note_off', 60, 0)]).save(str(src))
    out = tmp_path / 'out.mid'
    TimingQuantizer(grid_resolution=8).quantize_midi_file(src, out)
    assert _abs_notes(out) == [(0, 'note_on', 60), (480, 'note_off', 60),
                               (480, 'note_on', 60), (960, 'note_off', 60)]
