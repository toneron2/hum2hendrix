# Installation Guide

## System Requirements

- Python 3.9 or higher
- 4GB+ RAM
- 4GB free disk space
- Microphone or audio input device
- Supported OS: Linux, macOS, Windows

## Quick Install (Linux/macOS)

```bash
# Clone repository
git clone https://github.com/yourusername/hum2hendrix.git
cd hum2hendrix

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Verify installation
python -c "import audio_to_midi; print('✓ Installation successful')"
```

## Quick Install (Windows)

```powershell
# Clone repository
git clone https://github.com/yourusername/hum2hendrix.git
cd hum2hendrix

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Verify installation
python -c "import audio_to_midi; print('✓ Installation successful')"
```

## Detailed Installation Steps

### 1. Install Python Dependencies

#### Core Dependencies (Required)

```bash
pip install numpy librosa soundfile mido basic-pitch matplotlib pyyaml click
```

#### GPU Acceleration (Optional)

For faster audio-to-MIDI conversion with GPU:

```bash
pip install tensorflow-gpu  # NVIDIA GPU with CUDA
```

#### Alternative Pitch Detection (Optional)

```bash
pip install crepe  # CREPE pitch detector
```

### 2. Install System Dependencies

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    portaudio19-dev \
    libasound2-dev \
    libflac-dev \
    libsndfile1-dev
```

#### macOS

```bash
brew install portaudio libsndfile flac
```

#### Windows

No additional system dependencies typically required.
Use `pip` to install all Python packages.

### 3. Make Scripts Executable

```bash
chmod +x scripts/*.py
```

Add to PATH (optional):

```bash
export PATH="$PATH:$(pwd)/scripts"
```

## Platform-Specific Notes

### Android/Termux

Running on Android via Termux requires additional steps:

```bash
# Install Termux dependencies
pkg install python python-numpy python-scipy libsndfile portaudio

# Some packages may need special handling
pip install --no-build-isolation librosa

# Note: basic-pitch may not work on ARM without TensorFlow Lite
# Use librosa pitch detection as fallback
```

### Raspberry Pi

```bash
# Install system dependencies
sudo apt-get install python3-numpy python3-scipy

# Install remaining Python packages
pip install librosa basic-pitch mido
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'audio_to_midi'`

**Solution**: Ensure you're in the project root and have activated the virtual environment:

```bash
cd /path/to/hum2hendrix
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
```

### Issue: `ImportError: No module named '_portaudio'`

**Solution**: Install PortAudio system library:

```bash
# Linux
sudo apt-get install portaudio19-dev

# macOS
brew install portaudio

# Then reinstall pyaudio
pip install --force-reinstall pyaudio
```

### Issue: Basic Pitch installation fails

**Solution**: Install TensorFlow first:

```bash
pip install tensorflow>=2.13.0
pip install basic-pitch
```

### Issue: MIDI playback not working

**Solution**: Install MIDI backend:

```bash
# Linux
sudo apt-get install timidity

# macOS
brew install fluidsynth
```

### Issue: Matplotlib displays not showing

**Solution**: Install GUI backend:

```bash
pip install PyQt5  # or
pip install tk
```

## Verifying Installation

Run the test suite:

```bash
pytest tests/
```

Test individual components:

```bash
# Test audio loading
python -c "import librosa; librosa.load('test.wav')"

# Test MIDI writing
python -c "import mido; mido.MidiFile().save('test.mid')"

# Test Basic Pitch
python -c "from basic_pitch.inference import predict; print('✓ Basic Pitch OK')"
```

## Next Steps

After installation:

1. Read [USAGE.md](USAGE.md) for usage examples
2. Try the examples in `examples/`
3. Customize `config/default.yaml` for your preferences
4. See [SCALES.md](SCALES.md) for available scales

## Updating

To update to the latest version:

```bash
cd hum2hendrix
git pull origin main
pip install --upgrade -r requirements.txt
```

## Uninstalling

```bash
pip uninstall hum2hendrix
rm -rf venv/
```
