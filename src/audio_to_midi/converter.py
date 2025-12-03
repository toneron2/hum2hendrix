"""
Audio-to-MIDI Converter

Main conversion logic from audio waveform to MIDI file.
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
import mido
from mido import MidiFile, MidiTrack, Message


class AudioToMIDIConverter:
    """
    Converts audio files (hummed melodies) into MIDI files.

    Uses deep learning pitch detection (Basic Pitch or CREPE) to extract
    fundamental frequency contours and convert them to MIDI note events.
    """

    def __init__(
        self,
        model: str = 'basic_pitch',
        sample_rate: int = 22050,
        confidence_threshold: float = 0.5,
        min_note_duration: float = 0.1,
        onset_threshold: float = 0.5,
    ):
        """
        Initialize converter.

        Args:
            model: Pitch detection model ('basic_pitch' or 'crepe')
            sample_rate: Target sample rate for audio
            confidence_threshold: Minimum confidence for note detection (0-1)
            min_note_duration: Minimum note length in seconds
            onset_threshold: Threshold for note onset detection (0-1)
        """
        self.model = model
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self.min_note_duration = min_note_duration
        self.onset_threshold = onset_threshold

    def load_audio(self, audio_path: Path) -> Tuple[np.ndarray, int]:
        """
        Load and preprocess audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            (audio_samples, sample_rate) tuple
        """
        # Load audio with librosa
        audio, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True,
        )

        # Normalize audio to [-1, 1]
        if np.abs(audio).max() > 0:
            audio = audio / np.abs(audio).max()

        return audio, sr

    def detect_pitch(self, audio: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect pitch from audio using specified model.

        Args:
            audio: Audio samples
            sr: Sample rate

        Returns:
            (times, frequencies, confidences) arrays
        """
        if self.model == 'basic_pitch':
            from .pitch_detection import detect_pitch_basic_pitch
            return detect_pitch_basic_pitch(
                audio,
                sr,
                onset_threshold=self.onset_threshold,
                min_note_len=int(self.min_note_duration * 1000),  # ms
            )
        elif self.model == 'crepe':
            from .pitch_detection import detect_pitch_crepe
            return detect_pitch_crepe(
                audio,
                sr,
                confidence_threshold=self.confidence_threshold,
            )
        else:
            raise ValueError(f"Unknown model: {self.model}")

    def frequency_to_midi(self, frequency: float) -> int:
        """
        Convert frequency in Hz to MIDI note number.

        Args:
            frequency: Frequency in Hz

        Returns:
            MIDI note number (0-127)
        """
        if frequency <= 0:
            return 0

        # MIDI note number = 69 + 12*log2(f/440)
        midi_note = 69 + 12 * np.log2(frequency / 440.0)
        return int(np.round(np.clip(midi_note, 0, 127)))

    def notes_to_midi(
        self,
        notes: List[Tuple[float, float, int, float]],
        tempo: int = 120,
    ) -> MidiFile:
        """
        Convert note list to MIDI file.

        Args:
            notes: List of (start_time, duration, midi_note, velocity) tuples
            tempo: Tempo in BPM

        Returns:
            MidiFile object
        """
        # Create MIDI file
        mid = MidiFile(type=1)
        track = MidiTrack()
        mid.tracks.append(track)

        # Add tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))

        # Convert to MIDI events
        # We need to convert time to ticks
        ticks_per_beat = mid.ticks_per_beat
        ticks_per_second = ticks_per_beat * tempo / 60.0

        # Create note on/off events
        events = []
        for start_time, duration, midi_note, velocity in notes:
            start_tick = int(start_time * ticks_per_second)
            end_tick = int((start_time + duration) * ticks_per_second)

            events.append((start_tick, 'note_on', midi_note, velocity))
            events.append((end_tick, 'note_off', midi_note, 0))

        # Sort by time
        events.sort(key=lambda x: x[0])

        # Convert to delta times and add to track
        last_tick = 0
        for tick, msg_type, note, velocity in events:
            delta = tick - last_tick

            if msg_type == 'note_on':
                track.append(Message('note_on', note=note, velocity=int(velocity), time=delta))
            else:
                track.append(Message('note_off', note=note, velocity=0, time=delta))

            last_tick = tick

        return mid

    def convert(
        self,
        audio_path: Path,
        output_path: Path,
        tempo: int = 120,
    ) -> MidiFile:
        """
        Full conversion pipeline: audio → MIDI file.

        Args:
            audio_path: Input audio file path
            output_path: Output MIDI file path
            tempo: Tempo in BPM for MIDI file

        Returns:
            MidiFile object
        """
        # Load audio
        audio, sr = self.load_audio(audio_path)

        # Detect pitch
        times, frequencies, confidences = self.detect_pitch(audio, sr)

        # Filter by confidence
        mask = confidences >= self.confidence_threshold
        times = times[mask]
        frequencies = frequencies[mask]
        confidences = confidences[mask]

        # Convert to MIDI notes
        midi_notes = np.array([self.frequency_to_midi(f) for f in frequencies])

        # Segment into discrete notes
        notes = self._segment_notes(times, midi_notes, confidences)

        # Create MIDI file
        mid = self.notes_to_midi(notes, tempo=tempo)

        # Save
        mid.save(output_path)

        return mid

    def _segment_notes(
        self,
        times: np.ndarray,
        midi_notes: np.ndarray,
        confidences: np.ndarray,
    ) -> List[Tuple[float, float, int, float]]:
        """
        Segment continuous pitch contour into discrete notes.

        Args:
            times: Time array (seconds)
            midi_notes: MIDI note numbers
            confidences: Confidence scores

        Returns:
            List of (start_time, duration, midi_note, velocity) tuples
        """
        if len(times) == 0:
            return []

        notes = []
        current_note = None
        current_start = None

        for i, (time, note, conf) in enumerate(zip(times, midi_notes, confidences)):
            if current_note is None:
                # Start new note
                current_note = note
                current_start = time
            elif note != current_note:
                # Note changed, save previous
                duration = time - current_start
                if duration >= self.min_note_duration:
                    velocity = int(np.clip(conf * 127, 1, 127))
                    notes.append((current_start, duration, int(current_note), velocity))

                # Start new note
                current_note = note
                current_start = time

        # Add final note
        if current_note is not None:
            duration = times[-1] - current_start
            if duration >= self.min_note_duration:
                velocity = int(np.clip(confidences[-1] * 127, 1, 127))
                notes.append((current_start, duration, int(current_note), velocity))

        return notes
