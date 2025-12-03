# Usage Guide

## Quick Start

Convert hummed audio to quantized MIDI in one command:

```bash
python scripts/h2h_pipeline.py my_humming.wav
```

This will:
1. Convert audio to MIDI
2. Quantize pitch to E minor pentatonic
3. Quantize timing to 16th note grid
4. Generate visualizations
5. Save all outputs to `./output/`

## Command Line Tools

### 1. Full Pipeline

```bash
python scripts/h2h_pipeline.py [OPTIONS] AUDIO_FILE
```

**Options:**
- `--config, -c`: Configuration file (YAML)
- `--output-dir, -o`: Output directory
- `--scale, -s`: Scale name (default: minor_pentatonic)
- `--root, -r`: Root note (default: E)
- `--tempo, -t`: Tempo in BPM (default: 72)
- `--grid, -g`: Timing grid (default: 16)
- `--no-visualize`: Skip visualization

**Examples:**

```bash
# Basic usage (E minor pentatonic, 16th notes)
python scripts/h2h_pipeline.py humming.wav

# Blues in A, 8th note triplets, 120 BPM
python scripts/h2h_pipeline.py solo.mp3 --scale blues --root A --grid 8 --tempo 120

# Use custom configuration
python scripts/h2h_pipeline.py melody.wav --config config/little_wing.yaml

# Save to specific directory
python scripts/h2h_pipeline.py audio.wav -o ./my_project/output
```

### 2. Audio to MIDI Only

Convert audio without quantization:

```bash
python scripts/hum_to_midi.py [OPTIONS] AUDIO_FILE
```

**Examples:**

```bash
# Basic conversion
python scripts/hum_to_midi.py humming.wav

# Specify output file
python scripts/hum_to_midi.py audio.mp3 --output raw_solo.mid

# Use CREPE model instead of Basic Pitch
python scripts/hum_to_midi.py audio.wav --model crepe

# Lower confidence threshold (detect more notes)
python scripts/hum_to_midi.py quiet.wav --confidence 0.3
```

### 3. MIDI Quantization Only

Quantize existing MIDI file:

```bash
python scripts/quantize_midi.py [OPTIONS] MIDI_FILE
```

**Examples:**

```bash
# Quantize pitch to E blues scale
python scripts/quantize_midi.py raw.mid --scale blues --root E

# Quantize timing to 16th note grid
python scripts/quantize_midi.py raw.mid --grid 16

# Both pitch and timing
python scripts/quantize_midi.py raw.mid --scale minor_pentatonic --root A --grid 16

# Pitch only (no timing correction)
python scripts/quantize_midi.py raw.mid --pitch-only --scale blues

# Timing only (no pitch correction)
python scripts/quantize_midi.py raw.mid --timing-only --grid 8
```

### 4. Visualization Only

Generate piano roll visualizations:

```bash
python scripts/visualize_midi.py [OPTIONS] MIDI_FILE
```

**Examples:**

```bash
# Basic piano roll
python scripts/visualize_midi.py solo.mid

# Compare before/after quantization
python scripts/visualize_midi.py quantized.mid --compare raw.mid

# Overlay chord progression (Little Wing example)
python scripts/visualize_midi.py solo.mid --chords "Em:0:2,G:2:2,Am:4:2,Em:6:2"

# Save to specific file
python scripts/visualize_midi.py solo.mid --output my_visualization.png
```

## Workflow Examples

### Example 1: Simple Solo (E Minor Pentatonic)

```bash
# Record humming (use your preferred audio recorder)
# Filename: my_solo.wav

# Convert with defaults (E minor pentatonic, 16th notes, 72 BPM)
python scripts/h2h_pipeline.py my_solo.wav

# Output files created:
# - output/my_solo_raw.mid (raw conversion)
# - output/my_solo_pitch_quantized.mid (pitch corrected)
# - output/my_solo_final.mid (pitch + timing corrected)
# - output/my_solo_pianoroll.png (visualization)
# - output/my_solo_comparison.png (before/after)
```

### Example 2: Little Wing Style Solo

```bash
# Use pre-configured Little Wing settings
python scripts/h2h_pipeline.py humming.wav --config config/little_wing.yaml

# Or specify manually:
python scripts/h2h_pipeline.py humming.wav \
  --scale minor_pentatonic \
  --root E \
  --tempo 72 \
  --grid 16
```

### Example 3: SRV Blues with Swing

```bash
# Use SRV blues configuration
python scripts/h2h_pipeline.py blues_solo.wav --config config/srv_blues.yaml

# Or specify manually:
python scripts/h2h_pipeline.py blues_solo.wav \
  --scale blues \
  --root E \
  --tempo 120 \
  --grid 8
```

### Example 4: Step-by-Step Processing

