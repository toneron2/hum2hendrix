"""Tests for piano roll and chord overlay rendering."""

import mido
import pytest

from visualization import (
    extract_notes_from_midi,
    overlay_chords_on_pianoroll,
    parse_chord,
    plot_chord_progression,
    plot_midi_comparison,
    plot_piano_roll,
)
from visualization.chord_overlay import LITTLE_WING_CHORDS, chord_pitch_classes
from visualization.piano_roll import midi_note_name


def _write_midi(path, bpm, notes, tpb=480):
    """notes: (start_beats, duration_beats, pitch, velocity)."""
    mid = mido.MidiFile(ticks_per_beat=tpb)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    events = []
    for start, dur, pitch, vel in notes:
        events.append((int(start * tpb), 1, 'note_on', pitch, vel))
        events.append((int((start + dur) * tpb), 0, 'note_off', pitch, 0))
    events.sort()
    last = 0
    for tick, _, kind, pitch, vel in events:
        track.append(mido.Message(kind, note=pitch, velocity=vel, time=tick - last))
        last = tick
    mid.save(str(path))
    return path


def test_extract_notes_honours_file_tempo(tmp_path):
    path = _write_midi(tmp_path / 'a.mid', 72, [(0, 1, 64, 100), (1, 1, 67, 90)])
    notes = extract_notes_from_midi(path)
    beat = 60 / 72
    assert [n[2] for n in notes] == [64, 67]
    assert notes[0][0] == pytest.approx(0.0)
    assert notes[0][1] == pytest.approx(beat)
    assert notes[1][0] == pytest.approx(beat)
    assert notes[1][3] == 90


def test_extract_notes_honours_mid_file_tempo_change(tmp_path):
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120)))
    track.append(mido.Message('note_on', note=60, velocity=80, time=0))
    track.append(mido.Message('note_off', note=60, velocity=0, time=480))   # 0.5 s at 120
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(60)))
    track.append(mido.Message('note_on', note=62, velocity=80, time=0))
    track.append(mido.Message('note_off', note=62, velocity=0, time=480))   # 1.0 s at 60
    mid.save(str(tmp_path / 'b.mid'))

    notes = extract_notes_from_midi(tmp_path / 'b.mid')
    assert notes[0][1] == pytest.approx(0.5)
    assert notes[1][0] == pytest.approx(0.5)
    assert notes[1][1] == pytest.approx(1.0)


def test_midi_note_name_uses_c4_equals_60():
    assert midi_note_name(60) == 'C4'
    assert midi_note_name(64) == 'E4'
    assert midi_note_name(40) == 'E2'


@pytest.mark.parametrize('symbol, expected', [
    ('Em', [64, 67, 71]),
    ('EM', [64, 68, 71]),
    ('E', [64, 68, 71]),
    ('Em7', [64, 67, 71, 74]),
    ('Gmaj7', [67, 71, 74, 78]),
    ('GM7', [67, 71, 74, 78]),
    ('Bm7b5', [71, 74, 77, 81]),
    ('Bbm', [70, 73, 77]),
    ('F#dim7', [66, 69, 72, 75]),
    ('Am9', [69, 72, 76, 79, 83]),
    ('Dsus4', [62, 67, 69]),
])
def test_parse_chord(symbol, expected):
    name, notes = parse_chord(symbol)
    assert name == symbol
    assert notes == expected


def test_parse_chord_rejects_unknown_symbols():
    with pytest.raises(ValueError):
        parse_chord('H')
    with pytest.raises(ValueError):
        parse_chord('Cxyz')
    with pytest.raises(ValueError):
        parse_chord('')


def test_chord_pitch_classes_follow_quality():
    assert chord_pitch_classes('Em') == [4, 7, 11]
    assert chord_pitch_classes('E') == [4, 8, 11]


def test_little_wing_chords_all_parse():
    for symbol, _, _ in LITTLE_WING_CHORDS:
        parse_chord(symbol)


def test_plots_write_png_files(tmp_path):
    a = _write_midi(tmp_path / 'a.mid', 72, [(0, 1, 64, 100), (1, 0.5, 65, 60), (2, 1, 67, 120)])
    b = _write_midi(tmp_path / 'b.mid', 72, [(0, 1, 64, 100), (1, 0.5, 64, 60), (2, 1, 67, 120)])

    plot_piano_roll(a, tmp_path / 'roll.png', dpi=50)
    plot_piano_roll(a, tmp_path / 'roll_plain.png', show_velocity=False, dpi=50)
    plot_midi_comparison(a, b, tmp_path / 'cmp.png', dpi=50)
    plot_chord_progression(LITTLE_WING_CHORDS[:4], tmp_path / 'chords.png', dpi=50)
    overlay_chords_on_pianoroll(a, [('Em', 0, 1.5), ('G', 1.5, 1.5)], tmp_path / 'overlay.png', dpi=50)

    for name in ['roll', 'roll_plain', 'cmp', 'chords', 'overlay']:
        assert (tmp_path / f'{name}.png').stat().st_size > 1000


def test_overlay_rejects_bad_chord_before_drawing(tmp_path):
    a = _write_midi(tmp_path / 'a.mid', 120, [(0, 1, 64, 100)])
    with pytest.raises(ValueError):
        overlay_chords_on_pianoroll(a, [('Em', 0, 1), ('Zq', 1, 1)], tmp_path / 'x.png')
    assert not (tmp_path / 'x.png').exists()


def test_empty_midi_piano_roll_does_not_write(tmp_path):
    path = _write_midi(tmp_path / 'empty.mid', 120, [])
    plot_piano_roll(path, tmp_path / 'empty.png')
    assert not (tmp_path / 'empty.png').exists()
