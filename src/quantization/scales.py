"""
Musical Scale Definitions

Common scales for pitch quantization, especially blues and jazz scales.
"""

from typing import List, Dict

# Scale definitions as semitone intervals from root
# Format: scale_name -> list of semitones from root
SCALE_INTERVALS = {
    # Pentatonic Scales
    'major_pentatonic': [0, 2, 4, 7, 9],
    'minor_pentatonic': [0, 3, 5, 7, 10],

    # Blues Scales
    'blues': [0, 3, 5, 6, 7, 10],  # Minor pentatonic + b5
    'major_blues': [0, 2, 3, 4, 7, 9],

    # Major Modes
    'ionian': [0, 2, 4, 5, 7, 9, 11],  # Major scale
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],

    # Minor Modes
    'aeolian': [0, 2, 3, 5, 7, 8, 10],  # Natural minor
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10],

    # Harmonic/Melodic Minor
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11],

    # Chromatic (all notes)
    'chromatic': list(range(12)),
}

# Common root notes (MIDI pitch class)
ROOT_NOTES = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11,
}


def get_scale(scale_name: str, root: str = 'C', octave: int = 4) -> List[int]:
    """
    Get MIDI note numbers for a scale starting from a root note.

    Args:
        scale_name: Name of scale (e.g., 'minor_pentatonic', 'blues')
        root: Root note name (e.g., 'E', 'C#', 'Bb')
        octave: Starting octave (default: 4)

    Returns:
        List of MIDI note numbers in the scale across all octaves

    Example:
        >>> get_scale('minor_pentatonic', 'E', 4)
        [64, 67, 69, 71, 74]  # E, G, A, B, D starting from octave 4
    """
    if scale_name not in SCALE_INTERVALS:
        raise ValueError(f"Unknown scale: {scale_name}")

    if root not in ROOT_NOTES:
        raise ValueError(f"Unknown root note: {root}")

    # Get root MIDI note
    root_pitch_class = ROOT_NOTES[root]
    root_midi = octave * 12 + root_pitch_class

    # Generate scale notes across multiple octaves (covers MIDI range 0-127)
    scale_notes = []
    intervals = SCALE_INTERVALS[scale_name]

    for oct in range(-1, 10):  # Cover octaves -1 to 9
        for interval in intervals:
            midi_note = root_midi + (oct - octave) * 12 + interval
            if 0 <= midi_note <= 127:
                scale_notes.append(midi_note)

    return sorted(scale_notes)


def find_nearest_scale_note(midi_note: int, scale_notes: List[int]) -> int:
    """
    Find the nearest note in the scale to the given MIDI note.

    Args:
        midi_note: MIDI note number to quantize
        scale_notes: List of allowed MIDI notes

    Returns:
        Nearest MIDI note from the scale
    """
    if not scale_notes:
        return midi_note

    # Find minimum distance
    distances = [abs(midi_note - scale_note) for scale_note in scale_notes]
    min_index = distances.index(min(distances))

    return scale_notes[min_index]


def get_scale_name_list() -> List[str]:
    """Get list of available scale names."""
    return sorted(SCALE_INTERVALS.keys())


def get_root_note_list() -> List[str]:
    """Get list of available root notes."""
    return sorted(set(ROOT_NOTES.keys()), key=lambda x: ROOT_NOTES[x])


# Pre-defined common scales for convenience
SCALES = {
    'e_minor_pentatonic': get_scale('minor_pentatonic', 'E', 4),
    'e_blues': get_scale('blues', 'E', 4),
    'a_minor_pentatonic': get_scale('minor_pentatonic', 'A', 4),
    'a_blues': get_scale('blues', 'A', 4),
    'c_major': get_scale('ionian', 'C', 4),
    'g_major': get_scale('ionian', 'G', 4),
    'd_dorian': get_scale('dorian', 'D', 4),
}


if __name__ == '__main__':
    # Demo: print some scales
    print("E Minor Pentatonic:")
    print(get_scale('minor_pentatonic', 'E', 4)[:5])

    print("\nE Blues Scale:")
    print(get_scale('blues', 'E', 4)[:6])

    print("\nAvailable scales:")
    print(get_scale_name_list())
