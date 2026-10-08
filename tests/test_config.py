"""Tests for configuration loading."""

import warnings
from pathlib import Path

import pytest
import yaml

from pipeline.config import Config, load_config, save_config

CONFIG_DIR = Path(__file__).resolve().parent.parent / 'config'


@pytest.mark.parametrize('name', ['default.yaml', 'little_wing.yaml', 'srv_blues.yaml'])
def test_shipped_configs_load_without_warnings(name):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        cfg = load_config(CONFIG_DIR / name)
    assert cfg.quantization.pitch.scale in ('minor_pentatonic', 'blues')


def test_unknown_keys_are_ignored_with_a_warning():
    data = {'quantization': {'pitch': {'scale': 'blues', 'octave': 3}}}
    with pytest.warns(UserWarning, match='octave'):
        cfg = Config.from_dict(data)
    assert cfg.quantization.pitch.scale == 'blues'
    assert cfg.quantization.timing.grid == 16


def test_empty_and_missing_config():
    assert Config.from_dict({}) == Config()
    assert Config.from_dict(None) == Config()
    assert load_config(None) == Config()
    assert load_config(Path('/nonexistent.yaml')) == Config()


def test_round_trip_through_yaml(tmp_path):
    cfg = Config()
    cfg.quantization.timing.swing = 0.66
    cfg.conversion.model = 'librosa'
    out = tmp_path / 'c.yaml'
    save_config(cfg, out)
    assert load_config(out) == cfg
    assert yaml.safe_load(out.read_text())['quantization']['timing']['swing'] == 0.66
