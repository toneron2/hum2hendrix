"""Tests for the pipeline orchestrator's error handling."""

import pytest

from pipeline import Config, HumToHendrixPipeline


class _FailingConverter:
    def convert(self, *args, **kwargs):
        raise RuntimeError("boom")


class _StubConverter:
    def convert(self, audio_path, output_path, tempo=120):
        import mido
        mido.MidiFile().save(str(output_path))


def test_audio_to_midi_failure_raises(tmp_path):
    pipeline = HumToHendrixPipeline(Config())
    pipeline.audio_to_midi = _FailingConverter()
    with pytest.raises(RuntimeError):
        pipeline.process(tmp_path / 'x.wav', output_dir=tmp_path, visualize=False)


def test_later_stage_failure_is_recorded_and_falls_back(tmp_path):
    cfg = Config()
    pipeline = HumToHendrixPipeline(cfg)
    pipeline.audio_to_midi = _StubConverter()

    class _BrokenTiming:
        def quantize_midi_file(self, *a, **k):
            raise ValueError("bad grid")

    pipeline.timing_quantizer = _BrokenTiming()
    results = pipeline.process(tmp_path / 'x.wav', output_dir=tmp_path, visualize=False)

    assert results['errors'] == ['timing quantization: bad grid']
    assert results['final_midi'] == tmp_path / 'x_pitch_quantized.mid'
    assert results['final_midi'].exists()


def test_disabled_stages(tmp_path):
    cfg = Config()
    cfg.quantization.pitch.enabled = False
    cfg.quantization.timing.enabled = False
    pipeline = HumToHendrixPipeline(cfg)
    pipeline.audio_to_midi = _StubConverter()
    results = pipeline.process(tmp_path / 'x.wav', output_dir=tmp_path, visualize=False)
    assert results['errors'] == []
    assert results['final_midi'] == tmp_path / 'x_raw.mid'
    assert pipeline.pitch_quantizer is None and pipeline.timing_quantizer is None