```bash
# Step 1: Convert audio to MIDI (no quantization)
python scripts/hum_to_midi.py humming.wav --output raw.mid

# Step 2: Inspect raw MIDI
python scripts/visualize_midi.py raw.mid --output raw_view.png

# Step 3: Quantize pitch only
python scripts/quantize_midi.py raw.mid --pitch-only \
  --scale blues --root A --output pitch_fixed.mid

# Step 4: Quantize timing
python scripts/quantize_midi.py pitch_fixed.mid --timing-only \
  --grid 16 --output final.mid

# Step 5: Compare results
python scripts/visualize_midi.py final.mid --compare raw.mid
```

### Example 5: Jazz Reharmonization

```bash
# Convert melody
python scripts/hum_to_midi.py melody.wav --output melody.mid

# Visualize with chord progression
python scripts/visualize_midi.py melody.mid \
  --chords "Em7:0:2,Gmaj7:2:2,Am7:4:2,Em7:6:2" \
  --output with_chords.png

# Try alternate harmony
python scripts/visualize_midi.py melody.mid \
  --chords "Em7:0:2,G7:2:2,Am7b5:4:2,Em7:6:2" \
  --output alternate_harmony.png
```

## Configuration Files

### Using Pre-made Configs

```bash
# Little Wing style
python scripts/h2h_pipeline.py solo.wav --config config/little_wing.yaml

# SRV blues style
python scripts/h2h_pipeline.py solo.wav --config config/srv_blues.yaml

# Default settings
python scripts/h2h_pipeline.py solo.wav --config config/default.yaml
```

### Creating Custom Config

1. Copy `config/default.yaml` to `config/my_config.yaml`
2. Edit parameters:

```yaml
quantization:
  pitch:
    scale: blues
    root: A
  timing:
    grid: 8
    tempo: 120
    swing: 0.66  # Triplet swing
```

3. Use your config:

```bash
python scripts/h2h_pipeline.py audio.wav --config config/my_config.yaml
```

## Python API Usage

Use the library directly in Python scripts:

```python
from pathlib import Path
from pipeline import HumToHendrixPipeline
from pipeline.config import Config

# Create pipeline with defaults
pipeline = HumToHendrixPipeline()

# Or with custom config
config = Config()
config.quantization.pitch.scale = 'blues'
config.quantization.pitch.root = 'A'
pipeline = HumToHendrixPipeline(config)

# Process audio file
results = pipeline.process(
    audio_path=Path('my_solo.wav'),
    output_dir=Path('./output'),
    visualize=True,
)

# Access generated files
print(f"Final MIDI: {results['final_midi']}")
print(f"Visualization: {results['piano_roll']}")
```

## Tips and Best Practices

### Recording Tips

1. **Environment**: Record in a quiet room
2. **Microphone**: USB microphone recommended, built-in mic works
3. **Distance**: 6-12 inches from microphone
4. **Volume**: Moderate volume, not too loud or quiet
5. **Format**: WAV or FLAC preferred (uncompressed)

### Humming Tips

1. **Clarity**: Hum clearly with consistent tone
2. **Pitch**: Don't worry about perfect pitch (quantization fixes it)
3. **Timing**: Approximate rhythm (quantization fixes it)
4. **Articulation**: Separate notes with slight pauses
5. **Duration**: Start with short phrases (4-8 bars)

### Parameter Tuning

**If too many notes detected:**
- Increase `confidence_threshold` (0.5 → 0.7)
- Increase `min_note_duration` (0.1 → 0.2)

**If too few notes detected:**
- Decrease `confidence_threshold` (0.5 → 0.3)
- Decrease `min_note_duration` (0.1 → 0.05)

**If timing feels robotic:**
- Use coarser grid (16 → 8)
- Add swing (0.0 → 0.5-0.66)

**If pitch corrections sound wrong:**
- Try different scale (minor_pentatonic → blues)
- Check root note matches backing track

## Troubleshooting

### No MIDI notes generated

- Check audio file plays correctly
- Try lower `confidence_threshold` (e.g., 0.3)
- Ensure humming is audible and clear
- Try `--model crepe` as alternative

### Wrong notes after quantization

- Verify scale and root note match backing track
- Try visualizing before quantization to check raw conversion
- Some notes may need manual editing in DAW

### Timing still off after quantization

- Verify tempo matches backing track
- Try different grid resolution (8, 16, or 32)
- Check if swing should be enabled

## Next Steps

- See [SCALES.md](SCALES.md) for available scales
- See [VST_SETUP.md](VST_SETUP.md) for audio rendering (future)
- Check [examples/](../examples/) for sample workflows
- Read [PIPELINE.md](../architecture/PIPELINE.md) for technical details
