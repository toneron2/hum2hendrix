"""Tests for the command-line entry points."""

import re
from pathlib import Path

import mido
import pytest
from click.testing import CliRunner

from pipeline import cli

REPO = Path(__file__).resolve().parent.parent


def _midi(path, notes, bpm=120, tpb=480):
    mid = mido.MidiFile(ticks_per_beat=tpb)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    last = 0
    for tick, kind, note in sorted(notes):
        track.append(mido.Message(kind, note=note, velocity=90 if kind == 'note_on' else 0, time=tick - last))
        last = tick
    mid.save(str(path))
    return path


def _abs_notes(path):
    now, out = 0, []
    for msg in mido.MidiFile(str(path)).tracks[0]:
        now += msg.time
        if msg.type in ('note_on', 'note_off'):
            out.append((now, msg.type, msg.note))
    return out


def test_setup_console_scripts_point_at_real_functions():
    text = (REPO / 'setup.py').read_text()
    targets = re.findall(r'"[\w-]+=pipeline\.cli:(\w+)"', text)
    assert len(targets) == 4
    for name in targets:
        assert callable(getattr(cli, name))


def test_quantize_pitch_and_timing(tmp_path):
    src = _midi(tmp_path / 'in.mid', [(10, 'note_on', 65), (250, 'note_off', 65)])
    result = CliRunner().invoke(cli.quantize, [str(src), '--scale', 'minor_pentatonic', '--root', 'E', '--grid', '8'])
    assert result.exit_code == 0, result.output
    out = tmp_path / 'in_quantized.mid'
    assert _abs_notes(out) == [(0, 'note_on', 64), (240, 'note_off', 64)]
    assert not list(tmp_path.glob('*_temp.mid'))


def test_quantize_timing_only_and_usage_errors(tmp_path):
    src = _midi(tmp_path / 'in.mid', [(10, 'note_on', 65), (250, 'note_off', 65)])
    runner = CliRunner()

    ok = runner.invoke(cli.quantize, [str(src), '--timing-only', '--grid', '8', '-o', str(tmp_path / 'o.mid')])
    assert ok.exit_code == 0, ok.output
    assert _abs_notes(tmp_path / 'o.mid') == [(0, 'note_on', 65), (240, 'note_off', 65)]

    assert runner.invoke(cli.quantize, [str(src), '--timing-only']).exit_code == 2
    assert runner.invoke(cli.quantize, [str(src), '--pitch-only', '--timing-only']).exit_code == 2
    bad_scale = runner.invoke(cli.quantize, [str(src), '--scale', 'nope'])
    assert bad_scale.exit_code == 2 and 'Unknown scale' in bad_scale.output


def test_visualize_modes_and_bad_chords(tmp_path):
    a = _midi(tmp_path / 'a.mid', [(0, 'note_on', 64), (480, 'note_off', 64)])
    b = _midi(tmp_path / 'b.mid', [(20, 'note_on', 65), (470, 'note_off', 65)])
    runner = CliRunner()

    r = runner.invoke(cli.visualize, [str(a), '--dpi', '40'])
    assert r.exit_code == 0, r.output
    assert (tmp_path / 'a.png').exists()

    r = runner.invoke(cli.visualize, [str(a), '--compare', str(b), '-o', str(tmp_path / 'c.png'), '--dpi', '40'])
    assert r.exit_code == 0, r.output
    assert 'b.mid (original)' in r.output

    r = runner.invoke(cli.visualize, [str(a), '--chords', 'Em:0:1,G:1:1', '-o', str(tmp_path / 'd.png'), '--dpi', '40'])
    assert r.exit_code == 0, r.output

    r = runner.invoke(cli.visualize, [str(a), '--chords', 'Em:0', '-o', str(tmp_path / 'e.png')])
    assert r.exit_code == 2 and 'SYMBOL:START:DURATION' in r.output
    r = runner.invoke(cli.visualize, [str(a), '--chords', 'Zz:0:1', '-o', str(tmp_path / 'e.png')])
    assert r.exit_code == 2


def test_visualize_empty_file_fails(tmp_path):
    empty = _midi(tmp_path / 'empty.mid', [])
    r = CliRunner().invoke(cli.visualize, [str(empty)])
    assert r.exit_code == 1


def _tones_wav(path, sr=22050):
    import numpy as np
    import soundfile as sf

    t = np.arange(int(sr * 2.2)) / sr
    sig = np.zeros_like(t)
    for freq, start in [(220.0, 0.0), (329.63, 0.7), (440.0, 1.4)]:
        m = (t >= start) & (t < start + 0.6)
        sig[m] = 0.5 * np.sin(2 * np.pi * freq * t[m]) * np.hanning(m.sum())
    sf.write(str(path), sig, sr)
    return path


def test_full_pipeline_cli_overrides_config_and_exits_zero(tmp_path):
    pytest.importorskip('librosa')
    wav = _tones_wav(tmp_path / 'tones.wav')
    out = tmp_path / 'out'
    r = CliRunner().invoke(cli.full_pipeline, [
        str(wav), '--config', str(REPO / 'config' / 'srv_blues.yaml'),
        '--model', 'librosa', '--grid', '16', '--swing', '0', '-o', str(out), '--no-visualize',
    ])
    assert r.exit_code == 0, r.output
    assert (out / 'tones_raw.mid').exists()
    assert (out / 'tones_final.mid').exists()
    assert 'Quantizing timing to 16th' in r.output  # CLI --grid beat the config's 8
    assert 'blues scale' in r.output                # config value kept where not overridden


def test_full_pipeline_cli_reports_bad_option(tmp_path):
    wav = _tones_wav(tmp_path / 'tones.wav')
    r = CliRunner().invoke(cli.full_pipeline, [str(wav), '--scale', 'nope', '--no-visualize'])
    assert r.exit_code == 2 and 'Unknown scale' in r.output


def test_hum_to_midi_cli(tmp_path):
    pytest.importorskip('librosa')
    wav = _tones_wav(tmp_path / 'tones.wav')
    r = CliRunner().invoke(cli.audio_to_midi, [str(wav), '--model', 'librosa', '-o', str(tmp_path / 't.mid')])
    assert r.exit_code == 0, r.output
    assert [n for _, k, n in _abs_notes(tmp_path / 't.mid') if k == 'note_on'] == [57, 64, 69]
