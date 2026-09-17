# Hum-to-Hendrix Pipeline

Convert hummed melodies into Hendrix/SRV-style guitar solos with automatic pitch correction, timing quantization, and professional amp simulation.

**Status: The audio-to-MIDI stage is in progress and rendering is not built.**
[Development Status](#development-status) below carries the phases.

A standalone project on this account, separate from the governance architecture.

## Project Overview

This system solves a specific engineering problem: converting musical ideas expressed through humming into rendered guitar performances, bypassing the need for instrumental motor skills. The pipeline handles pitch correction, rhythm quantization, and timbral synthesis to produce authentic electric guitar output.

**Core Principle:** Decouple ideation (humming) from execution (motor skills).

## The Pipeline

```
Input (Humming)
    ↓
Audio-to-MIDI Conversion (Signal Transduction)
    ↓
Quantization Layer (Pitch + Timing Correction)
    ↓
MIDI Processing & Visualization
    ↓
Virtual Instrument Rendering (Guitar)
    ↓
Amp Simulation (Hendrix/SRV Tone)
    ↓
Output (Stratocaster Audio)
```

## Features

- **Audio-to-MIDI Conversion**: Uses deep learning models (Basic Pitch/NeuralNote) to extract pitch and timing from hummed audio
- **Pitch Quantization**: Snap notes to specific scales (E Minor Pentatonic, Blues scales, etc.)
- **Timing Quantization**: Correct rhythm to grid (1/8th, 1/16th notes)
- **Visual MIDI Editor**: Piano roll visualization for surgical note editing
- **Chord Progression Experimentation**: Layer and compare different jazz reharmonizations
- **Professional Guitar Rendering**: Sample-based Stratocaster with articulations
- **Authentic Amp Simulation**: Neural amp modeling (NAM) for Fender Twin/Dumble tones

## Tech Stack

### Core Python Libraries
- `basic-pitch` or `crepe`: Audio-to-MIDI conversion
- `librosa`: Audio analysis and processing
- `mido`: MIDI file manipulation
- `music21`: Music theory and scale quantization
- `numpy`: Numerical operations

### Desktop DAW + VST (Optional Advanced Workflow)
- **DAW**: Reaper (evaluation) or Ardour (FOSS)
- **Audio-to-MIDI**: NeuralNote VST
- **Guitar**: Unreal Instruments Standard Guitar + Plogue Sforzando
- **Amp Sim**: Neural Amp Modeler (NAM) with ToneHunt.org models

### Hybrid Approach (Recommended)
Python CLI for core processing, optional DAW integration for final mixing.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Convert hummed audio to MIDI
python scripts/hum_to_midi.py examples/audio/my_solo.wav --output output/solo.mid

# Quantize to E Minor Pentatonic, 1/16th note grid
python scripts/quantize_midi.py output/solo.mid --scale e_minor_pentatonic --grid 16

# Visualize MIDI
python scripts/visualize_midi.py output/solo_quantized.mid

# Render with guitar tone (requires VST setup)
python scripts/render_audio.py output/solo_quantized.mid --output output/final.wav
```

## Project Structure

```
hum2hendrix/
├── src/                        # Core modules
│   ├── audio_to_midi/          # Audio → MIDI conversion
│   ├── quantization/           # Pitch/timing correction
│   ├── synthesis/              # Audio rendering
│   ├── visualization/          # MIDI/chord visualizers
│   └── pipeline/               # Orchestration logic
├── scripts/                    # CLI entry points
├── config/                     # Configuration files
├── docs/                       # Documentation
│   ├── architecture/           # Technical design docs
│   ├── guides/                 # Setup and usage guides
│   └── examples/               # Workflow examples
├── models/                     # Amp sims and instruments
├── examples/                   # Sample audio/MIDI files
├── tests/                      # Unit tests
├── output/                     # Generated files
└── temp/                       # Temporary processing files
```

## Use Cases

### 1. Solo Development
- Hum an 8-bar solo over a backing track
- Quantize to appropriate scale
- Experiment with different phrasings in MIDI editor
- Export final guitar audio

### 2. Chord Progression Exploration
- Input melody (hummed or MIDI)
- Layer multiple chord progression variants
- Visualize harmonic relationships in piano roll
- Compare reharmonizations (original vs jazz alterations)

### 3. Little Wing Example
- Load Em-G-Am-Em backing track
- Hum solo ideas
- Snap to E minor pentatonic
- Apply Hendrix-style amp tone
- Export final mix

## Documentation

- [Architecture Overview](docs/architecture/PIPELINE.md)
- [Installation Guide](docs/guides/INSTALLATION.md)
- [VST Setup](docs/guides/VST_SETUP.md)
- [Scale Reference](docs/guides/SCALES.md)
- [Amp Tone Guide](docs/guides/AMP_TONES.md)
- [Workflow Examples](docs/examples/)

## Development Status

**Phase 1**: Core Python pipeline (audio → MIDI → quantization) - In Progress
**Phase 2**: Visualization and MIDI editing tools
**Phase 3**: VST integration and rendering
**Phase 4**: Chord progression experimentation
**Phase 5**: Web interface (optional future enhancement)

## Requirements

- Python 3.9+
- Microphone input
- Optional: MIDI keyboard
- Optional: Desktop DAW for advanced mixing

## Contributing

This is a personal project. See [CLAUDE.md](CLAUDE.md) for AI collaboration context.

## License

MIT License - See LICENSE file for details

## References

- [NeuralNote VST](https://github.com/DamRsn/NeuralNote)
- [Spotify Basic Pitch](https://github.com/spotify/basic-pitch)
- [Neural Amp Modeler](https://github.com/sdatkinson/neural-amp-modeler)
- [ToneHunt Models](https://tonehunt.org/)
- [Reaper DAW](https://www.reaper.fm/)
- [Plogue Sforzando](https://www.plogue.com/products/sforzando.html)

## Contact

See [CLAUDE.md](CLAUDE.md) for project context and collaboration notes.
