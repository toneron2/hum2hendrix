# hum2hendrix

**Hummed melodies to rendered electric guitar: pitch detection, quantization to a scale and
a grid, then a sampled instrument through an amplifier model.** The purpose is to separate
the musical idea from the motor skill needed to play it.

| | |
|---|---|
| **Status** | Audio to MIDI, quantization and piano-roll views run, with 68 tests; rendering is not built. |
| **Release** | [0.2.0](https://github.com/toneron2/hum2hendrix/releases/tag/v0.2.0), October 2026 |
| **Code** | Python, 2,287 lines across `src/` (audio_to_midi, quantization, pipeline, visualization) and four commands |
| **Python** | 3.9 to 3.11, because Basic Pitch pins TensorFlow below 2.16; the librosa pYIN model runs on any version |
| **Audio to MIDI** | Spotify Basic Pitch; librosa pYIN and CREPE (separate install) as alternatives |
| **Quantization** | pitch to a chosen scale (e.g. E minor pentatonic); onsets and offsets to a 1/4 to 1/32 grid, with swing |
| **Rendering (planned)** | sampled Stratocaster (Unreal Instruments Standard Guitar in Plogue Sforzando), Neural Amp Modeler for the amplifier |
| **Licence** | MIT |

A standalone project on this account, separate from the governance architecture.

## Pipeline

```
 humming (WAV) ─▶ audio-to-MIDI ─▶ pitch + timing quantization ─▶ piano-roll view ─▶ guitar instrument ─▶ amp model ─▶ WAV
                  [runs]           [runs]                         [runs]             [not built]          [not built]
```

```bash
pip install -r requirements.txt && pip install .
h2h-pipeline hum.wav --scale minor_pentatonic --root E --grid 8 --swing 0.66 -o output
```

The stages also run one at a time:

```bash
hum2midi hum.wav -o solo.mid --tempo 72
quantize-midi solo.mid --scale minor_pentatonic --root E --grid 16 -o solo_q.mid
visualize-midi solo_q.mid --compare solo.mid -o compare.png
python -m pytest tests
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
