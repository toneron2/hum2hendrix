"""Tests for pitch quantization."""

import mido
import pytest

from quantization import PitchQuantizer


def test_quantizes_to_nearest_scale_note_tie_lower():
    q = PitchQuantizer(scale_name='minor_pentatonic', root='E')
    assert q.quantize_note(64) == 64   # E stays
    assert q.quantize_note(63) == 62   # D# is equidistant from D and E: lower wins
    assert q.quantize_note(65) == 64   # F -> E
    assert q.quantize_note(66) == 67   # F# -> G
    assert q.quantize_note(73) == 74   # C# -> D


def test_same_result_in_every_octave():
    q = PitchQuantizer(scale_name='blues', root='A')
    for note in range(12, 116):
        assert q.quantize_note(note + 12) == q.quantize_note(note) + 12


def test_custom_scale_notes_apply_to_every_octave():
    q = PitchQuantizer(scale_notes=[64, 67, 69, 71, 74])  # E minor pentatonic
    assert q.quantize_note(41) == 40   # F2 -> E2, far below the listed notes
    assert q.quantize_note(101) == 100  # F7 -> E7


def test_stays_within_midi_range():
    q = PitchQuantizer(scale_notes=[0])  # C only
    assert q.quantize_note(127) == 120
    assert q.quantize_note(5) == 0
    assert q.quantize_note(7) == 12


def test_quantize_midi_file_rewrites_note_messages(tmp_path):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=500000))
    track.append(mido.Message('note_on', note=65, velocity=90, time=0))
    track.append(mido.Message('note_off', note=65, velocity=0, time=120))
    track.append(mido.Message('control_change', control=7, value=100, time=0))
    src = tmp_path / 'in.mid'
    mid.save(str(src))

    out = tmp_path / 'out.mid'
    PitchQuantizer(scale_name='minor_pentatonic', root='E').quantize_midi_file(src, out)

    msgs = list(mido.MidiFile(str(out)).tracks[0])
    notes = [(m.type, m.note, m.time) for m in msgs if m.type in ('note_on', 'note_off')]
    assert notes == [('note_on', 64, 0), ('note_off', 64, 120)]
    assert any(m.type == 'control_change' for m in msgs)


def test_default_is_e_minor_pentatonic():
    assert sorted(PitchQuantizer().pitch_classes) == [2, 4, 7, 9, 11]


def test_unknown_scale_rejected():
    with pytest.raises(ValueError):
        PitchQuantizer(scale_name='nope')
