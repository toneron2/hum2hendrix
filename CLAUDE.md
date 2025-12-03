# Claude Code Collaboration Context

## Project Genesis

**Created**: December 3, 2025
**Location**: Initially conceived on mobile (Samsung Galaxy S23), developed in Termux/Claude Code
**AI Collaboration**: Gemini (initial brainstorming) → Claude Haiku (refinement) → Claude Sonnet 4.5 (implementation)

## Project Owner Context

**Background**: 58-year-old musician and software engineer with motor difficulties preventing guitar/piano performance. Extensive musical knowledge and internal auditory processing capabilities without instrumental execution ability.

**Development Style**:
- Works in **sequence**, not to imaginary deadlines
- Multiple concurrent projects managed by priority
- Speech-to-text heavily used due to motor constraints
- Home lab for primary development (managed by Claude Code)
- Mobile ideation and planning when away from workstation
- Trusts AI recommendations (75% accuracy rate)

**Musical Influences**:
- Mississippi Delta Blues to Stevie Ray Vaughan
- Jimi Hendrix (especially "Little Wing")
- 8-bar blues progressions
- Jazz phrasing and reharmonization

**Technical Goals**:
1. Convert hummed melodies to MIDI
2. Correct pitch (no natural pitch accuracy)
3. Correct timing (difficulty keeping time)
4. Render as authentic Stratocaster with Hendrix/SRV tone
5. Visualize chord progressions for experimentation
6. Achieve "refactoring code" workflow for music (pseudocode → syntax → debug → compile)

## Development Constraints

**Platform**:
- Primary: Linux workstation (home lab)
- Secondary: Android/Termux (mobile ideation)
- Waiting for more powerful workstation for speech-to-text integration

**Accessibility**:
- Motor difficulties require speech-to-text interfaces
- Visual MIDI editing preferred (piano roll as "paper")
- CLI-first approach for automation

**Philosophy**:
- No imaginary deadlines
- Work to sequence across multiple projects
- Open source preferred
- Hobbyist scope (not commercial)
- Technical over emotional language
- Concise communication

## Technical Architecture Decisions

### Hybrid Approach (Recommended)
Python CLI core + optional DAW integration for final polish.

**Rationale**:
- Python provides cross-platform compatibility (Linux workstation + potential Android)
- CLI enables automation and scripting
- DAW integration optional but available for advanced users
- Modular design allows incremental development

### Audio-to-MIDI Strategy
Primary: `basic-pitch` (Spotify open source)
Alternative: `crepe` or NeuralNote VST integration

**Rationale**:
- `basic-pitch` is actively maintained, well-documented, Python-native
- Works without GPU (important for various environments)
- Can be wrapped in CLI
- NeuralNote VST available as DAW integration path

### Quantization Approach
Use `music21` library for music theory operations.

**Rationale**:
- Handles scale definitions (pentatonic, blues, jazz modes)
- MIDI manipulation capabilities
- Music theory abstractions (intervals, chords, keys)

### Rendering Path
Phase 1: MIDI output only
Phase 2: VST hosting via Python (optional)
Phase 3: Native synthesis (stretch goal)

**Rationale**:
- Get MIDI pipeline working first
- User can import MIDI into DAW manually
- VST hosting complex, defer until core pipeline proven

## Key Features Priority

### Phase 1 (MVP)
1. Audio file → MIDI conversion
2. Pitch quantization to user-specified scale
3. Timing quantization to grid
4. MIDI file output

### Phase 2 (Visualization)
1. Piano roll visualization (matplotlib or web-based)
2. Chord progression overlay
3. Before/after comparison

### Phase 3 (Advanced)
1. VST integration for rendering
2. Amp simulation
3. Batch processing

### Phase 4 (Experimentation)
1. Chord progression variants
2. Reharmonization suggestions
3. Jazz voicing generation

## Workflow Example: "Little Wing" Solo

```bash
# 1. Record humming over backing track (external tool or system mic)
# 2. Convert to MIDI
python scripts/hum_to_midi.py my_solo.wav

# 3. Quantize to E minor pentatonic, 1/16th grid
python scripts/quantize_midi.py my_solo.mid --scale e_minor_pentatonic --tempo 72

# 4. Visualize and inspect
python scripts/visualize_midi.py my_solo_quantized.mid

# 5. (Optional) Render with guitar + amp
python scripts/render_audio.py my_solo_quantized.mid --tone hendrix
```

## Development Environment

**Primary Workstation** (future):
- Linux-based
- Full VST support
- Python 3.9+
- Speech-to-text integration in progress

**Current Mobile** (Android/Termux):
- Git available
- Python to be installed
- Used for planning and documentation

## Communication Preferences

- **Technical, not emotional**: Focus on engineering, no feelings/emotions
- **Concise**: 1-2 paragraphs max per response during brainstorming
- **No fluff**: Skip pleasantries, get to substance
- **Assumptions OK**: 75% accuracy means make smart decisions
- **Sequence-based planning**: No timelines, just ordered steps

## AI Collaboration Notes

**What Works**:
- Claude Code manages entire home lab infrastructure
- Trust in AI recommendations (high success rate)
- Speech-to-text on mobile for ideation
- Parallel work on multiple projects

**What to Avoid**:
- Imaginary deadlines ("2-3 weeks out")
- Emotional language
- Long responses during brainstorming
- Asking too many clarifying questions (make smart assumptions)

## Repository Maintenance

**Commit Style**: Technical, descriptive
**Branching**: Feature branches for major additions
**Documentation**: Keep up-to-date as architecture evolves
**Testing**: Unit tests for each module

## Future Enhancements (Unprioritized)

- Web interface for mobile editing
- Real-time processing (low-latency humming)
- Collaborative jamming (multiple users)
- Machine learning for style transfer (learn user's phrasing)
- Integration with backing track generation
- Automatic chord progression detection from hummed melody

## Questions for Future Sessions

1. Desktop vs pure-Python rendering approach?
2. Web interface value vs CLI-only?
3. Real-time processing requirements?
4. Multi-instrument support beyond guitar?

## Related Projects in Home Lab

(To be documented as relevant integrations emerge)

## Version History

- v0.1 (Dec 3, 2025): Initial repository creation, architecture planning
- Future versions tracked in CHANGELOG.md

## Notes for Future Claude Sessions

- User works in sequence, not timelines
- Trust established - make architectural decisions confidently
- Focus on modular, testable code
- CLI-first, GUI optional
- Open source preferred
- This is a passion project, not commercial
- Motor difficulties inform UX decisions (speech-to-text, visual editing)
