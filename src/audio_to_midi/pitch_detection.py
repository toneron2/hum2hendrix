"""
Pitch Detection Wrappers

Interfaces to various pitch detection models (Basic Pitch, CREPE, etc.)
"""

import numpy as np
from typing import Tuple


def detect_pitch_basic_pitch(
    audio: np.ndarray,
    sr: int,
    onset_threshold: float = 0.5,
    frame_threshold: float = 0.3,
    min_note_len: int = 58,  # milliseconds
    min_freq: float = 80.0,  # Hz (E2)
    max_freq: float = 1200.0,  # Hz (D6)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect pitch using Spotify's Basic Pitch model.

    Args:
        audio: Audio samples (mono)
        sr: Sample rate
        onset_threshold: Threshold for note onset detection
        frame_threshold: Threshold for frame-level pitch activation
        min_note_len: Minimum note length in milliseconds
        min_freq: Minimum frequency to detect (Hz)
        max_freq: Maximum frequency to detect (Hz)

    Returns:
        (times, frequencies, confidences) arrays
    """
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except ImportError:
        raise ImportError(
            "basic-pitch not installed. Install with: pip install basic-pitch"
        )

    # Run Basic Pitch inference
    model_output, midi_data, note_events = predict(
        audio,
        sr,
        onset_threshold=onset_threshold,
        frame_threshold=frame_threshold,
        minimum_note_length=min_note_len,
        minimum_frequency=min_freq,
        maximum_frequency=max_freq,
        model_or_model_path=ICASSP_2022_MODEL_PATH,
    )

    # Extract note events
    # note_events format: List of (start_time, end_time, pitch_midi, amplitude)
    if len(note_events) == 0:
        return np.array([]), np.array([]), np.array([])

    times = []
    frequencies = []
    confidences = []

    for start_time, end_time, pitch_midi, amplitude, _ in note_events:
        # Convert MIDI pitch to frequency
        frequency = 440.0 * (2.0 ** ((pitch_midi - 69) / 12.0))

        # Use center time
        time = (start_time + end_time) / 2.0

        times.append(time)
        frequencies.append(frequency)
        confidences.append(amplitude)

    return (
        np.array(times),
        np.array(frequencies),
        np.array(confidences),
    )


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

    # Run CREPE inference
    time, frequency, confidence, activation = crepe.predict(
        audio,
        sr,
        model_capacity=model_capacity,
        viterbi=True,  # Use Viterbi smoothing for better pitch tracking
        step_size=step_size,
    )

    # Filter by confidence
    mask = confidence >= confidence_threshold
    time = time[mask]
    frequency = frequency[mask]
    confidence = confidence[mask]

    # Filter out unvoiced regions (very low frequencies)
    voiced_mask = frequency > 50.0
    time = time[voiced_mask]
    frequency = frequency[voiced_mask]
    confidence = confidence[voiced_mask]

    return time, frequency, confidence


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

    # Use librosa's pyin (probabilistic YIN)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=fmin,
        fmax=fmax,
        sr=sr,
        hop_length=hop_length,
    )

    # Create time array
    times = librosa.frames_to_time(
        np.arange(len(f0)),
        sr=sr,
        hop_length=hop_length,
    )

    # Filter NaN values and unvoiced regions
    valid_mask = ~np.isnan(f0) & voiced_flag
    times = times[valid_mask]
    frequencies = f0[valid_mask]
    confidences = voiced_probs[valid_mask]

    return times, frequencies, confidences
