"""
Pipeline Orchestration Module

Coordinates the full hum-to-hendrix processing pipeline.
"""

from .orchestrator import HumToHendrixPipeline
from .config import load_config, Config

__all__ = [
    'HumToHendrixPipeline',
    'load_config',
    'Config',
]

__version__ = '0.1.0'
