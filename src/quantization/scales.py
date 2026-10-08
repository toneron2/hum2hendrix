"""
Musical Scale Definitions

Common scales for pitch quantization, especially blues and jazz scales.
"""

from bisect import bisect_left
from typing import Dict, FrozenSet, Iterable, List

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

# Root note name -> pitch class
ROOT_NOTES = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11,
}

MIDI_MIN = 0
MIDI_MAX = 127


def get_scale_pitch_classes(scale_name: str, root: str = 'C') -> FrozenSet[int]:
    """
    Get the pitch classes (0-11) of a scale.

    Args:
        scale_name: Name of scale (e.g., 'minor_pentatonic', 'blues')
        root: Root note name (e.g., 'E', 'C#', 'Bb')

    Returns:
        Set of pitch classes in the scale

    Example:
        >>> sorted(get_scale_pitch_classes('minor_pentatonic', 'E'))
        [2, 4, 7, 9, 11]  # D, E, G, A, B
    """
    if scale_name not in SCALE_INTERVALS:
        raise ValueError(f"Unknown scale: {scale_name}")
    if root not in ROOT_NOTES:
        raise ValueError(f"Unknown root note: {root}")

    root_pc = ROOT_NOTES[root]
    return frozenset((root_pc + interval) % 12 for interval in SCALE_INTERVALS[scale_name])


def get_scale(scale_name: str, root: str = 'C') -> List[int]:
    """
    Get all MIDI note numbers (0-127) belonging to a scale.

    Args:
        scale_name: Name of scale (e.g., 'minor_pentatonic', 'blues')
        root: Root note name (e.g., 'E', 'C#', 'Bb')

    Returns:
        Sorted list of MIDI note numbers in the scale across the full range

    Example:
        >>> get_scale('minor_pentatonic', 'E')[:5]
        [2, 4, 7, 9, 11]
    """
    pitch_classes = get_scale_pitch_classes(scale_name, root)
    return [n for n in range(MIDI_MIN, MIDI_MAX + 1) if n % 12 in pitch_classes]


def build_pitch_class_map(pitch_classes: Iterable[int]) -> Dict[int, int]:
    """
    Build a lookup from every pitch class (0-11) to the signed semitone offset
    that moves it to the nearest pitch class in `pitch_classes`.

    Ties resolve downward (toward the lower note), matching the behaviour of
    `find_nearest_scale_note`.
    """
    allowed = sorted(set(pc % 12 for pc in pitch_classes))
    if not allowed:
        raise ValueError("Scale must contain at least one pitch class")

    offsets: Dict[int, int] = {}
    for pc in range(12):
        best = None
        for target in allowed:
            # Nearest representative of `target` relative to `pc`, in [-6, 6]
            delta = (target - pc + 6) % 12 - 6
            if best is None or abs(delta) < abs(best) or (abs(delta) == abs(best) and delta < best):
                best = delta
        offsets[pc] = best
    return offsets


def find_nearest_scale_note(midi_note: int, scale_notes: List[int]) -> int:
    """
    Find the nearest note in a sorted list of allowed MIDI notes.

    Ties resolve to the lower note.

    Args:
        midi_note: MIDI note number to quantize
        scale_notes: Sorted list of allowed MIDI notes

    Returns:
        Nearest MIDI note from the list
    """
    if not scale_notes:
        return midi_note

    i = bisect_left(scale_notes, midi_note)
    if i == 0:
        return scale_notes[0]
    if i == len(scale_notes):
        return scale_notes[-1]

    lower, upper = scale_notes[i - 1], scale_notes[i]
    return upper if (upper - midi_note) < (midi_note - lower) else lower


def get_scale_name_list() -> List[str]:
    """Get list of available scale names."""
    return sorted(SCALE_INTERVALS.keys())


def get_root_note_list() -> List[str]:
    """Get list of available root notes, ordered by pitch class."""
    return sorted(ROOT_NOTES.keys(), key=lambda x: (ROOT_NOTES[x], x))


# Pre-defined common scales for convenience
SCALES = {
    'e_minor_pentatonic': get_scale('minor_pentatonic', 'E'),
    'e_blues': get_scale('blues', 'E'),
    'a_minor_pentatonic': get_scale('minor_pentatonic', 'A'),
    'a_blues': get_scale('blues', 'A'),
    'c_major': get_scale('ionian', 'C'),
    'g_major': get_scale('ionian', 'G'),
    'd_dorian': get_scale('dorian', 'D'),
}


if __name__ == '__main__':
    print("E Minor Pentatonic pitch classes:")
    print(sorted(get_scale_pitch_classes('minor_pentatonic', 'E')))

    print("\nE Blues Scale (first octave above middle C):")
    print([n for n in get_scale('blues', 'E') if 60 <= n < 72])

    print("\nAvailable scales:")
    print(get_scale_name_list())
