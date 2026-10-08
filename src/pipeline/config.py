"""
Configuration Management

Load and validate pipeline configuration.
"""

import warnings
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import yaml

T = TypeVar('T')


def _build(cls: Type[T], values: Optional[Dict[str, Any]], section: str) -> T:
    """Instantiate a config dataclass, warning about (and ignoring) unknown keys."""
    values = dict(values or {})
    known = {f.name for f in fields(cls)}
    unknown = sorted(set(values) - known)
    if unknown:
        warnings.warn(f"Ignoring unknown config keys in '{section}': {', '.join(unknown)}")
    return cls(**{k: v for k, v in values.items() if k in known})


@dataclass
class AudioInputConfig:
    """Audio input settings."""
    sample_rate: int = 22050
    normalize: bool = True


@dataclass
class ConversionConfig:
    """Audio-to-MIDI conversion settings."""
    model: str = 'basic_pitch'  # or 'crepe'
    confidence_threshold: float = 0.5
    min_note_duration: float = 0.1  # seconds
    onset_threshold: float = 0.5


@dataclass
class PitchQuantizationConfig:
    """Pitch quantization settings."""
    enabled: bool = True
    scale: str = 'minor_pentatonic'
    root: str = 'E'


@dataclass
class TimingQuantizationConfig:
    """Timing quantization settings."""
    enabled: bool = True
    grid: int = 16  # sixteenth notes
    tempo: int = 72  # BPM
    swing: float = 0.0  # 0 or 0.5 = straight, 0.66 = triplet, 0.75 = heavy


@dataclass
class QuantizationConfig:
    """Combined quantization settings."""
    pitch: PitchQuantizationConfig = field(default_factory=PitchQuantizationConfig)
    timing: TimingQuantizationConfig = field(default_factory=TimingQuantizationConfig)


@dataclass
class SynthesisConfig:
    """Audio synthesis settings."""
    mode: str = 'midi_export'  # or 'audio_render'
    instrument: str = 'stratocaster'
    amp_model: str = 'fender_twin'


@dataclass
class OutputConfig:
    """Output settings."""
    directory: str = './output'
    format: str = 'wav'
    bit_depth: int = 24
    sample_rate: int = 44100


@dataclass
class Config:
    """Complete pipeline configuration."""
    audio_input: AudioInputConfig = field(default_factory=AudioInputConfig)
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    quantization: QuantizationConfig = field(default_factory=QuantizationConfig)
    synthesis: SynthesisConfig = field(default_factory=SynthesisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Load configuration from dictionary."""
        config_dict = config_dict or {}
        quant = config_dict.get('quantization') or {}
        return cls(
            audio_input=_build(AudioInputConfig, config_dict.get('audio_input'), 'audio_input'),
            conversion=_build(ConversionConfig, config_dict.get('conversion'), 'conversion'),
            quantization=QuantizationConfig(
                pitch=_build(PitchQuantizationConfig, quant.get('pitch'), 'quantization.pitch'),
                timing=_build(TimingQuantizationConfig, quant.get('timing'), 'quantization.timing'),
            ),
            synthesis=_build(SynthesisConfig, config_dict.get('synthesis'), 'synthesis'),
            output=_build(OutputConfig, config_dict.get('output'), 'output'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'audio_input': {
                'sample_rate': self.audio_input.sample_rate,
                'normalize': self.audio_input.normalize,
            },
            'conversion': {
                'model': self.conversion.model,
                'confidence_threshold': self.conversion.confidence_threshold,
                'min_note_duration': self.conversion.min_note_duration,
                'onset_threshold': self.conversion.onset_threshold,
            },
            'quantization': {
                'pitch': {
                    'enabled': self.quantization.pitch.enabled,
                    'scale': self.quantization.pitch.scale,
                    'root': self.quantization.pitch.root,
                },
                'timing': {
                    'enabled': self.quantization.timing.enabled,
                    'grid': self.quantization.timing.grid,
                    'tempo': self.quantization.timing.tempo,
                    'swing': self.quantization.timing.swing,
                },
            },
            'synthesis': {
                'mode': self.synthesis.mode,
                'instrument': self.synthesis.instrument,
                'amp_model': self.synthesis.amp_model,
            },
            'output': {
                'directory': self.output.directory,
                'format': self.output.format,
                'bit_depth': self.output.bit_depth,
                'sample_rate': self.output.sample_rate,
            },
        }


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to YAML config file (optional)

    Returns:
        Config object
    """
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return Config.from_dict(config_dict)
    else:
        # Return default config
        return Config()


def save_config(config: Config, output_path: Path) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Config object
        output_path: Path to save YAML file
    """
    with open(output_path, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)
