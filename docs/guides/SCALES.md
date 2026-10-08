# Musical Scales Reference

## Available Scales

### Pentatonic Scales

**major_pentatonic**
- Intervals: 1, 2, 3, 5, 6
- Example (C): C, D, E, G, A
- Sound: Bright, happy, country/rock
- Use: Major key solos, country licks

**minor_pentatonic**
- Intervals: 1, ♭3, 4, 5, ♭7
- Example (E): E, G, A, B, D
- Sound: Dark, bluesy, rock
- Use: Rock/blues solos (Hendrix, SRV, Clapton)
- **Most common for blues/rock**

### Blues Scales

**blues**
- Intervals: 1, ♭3, 4, ♭5, 5, ♭7
- Example (E): E, G, A, B♭, B, D
- Sound: Classic blues, gritty
- Use: Blues solos with "blue note" (♭5)
- **Adds spice to minor pentatonic**

**major_blues**
- Intervals: 1, 2, ♭3, 3, 5, 6
- Example (E): E, F#, G, G#, B, C#
- Sound: Major blues, jazzy
- Use: Major key blues, jazz-blues

### Major Modes (Diatonic)

**ionian** (Major scale)
- Intervals: 1, 2, 3, 4, 5, 6, 7
- Example (C): C, D, E, F, G, A, B
- Sound: Happy, bright, resolved
- Use: Major key melodies

**lydian**
- Intervals: 1, 2, 3, ♯4, 5, 6, 7
- Example (F): F, G, A, B, C, D, E
- Sound: Dreamy, floating, ethereal
- Use: Jazz, fusion, Steve Vai

**mixolydian**
- Intervals: 1, 2, 3, 4, 5, 6, ♭7
- Example (G): G, A, B, C, D, E, F
- Sound: Bluesy major, rock
- Use: Rock riffs, dominant 7 chords

### Minor Modes

**aeolian** (Natural minor)
- Intervals: 1, 2, ♭3, 4, 5, ♭6, ♭7
- Example (A): A, B, C, D, E, F, G
- Sound: Sad, dark, resolved
- Use: Minor key melodies

**dorian**
- Intervals: 1, 2, ♭3, 4, 5, 6, ♭7
- Example (D): D, E, F, G, A, B, C
- Sound: Jazzy minor, funky
- Use: Jazz, funk, Santana

**phrygian**
- Intervals: 1, ♭2, ♭3, 4, 5, ♭6, ♭7
- Example (E): E, F, G, A, B, C, D
- Sound: Spanish, dark, exotic
- Use: Flamenco, metal, Middle Eastern

**locrian**
- Intervals: 1, ♭2, ♭3, 4, ♭5, ♭6, ♭7
- Example (B): B, C, D, E, F, G, A
- Sound: Unstable, dissonant, tense
- Use: Diminished contexts, theory exercises

### Advanced Minor

**harmonic_minor**
- Intervals: 1, 2, ♭3, 4, 5, ♭6, 7
- Example (A): A, B, C, D, E, F, G#
- Sound: Classical, dramatic, exotic
- Use: Classical, neoclassical metal, Yngwie

**melodic_minor**
- Intervals: 1, 2, ♭3, 4, 5, 6, 7
- Example (A): A, B, C, D, E, F#, G#
- Sound: Jazz minor, sophisticated
- Use: Jazz improvisation, fusion

### Special

**chromatic**
- All 12 notes
- Use: No quantization (keep all pitches)

## Root Notes

Available root notes:
- **Natural**: C, D, E, F, G, A, B
- **Sharps**: C#, D#, F#, G#, A#
- **Flats**: Db, Eb, Gb, Ab, Bb

## Common Combinations

### Blues/Rock Guitar

| Key | Scale | Root | Use Case |
|-----|-------|------|----------|
| E Minor | minor_pentatonic | E | Most common blues/rock key |
| E Minor | blues | E | Add blue note flavor |
| A Minor | minor_pentatonic | A | Second most common |
| G Major | mixolydian | G | Rock riffs, Stones style |

