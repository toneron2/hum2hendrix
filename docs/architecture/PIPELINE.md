# Pipeline Architecture

## System Overview

The Hum-to-Hendrix pipeline is a five-stage signal processing system that transforms vocal audio into rendered guitar audio with style-appropriate timbral characteristics.

```
┌─────────────────────────────────────────────────────────────────┐
│                        HUM-TO-HENDRIX PIPELINE                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ Audio Input  │  WAV/MP3/FLAC (hummed melody)
│ (Microphone) │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│   Stage 1: Audio Analysis    │
│   ─────────────────────────  │
│   - Load audio file           │
│   - Normalize amplitude       │
│   - Resample to 22050 Hz     │
│   - Extract harmonic content  │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│   Stage 2: Pitch Detection   │
│   ─────────────────────────  │
│   - Run inference (Basic     │
│     Pitch or CREPE)          │
│   - Extract F0 contour       │
│   - Detect note onsets       │
│   - Estimate velocities      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Stage 3: MIDI Conversion    │
│  ──────────────────────────  │
│  - Convert Hz to MIDI notes  │
│  - Create Note On/Off events │
│  - Set tempo from analysis   │
│  - Output raw MIDI file      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Stage 4: Quantization       │
│  ──────────────────────────  │
│  Pitch Quantization:         │
│  - Load scale definition     │
│  - Snap each note to         │
│    nearest scale degree      │
│                              │
│  Timing Quantization:        │
│  - Detect tempo/meter        │
│  - Snap onsets to grid       │
│    (1/8, 1/16, 1/32 notes)   │
│  - Adjust durations          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Stage 5: Synthesis          │
│  ──────────────────────────  │
│  Path A: MIDI Export         │
│  - Write corrected MIDI      │
│                              │
│  Path B: Audio Rendering     │
│  - Load guitar VST           │
│  - Render MIDI → Audio       │
│  - Apply amp simulation      │
│  - Export WAV                │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────┐
│  Output Files    │
│  ──────────────  │
│  - Quantized     │
│    MIDI          │
│  - Rendered      │
│    Audio (WAV)   │
└──────────────────┘
```

## Module Breakdown

### Module 1: Audio-to-MIDI (`src/audio_to_midi/`)

**Purpose**: Convert hummed audio into raw MIDI note events.

**Components**:
- `converter.py`: Main conversion logic
- `pitch_detection.py`: Wrapper for Basic Pitch or CREPE
- `onset_detection.py`: Note start/end detection
- `velocity_estimation.py`: Dynamic level estimation

**Key Algorithm**: Basic Pitch (Spotify)
- Deep learning model trained on multi-instrument audio
- Outputs MIDI with pitch, onset, and offset predictions
- Handles pitch bends (critical for blues)

**Inputs**:
- Audio file (WAV, MP3, FLAC)
- Sample rate: 22050 Hz (model requirement)

**Outputs**:
- Raw MIDI file with uncorrected pitch/timing
- Confidence scores per note (for filtering)

**Configuration Options**:
- Minimum note duration threshold
- Confidence threshold for note detection
- Onset sensitivity

---

### Module 2: Quantization (`src/quantization/`)

**Purpose**: Correct pitch and timing to musical constraints.

**Components**:
- `pitch_quantizer.py`: Scale-based pitch correction
- `timing_quantizer.py`: Grid-based rhythm correction
- `scales.py`: Scale definitions (pentatonic, blues, jazz modes)

#### Pitch Quantization Algorithm

```python
def quantize_pitch(note, scale):
    """
    Snap MIDI note to nearest scale degree.

    Args:
        note: MIDI note number (0-127)
        scale: List of allowed MIDI notes in one octave

    Returns:
        Corrected MIDI note number
    """
    # Find nearest note in scale (any octave)
    octave = note // 12
    pitch_class = note % 12

    # Find closest pitch class in scale
    scale_pitch_classes = [n % 12 for n in scale]
    closest = min(scale_pitch_classes,
                  key=lambda x: abs(x - pitch_class))

    # Reconstruct in original octave
    return octave * 12 + closest
```

