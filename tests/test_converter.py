"""Tests for the audio-to-MIDI converter."""

import sys
import types
from pathlib import Path

import mido
import numpy as np
import pytest

from audio_to_midi.converter import AudioToMIDIConverter


def _notes_in_seconds(midi_path):
    """Read back (start, duration, note, velocity) in seconds from a MIDI file."""
    mid = mido.MidiFile(str(midi_path))
    now = 0.0
    starts = {}
    notes = []
    for msg in mid:  # iterating a MidiFile yields tempo-aware seconds
        now += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            starts[msg.note] = (now, msg.velocity)
        elif msg.type in ('note_off', 'note_on'):
            start, vel = starts.pop(msg.note)
            notes.append((round(start, 3), round(now - start, 3), msg.note, vel))
    return notes


def test_frequencies_to_midi_vectorised():
    freqs = np.array([440.0, 220.0, 0.0, 261.63, 1.0e6])
    assert AudioToMIDIConverter.frequencies_to_midi(freqs).tolist() == [69, 57, 0, 60, 127]
    assert AudioToMIDIConverter.frequency_to_midi(329.63) == 64
    assert AudioToMIDIConverter.frequency_to_midi(-5) == 0


def test_segment_notes_uses_each_notes_own_confidence():
    conv = AudioToMIDIConverter(min_note_duration=0.1)
    times = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    pitches = np.array([60, 60, 60, 62, 62, 62])
    conf = np.array([0.9, 0.9, 0.9, 0.3, 0.3, 0.3])

    notes = conv.segment_notes(times, pitches, conf)

    assert [(n[2], n[3]) for n in notes] == [(60, 114), (62, 38)]
    assert notes[0][0] == 0.0 and notes[0][1] == pytest.approx(0.3)
    # the final note is kept and extends one frame past its last sample
    assert notes[1][0] == pytest.approx(0.3) and notes[1][1] == pytest.approx(0.3)


def test_segment_notes_splits_on_silence_gap():
    conv = AudioToMIDIConverter(min_note_duration=0.05)
    # same pitch before and after a 0.5 s rest
    times = np.array([0.0, 0.1, 0.2, 0.7, 0.8, 0.9])
    pitches = np.array([64] * 6)
    conf = np.array([0.8] * 6)

    notes = conv.segment_notes(times, pitches, conf)

    assert len(notes) == 2
    assert notes[0][:2] == (0.0, pytest.approx(0.3))
    assert notes[1][:2] == (pytest.approx(0.7), pytest.approx(0.3))


def test_segment_notes_drops_short_notes_and_handles_empty():
    conv = AudioToMIDIConverter(min_note_duration=0.25)
    assert conv.segment_notes(np.array([]), np.array([]), np.array([])) == []
    notes = conv.segment_notes(np.array([0.0, 0.1]), np.array([60, 62]), np.array([1.0, 1.0]))
    assert notes == []


def test_note_events_to_notes_keeps_detector_durations():
    conv = AudioToMIDIConverter(confidence_threshold=0.5, min_note_duration=0.1)
    events = [
        (1.0, 1.5, 67, 0.8),
        (0.0, 0.5, 64, 0.8),   # out of order on purpose
        (2.0, 2.05, 69, 0.9),  # too short
        (3.0, 3.5, 71, 0.2),   # too quiet
    ]
    notes = conv.note_events_to_notes(events)
    assert notes == [(0.0, 0.5, 64, 102), (1.0, 0.5, 67, 102)]


def test_notes_to_midi_roundtrip_respects_tempo(tmp_path):
    conv = AudioToMIDIConverter()
    notes = [(0.0, 0.5, 64, 100), (0.5, 0.5, 64, 90), (1.0, 0.25, 67, 80)]
    out = tmp_path / 'out.mid'
    conv.notes_to_midi(notes, tempo=72).save(str(out))

    assert _notes_in_seconds(out) == [(0.0, 0.5, 64, 100), (0.5, 0.5, 64, 90), (1.0, 0.25, 67, 80)]


