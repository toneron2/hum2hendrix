# hum2hendrix

**Hummed melodies to rendered electric guitar: pitch detection, quantization to a scale and
a grid, then a sampled instrument through an amplifier model.** The purpose is to separate
the musical idea from the motor skill needed to play it.

| | |
|---|---|
| **Status** | The audio-to-MIDI stage is in progress and rendering is not built. |
| **Code** | Python, 2,203 lines across `src/` (audio_to_midi, quantization, pipeline, visualization) and four scripts |
| **Audio to MIDI** | Spotify Basic Pitch (CREPE as an alternative) |
| **Quantization** | pitch to a chosen scale (e.g. E minor pentatonic); onsets and durations to 1/8 or 1/16 grid |
| **Rendering (planned)** | sampled Stratocaster (Unreal Instruments Standard Guitar in Plogue Sforzando), Neural Amp Modeler for the amplifier |
| **Licence** | MIT |

A standalone project on this account, separate from the governance architecture.

## Pipeline

```
 humming (WAV) ─▶ audio-to-MIDI ─▶ pitch + timing quantization ─▶ MIDI edit / view ─▶ guitar instrument ─▶ amp model ─▶ WAV
                  [in progress]     [in progress]                  [planned]           [not built]         [not built]
```

```bash
pip install -r requirements.txt
python scripts/hum_to_midi.py examples/audio/my_solo.wav --output output/solo.mid
python scripts/quantize_midi.py output/solo.mid --scale e_minor_pentatonic --grid 16
python scripts/visualize_midi.py output/solo_quantized.mid
```

The rendering stage is intended to run in a DAW (Reaper or Ardour) with NeuralNote for
conversion, the sampled guitar, and amplifier models from ToneHunt; the Python pipeline
produces the MIDI it consumes.

## Documents

[`docs/architecture/PIPELINE.md`](docs/architecture/PIPELINE.md),
[`docs/guides/INSTALLATION.md`](docs/guides/INSTALLATION.md),
[`docs/guides/USAGE.md`](docs/guides/USAGE.md),
[`docs/guides/SCALES.md`](docs/guides/SCALES.md).

## References

[Basic Pitch](https://github.com/spotify/basic-pitch) ·
[NeuralNote](https://github.com/DamRsn/NeuralNote) ·
[Neural Amp Modeler](https://github.com/sdatkinson/neural-amp-modeler) ·
[ToneHunt](https://tonehunt.org/) ·
[Plogue Sforzando](https://www.plogue.com/products/sforzando.html)

## Contact

Tony Slosar · TODOMODO.IO AGENCY LLC · anthonyslosar@gmail.com · [t.me/toneron2](https://t.me/toneron2) · [slosars.me](https://slosars.me)
