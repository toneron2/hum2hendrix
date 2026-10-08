"""
MIDI Quantization Module

Corrects pitch (snap to scale) and timing (snap to grid) in MIDI files.
"""

from .pitch_quantizer import PitchQuantizer, quantize_pitch_to_scale
from .timing_quantizer import TimingQuantizer, quantize_to_grid
from .scales import SCALES, get_scale

__all__ = [
    'PitchQuantizer',
    'TimingQuantizer',
    'quantize_pitch_to_scale',
    'quantize_to_grid',
    'SCALES',
    'get_scale',
]

__version__ = '0.2.0'