def test_unknown_model_rejected():
    with pytest.raises(ValueError):
        AudioToMIDIConverter(model='magic')


def test_basic_pitch_is_called_with_a_path(monkeypatch, tmp_path):
    """Basic Pitch's predict() takes a file path first, then the model."""
    calls = {}

    def fake_predict(audio_path, model_or_model_path, **kwargs):
        calls['audio_path'] = audio_path
        calls['model'] = model_or_model_path
        calls['kwargs'] = kwargs
        assert Path(audio_path).exists()
        return None, None, [(0.1, 0.6, 64, 0.7, []), (0.7, 1.2, 67, 0.6, [])]

    fake_pkg = types.ModuleType('basic_pitch')
    fake_pkg.ICASSP_2022_MODEL_PATH = 'MODEL'
    fake_inf = types.ModuleType('basic_pitch.inference')
    fake_inf.predict = fake_predict
    monkeypatch.setitem(sys.modules, 'basic_pitch', fake_pkg)
    monkeypatch.setitem(sys.modules, 'basic_pitch.inference', fake_inf)

    conv = AudioToMIDIConverter(model='basic_pitch', min_note_duration=0.1, confidence_threshold=0.5)
    audio = np.zeros(22050, dtype=np.float32)
    events = conv.detect_notes(audio, 22050)

    assert isinstance(calls['audio_path'], str)
    assert calls['model'] == 'MODEL'
    assert calls['kwargs']['minimum_note_length'] == pytest.approx(100.0)
    assert events == [(0.1, 0.6, 64, 0.7), (0.7, 1.2, 67, 0.6)]


def _write_tones(path, tones, sr=22050):
    """Write a WAV of (freq, start, duration) sine tones with silence between."""
    import soundfile as sf

    total = max(s + d for _, s, d in tones) + 0.2
    t = np.arange(int(sr * total)) / sr
    sig = np.zeros_like(t)
    for freq, start, dur in tones:
        m = (t >= start) & (t < start + dur)
        sig[m] = 0.5 * np.sin(2 * np.pi * freq * t[m]) * np.hanning(m.sum())
    sf.write(str(path), sig, sr)


def test_convert_with_librosa_fallback_end_to_end(tmp_path):
    pytest.importorskip('librosa')
    wav = tmp_path / 'tones.wav'
    _write_tones(wav, [(220.0, 0.0, 0.6), (329.63, 0.7, 0.6), (440.0, 1.4, 0.6)])

    conv = AudioToMIDIConverter(model='librosa', confidence_threshold=0.5, min_note_duration=0.1)
    conv.convert(wav, tmp_path / 'tones.mid', tempo=72)

    notes = _notes_in_seconds(tmp_path / 'tones.mid')
    assert [n[2] for n in notes] == [57, 64, 69]
    for (start, dur, _, _), (_, exp_start, exp_dur) in zip(notes, [(0, 0.0, 0.6), (0, 0.7, 0.6), (0, 1.4, 0.6)]):
        assert start == pytest.approx(exp_start, abs=0.08)
        assert dur == pytest.approx(exp_dur, abs=0.15)


def test_convert_with_basic_pitch_end_to_end(tmp_path):
    pytest.importorskip('basic_pitch')
    wav = tmp_path / 'tones.wav'
    _write_tones(wav, [(220.0, 0.0, 0.6), (329.63, 0.7, 0.6), (440.0, 1.4, 0.6)])

    conv = AudioToMIDIConverter(model='basic_pitch', confidence_threshold=0.3, min_note_duration=0.1)
    conv.convert(wav, tmp_path / 'tones.mid', tempo=72)

    notes = _notes_in_seconds(tmp_path / 'tones.mid')
    assert [n[2] for n in notes] == [57, 64, 69]
    assert notes[2][0] == pytest.approx(1.4, abs=0.1)
