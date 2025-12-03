"""
Hum-to-Hendrix Pipeline Setup
Convert hummed melodies to Hendrix-style guitar solos
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hum2hendrix",
    version="0.1.0",
    author="Home Lab Projects",
    description="Convert hummed melodies into guitar solos with automatic pitch/timing correction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hum2hendrix",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Musicians",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "mido>=1.3.0",
        "python-rtmidi>=1.5.0",
        "music21>=9.1.0",
        "basic-pitch>=0.3.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "gpu": [
            "tensorflow>=2.13.0",
        ],
        "vst": [
            "pedalboard>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hum2midi=pipeline.cli:audio_to_midi",
            "quantize-midi=pipeline.cli:quantize",
            "visualize-midi=pipeline.cli:visualize",
            "h2h-pipeline=pipeline.cli:full_pipeline",
        ],
    },
)