### Hendrix Style

**Little Wing**: E minor pentatonic / E blues
**Red House**: E blues
**Bold As Love**: E dorian (jazzy)
**The Wind Cries Mary**: F major → D aeolian

### Stevie Ray Vaughan

**Texas Flood**: E blues
**Pride and Joy**: E blues / E minor pentatonic
**Lenny**: E minor pentatonic
**Riviera Paradise**: E major blues / E mixolydian

### Jazz

**Dorian**: Minor 7 chords (Dm7, Am7)
**Mixolydian**: Dominant 7 chords (G7, D7)
**Lydian**: Major 7 chords (Cmaj7, Fmaj7)
**Melodic Minor**: Minor/Major 7 (Aminm7, Cminmaj7)

## Usage Examples

### CLI

```bash
# E minor pentatonic (default)
python scripts/h2h_pipeline.py audio.wav --scale minor_pentatonic --root E

# A blues scale
python scripts/h2h_pipeline.py audio.wav --scale blues --root A

# D dorian (jazz)
python scripts/h2h_pipeline.py audio.wav --scale dorian --root D

# C# harmonic minor
python scripts/h2h_pipeline.py audio.wav --scale harmonic_minor --root "C#"
```

### Python API

```python
from quantization import PitchQuantizer

# Create quantizer for specific scale
quantizer = PitchQuantizer(
    scale_name='blues',
    root='E',
)

# Quantize MIDI file
quantizer.quantize_midi_file('raw.mid', 'quantized.mid')
```

### Custom Scale

```python
from quantization import PitchQuantizer

# Define custom scale as MIDI note numbers (used as pitch classes in every octave)
custom_scale = [64, 67, 69, 71, 74]  # E, G, A, B, D (E minor pentatonic)

quantizer = PitchQuantizer(scale_notes=custom_scale)
```

## Scale Selection Guide

### Choose based on backing track:

1. **Major key** → Try mixolydian or major pentatonic
2. **Minor key** → Try minor pentatonic or blues
3. **Dominant 7 chord** → Mixolydian or blues
4. **Minor 7 chord** → Dorian or aeolian
5. **Jazz** → Dorian, melodic minor, or chromatic (no quantization)

### Choose based on style:

- **Classic blues**: blues scale
- **Rock guitar**: minor_pentatonic
- **Funk**: dorian
- **Jazz**: dorian, melodic_minor
- **Classical**: harmonic_minor, ionian
- **Metal**: phrygian, harmonic_minor
- **Flamenco**: phrygian

### Experimentation:

Try multiple scales on the same melody:

```bash
# Generate multiple versions
for scale in minor_pentatonic blues dorian; do
  python scripts/quantize_midi.py raw.mid \
    --scale $scale --root E \
    --output "quantized_${scale}.mid"
done
```

## Theory Quick Reference

### Intervals

- **1**: Root (tonic)
- **♭2**: Minor second
- **2**: Major second
- **♭3**: Minor third
- **3**: Major third
- **4**: Perfect fourth
- **♯4/♭5**: Tritone (augmented 4th / diminished 5th)
- **5**: Perfect fifth
- **♭6**: Minor sixth
- **6**: Major sixth
- **♭7**: Minor seventh (dominant)
- **7**: Major seventh (leading tone)

### Semitones from Root

| Note | Semitones |
|------|-----------|
| Root | 0 |
| ♭2 | 1 |
| 2 | 2 |
| ♭3 | 3 |
| 3 | 4 |
| 4 | 5 |
| ♯4/♭5 | 6 |
| 5 | 7 |
| ♭6 | 8 |
| 6 | 9 |
| ♭7 | 10 |
| 7 | 11 |

## Further Reading

- [Music Theory for Guitar](https://www.musictheory.net/)
- [Modes Explained](https://www.guitarhabits.com/modes/)
- [Pentatonic vs Blues Scale](https://www.guitarplayer.com/lessons/pentatonic-vs-blues-scale)
