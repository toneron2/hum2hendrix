"""Tests for scale definitions and nearest-note lookup."""

import random

import pytest

from quantization.scales import (
    build_pitch_class_map,
    find_nearest_scale_note,
    get_scale,
    get_scale_pitch_classes,
)


def test_pitch_classes_for_e_minor_pentatonic():
    assert sorted(get_scale_pitch_classes('minor_pentatonic', 'E')) == [2, 4, 7, 9, 11]


def test_get_scale_covers_full_midi_range():
    notes = get_scale('blues', 'A')
    assert notes[0] >= 0 and notes[-1] <= 127
    assert all(n % 12 in get_scale_pitch_classes('blues', 'A') for n in notes)
    assert 69 in notes and 72 in notes and 75 in notes  # A, C, Eb


def test_unknown_scale_or_root_rejected():
    with pytest.raises(ValueError):
        get_scale('whole_tone', 'C')
    with pytest.raises(ValueError):
        get_scale('blues', 'H')


def test_pitch_class_map_ties_resolve_downward():
    offsets = build_pitch_class_map({4, 7})  # E and G
    assert offsets[4] == 0 and offsets[7] == 0
    assert offsets[5] == -1  # F -> E
    assert offsets[6] == 1   # F# -> G
    # D# (3) is 1 from E (4): up
    assert offsets[3] == 1
    # A# (10): 3 to G, 6 to E -> G
    assert offsets[10] == -3


def test_find_nearest_matches_linear_scan():
    scale = get_scale('dorian', 'D')
    rng = random.Random(0)
    for _ in range(500):
        note = rng.randint(0, 127)
        distances = [abs(note - s) for s in scale]
        expected = scale[distances.index(min(distances))]
        assert find_nearest_scale_note(note, scale) == expected
    assert find_nearest_scale_note(60, []) == 60