**Scale Definitions**:
- E Minor Pentatonic: [E, G, A, B, D]
- E Blues: [E, G, A, Bb, B, D]
- E Dorian: [E, F#, G, A, B, C#, D]
- Custom scales supported via config

#### Timing Quantization Algorithm

```python
def quantize_timing(notes, grid_resolution, tempo):
    """
    Snap note onsets to rhythmic grid.

    Args:
        notes: List of (onset_time, duration, pitch) tuples
        grid_resolution: 4 (quarter), 8 (eighth), 16 (sixteenth)
        tempo: BPM

    Returns:
        Quantized notes with corrected onsets/durations
    """
    # Convert tempo to time per grid unit
    beat_duration = 60.0 / tempo
    grid_duration = beat_duration / (grid_resolution / 4)

    quantized = []
    for onset, duration, pitch in notes:
        # Snap onset to nearest grid line
        grid_position = round(onset / grid_duration)
        new_onset = grid_position * grid_duration

        # Optionally quantize duration as well
        new_duration = round(duration / grid_duration) * grid_duration

        quantized.append((new_onset, new_duration, pitch))

    return quantized
```

**Swing Support**: Optional swing parameter (50-75%) for jazz feel.

---

### Module 3: Visualization (`src/visualization/`)

**Purpose**: Display MIDI data for inspection and editing.

**Components**:
- `piano_roll.py`: Matplotlib-based piano roll
- `chord_overlay.py`: Overlay chord progressions on piano roll
- `comparison_view.py`: Before/after quantization comparison

**Piano Roll Features**:
- Horizontal axis: Time (bars/beats)
- Vertical axis: Pitch (MIDI note number)
- Color: Velocity (dynamics)
- Grid lines: Beat subdivisions

**Chord Visualization**:
- Display chord names above timeline
- Show chord tones on piano roll
- Highlight non-chord tones (tensions)

**Export Options**:
- PNG/SVG for static images
- Interactive HTML with zoom/pan
- MIDI player integration

---

### Module 4: Synthesis (`src/synthesis/`)

**Purpose**: Render MIDI as audio with guitar timbre.

**Components**:
- `vst_host.py`: Host VST plugins (future)
- `sampler.py`: Simple sample playback (MVP)
- `amp_sim.py`: Apply amp simulation (future)

#### MVP Approach: Sample Playback

For Phase 1, use basic sample playback:
- Load WAV samples per MIDI note
- Trigger samples at correct timing
- Apply ADSR envelope
- Mix to stereo

#### Advanced Approach: VST Hosting

For Phase 2+, integrate real VST plugins:
- Use `pedalboard` library (Spotify) for VST hosting
- Load Standard Guitar VST
- Load Neural Amp Modeler (NAM)
- Render MIDI → Audio in Python

---

### Module 5: Pipeline Orchestration (`src/pipeline/`)

**Purpose**: Coordinate all stages, handle errors, manage config.

**Components**:
- `orchestrator.py`: Main pipeline controller
- `config_loader.py`: Load YAML configurations
- `error_handler.py`: Robust error handling
- `progress_tracker.py`: Status reporting

**Configuration Schema** (`config/default.yaml`):

```yaml
audio_input:
  sample_rate: 22050
  normalize: true

conversion:
  model: basic_pitch  # or 'crepe'
  confidence_threshold: 0.5
  min_note_duration: 0.1  # seconds

quantization:
  pitch:
    enabled: true
    scale: e_minor_pentatonic
    root: E4
  timing:
    enabled: true
    grid: 16  # sixteenth notes
    tempo: 72  # BPM
    swing: 0  # 0-75

synthesis:
  mode: midi_export  # or 'audio_render'
  instrument: stratocaster
  amp_model: fender_twin

output:
  directory: ./output
  format: wav
  bit_depth: 24
  sample_rate: 44100
```

---

## Data Flow Diagram

```
┌─────────────┐
│ Input Audio │
│  (vocals)   │
└──────┬──────┘
       │
       │ numpy.ndarray (audio samples)
       ▼
┌──────────────────┐
│ Pitch Detection  │
│  (Basic Pitch)   │
└──────┬───────────┘
       │
       │ List[(time, frequency, confidence)]
       ▼
┌──────────────────┐
│ MIDI Conversion  │
└──────┬───────────┘
       │
       │ mido.MidiFile (raw)
       ▼
┌──────────────────┐
│  Quantization    │
└──────┬───────────┘
       │
       │ mido.MidiFile (corrected)
       ▼
┌──────────────────┐
│  Visualization   │  (Optional inspection)
└──────────────────┘
       │
       ▼
┌──────────────────┐
│   Synthesis      │
└──────┬───────────┘
       │
       │ numpy.ndarray (audio samples)
       ▼
┌──────────────────┐
│  Output Audio    │
│  (guitar WAV)    │
└──────────────────┘
```

---

## Error Handling Strategy

**Audio Input Errors**:
- File not found → Clear error message
- Unsupported format → Suggest conversion
- Corrupted file → Report specific issue

**Conversion Errors**:
- No pitch detected → Check input volume, suggest re-recording
- Low confidence → Warn user, proceed with best guess
- Model loading failure → Check installation

**Quantization Errors**:
- Invalid scale → Provide valid scale list
- Tempo out of range → Clamp to reasonable bounds (40-240 BPM)

**Synthesis Errors**:
- VST not found → Fallback to MIDI export
- Rendering timeout → Report progress, save partial

---

## Performance Considerations

**Audio Processing**:
- Basic Pitch inference: ~0.5x realtime (10s audio = 5s processing)
- CREPE faster but less accurate for vocals

**MIDI Quantization**:
- Negligible (<0.1s for 1000 notes)

**Audio Rendering**:
- Real-time or faster with optimized VSTs
- Sample-based synthesis: near-instant

**Bottleneck**: Audio-to-MIDI conversion (inference time)

**Optimization**:
- Batch processing for multiple files
- GPU acceleration for Basic Pitch (optional)
- Caching intermediate results

---

## Testing Strategy

**Unit Tests**:
- Each module independently testable
- Mock dependencies (audio files, models)

**Integration Tests**:
- Full pipeline with known input/output pairs
- Regression tests for quantization accuracy

**Test Data**:
- Synthetic audio (pure sine waves at known frequencies)
- Real hummed samples with ground truth MIDI
- Edge cases (whisper-quiet, shouted dynamics)

---

## Future Enhancements

1. **Real-time Processing**: Low-latency mode for live performance
2. **Machine Learning Style Transfer**: Learn user's phrasing patterns
3. **Multi-track Support**: Hum melody + bass + chords separately
4. **Automatic Chord Detection**: Infer harmony from melody
5. **Collaborative Mode**: Multiple users jam together remotely

---

## Dependencies

Core libraries:
- `basic-pitch`: Audio-to-MIDI conversion
- `librosa`: Audio analysis
- `mido`: MIDI file I/O
- `music21`: Music theory operations
- `numpy`: Numerical computing
- `scipy`: Signal processing
- `matplotlib`: Visualization
- `pyyaml`: Configuration parsing

Optional:
- `pedalboard`: VST hosting (Spotify library)
- `crepe`: Alternative pitch detection
- `tensorflow`: If using Basic Pitch with GPU

---

## References

- [Basic Pitch Paper](https://arxiv.org/abs/2209.10839)
- [CREPE Paper](https://arxiv.org/abs/1802.06182)
- [MIDI Specification](https://www.midi.org/specifications)
- [Music21 Documentation](https://web.mit.edu/music21/)
