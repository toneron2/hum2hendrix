"""
Pipeline Orchestration Module

Coordinates the full hum-to-hendrix processing pipeline.
"""

from .config import Config, load_config
from .orchestrator import HumToHendrixPipeline

__all__ = [
    'HumToHendrixPipeline',
    'load_config',
    'Config',
]

__version__ = '0.2.0'
