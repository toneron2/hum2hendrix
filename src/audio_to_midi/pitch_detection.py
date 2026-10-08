"""
Pitch Detection Wrappers

Interfaces to various pitch detection models (Basic Pitch, CREPE, librosa pyin).

Two kinds of detector live here:

* Note detectors return discrete note events ``(start, end, midi_note, amplitude)``.
  Basic Pitch is a note detector: it runs its own onset/offset segmentation.
* Contour detectors return frame-wise ``(times, frequencies, confidences)`` arrays.
  CREPE and librosa's pyin are contour detectors; the converter segments their
  output into notes.
"""

from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

NoteEvent = Tuple[float, float, int, float]


def detect_notes_basic_pitch(
    audio_path: Union[str, Path],
    onset_threshold: float = 0.5,
    frame_threshold: float = 0.3,
    min_note_len: float = 58.0,  # milliseconds
    min_freq: float = 80.0,  # Hz (E2)
    max_freq: float = 1200.0,  # Hz (D6)
) -> List[NoteEvent]:
    """
    Detect notes using Spotify's Basic Pitch model.

    Basic Pitch loads and resamples the audio itself, so it takes a file path
    rather than samples.

    Args:
        audio_path: Path to an audio file
        onset_threshold: Threshold for note onset detection
        frame_threshold: Threshold for frame-level pitch activation
        min_note_len: Minimum note length in milliseconds
        min_freq: Minimum frequency to detect (Hz)
        max_freq: Maximum frequency to detect (Hz)

    Returns:
        List of (start_time, end_time, midi_note, amplitude) tuples, sorted by
        start time. Amplitude is Basic Pitch's note activation in [0, 1].
    """
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except ImportError:
        raise ImportError(
            "basic-pitch not installed. Install with: pip install basic-pitch"
        )

    # predict(audio_path, model_or_model_path, ...) -> (model_output, midi, note_events)
    _, _, note_events = predict(
        str(audio_path),
        ICASSP_2022_MODEL_PATH,
        onset_threshold=onset_threshold,
        frame_threshold=frame_threshold,
        minimum_note_length=min_note_len,
        minimum_frequency=min_freq,
        maximum_frequency=max_freq,
    )

    # note_events: (start_time_s, end_time_s, pitch_midi, amplitude, pitch_bends)
    notes = [
        (float(event[0]), float(event[1]), int(event[2]), float(event[3]))
        for event in note_events
    ]
    notes.sort(key=lambda n: n[0])
    return notes


def detect_pitch_crepe(
    audio: np.ndarray,
    sr: int,
    model_capacity: str = 'tiny',
    step_size: int = 10,  # milliseconds
    confidence_threshold: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect pitch using CREPE (Convolutional Representation for Pitch Estimation).

    Args:
        audio: Audio samples (mono)
        sr: Sample rate
        model_capacity: Model size ('tiny', 'small', 'medium', 'large', 'full')
        step_size: Step size in milliseconds between frames
        confidence_threshold: Minimum confidence to include frame

    Returns:
        (times, frequencies, confidences) arrays
    """
    try:
        import crepe
    except ImportError:
        raise ImportError(
            "crepe not installed. Install with: pip install crepe"
        )

    time, frequency, confidence, _ = crepe.predict(
        audio,
        sr,
        model_capacity=model_capacity,
        viterbi=True,  # Viterbi smoothing for better pitch tracking
        step_size=step_size,
    )

    # Keep confident, voiced frames only
    mask = (confidence >= confidence_threshold) & (frequency > 50.0)
    return time[mask], frequency[mask], confidence[mask]


def detect_pitch_librosa(
    audio: np.ndarray,
    sr: int,
    fmin: float = 80.0,
    fmax: float = 1200.0,
    hop_length: int = 512,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect pitch using librosa's pyin algorithm (lightweight fallback).

    Args:
        audio: Audio samples (mono)
        sr: Sample rate
        fmin: Minimum frequency (Hz)
        fmax: Maximum frequency (Hz)
        hop_length: Hop length in samples

    Returns:
        (times, frequencies, confidences) arrays
    """
    import librosa

    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        hop_length=hop_length,
    )

    times = librosa.frames_to_time(
        np.arange(len(f0)),
        sr=sr,
        hop_length=hop_length,
    )

    # Drop unvoiced frames (NaN f0)
    valid_mask = ~np.isnan(f0) & voiced_flag
    return times[valid_mask], f0[valid_mask], voiced_probs[valid_mask]
