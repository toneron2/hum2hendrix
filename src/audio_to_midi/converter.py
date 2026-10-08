"""
Audio-to-MIDI Converter

Main conversion logic from audio waveform to MIDI file.
"""

import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

import mido
import numpy as np
from mido import Message, MidiFile, MidiTrack

from .pitch_detection import NoteEvent

# (start_time, duration, midi_note, velocity)
Note = Tuple[float, float, int, int]

NOTE_MODELS = ('basic_pitch',)
CONTOUR_MODELS = ('crepe', 'librosa')


class AudioToMIDIConverter:
    """
    Converts audio files (hummed melodies) into MIDI files.

    Supports Basic Pitch (note detector) and CREPE or librosa pyin (contour
    detectors). Contour output is segmented into notes by `segment_notes`.
    """

    def __init__(
        self,
        model: str = 'basic_pitch',
        sample_rate: int = 22050,
        confidence_threshold: float = 0.5,
        min_note_duration: float = 0.1,
        onset_threshold: float = 0.5,
        normalize: bool = True,
    ):
        """
        Initialize converter.

        Args:
            model: Pitch detection model ('basic_pitch', 'crepe' or 'librosa')
            sample_rate: Target sample rate for audio
            confidence_threshold: Minimum confidence for note detection (0-1).
                For Basic Pitch this filters on the note amplitude.
            min_note_duration: Minimum note length in seconds
            onset_threshold: Threshold for note onset detection (0-1, Basic Pitch)
            normalize: Peak-normalize audio to [-1, 1] before detection
        """
        if model not in NOTE_MODELS + CONTOUR_MODELS:
            raise ValueError(
                f"Unknown model: {model!r}. "
                f"Choose from {', '.join(NOTE_MODELS + CONTOUR_MODELS)}"
            )
        self.model = model
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self.min_note_duration = min_note_duration
        self.onset_threshold = onset_threshold
        self.normalize = normalize

    def load_audio(self, audio_path: Path) -> Tuple[np.ndarray, int]:
        """
        Load and preprocess audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            (audio_samples, sample_rate) tuple
        """
        import librosa  # heavy import; only needed when loading audio

        audio, sr = librosa.load(
            str(audio_path),
            sr=self.sample_rate,
            mono=True,
        )

        if self.normalize:
            peak = np.abs(audio).max()
            if peak > 0:
                audio = audio / peak

        return audio, sr

    def detect_notes(self, audio: np.ndarray, sr: int) -> List[NoteEvent]:
        """
        Run a note detector (Basic Pitch) on audio samples.

        Basic Pitch reads from a file, so the (possibly normalized and
        resampled) samples are written to a temporary WAV first.

        Returns:
            List of (start_time, end_time, midi_note, amplitude) tuples
        """
        import soundfile as sf

        from .pitch_detection import detect_notes_basic_pitch

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_wav = Path(tmp_dir) / 'input.wav'
            sf.write(tmp_wav, audio, sr)
            return detect_notes_basic_pitch(
                tmp_wav,
                onset_threshold=self.onset_threshold,
                min_note_len=self.min_note_duration * 1000.0,  # ms
            )

    def detect_pitch(self, audio: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Run a contour detector (CREPE or librosa pyin) on audio samples.

        Returns:
            (times, frequencies, confidences) arrays
        """
        if self.model == 'crepe':
            from .pitch_detection import detect_pitch_crepe
            return detect_pitch_crepe(
                audio,
                sr,
                confidence_threshold=self.confidence_threshold,
            )
        if self.model == 'librosa':
            from .pitch_detection import detect_pitch_librosa
            return detect_pitch_librosa(audio, sr)
        raise ValueError(f"{self.model!r} is not a contour model")

    @staticmethod
    def frequency_to_midi(frequency: float) -> int:
        """
        Convert frequency in Hz to MIDI note number.

        Args:
            frequency: Frequency in Hz

        Returns:
            MIDI note number (0-127)
        """
        if frequency <= 0:
            return 0
        return int(AudioToMIDIConverter.frequencies_to_midi(np.array([frequency]))[0])

    @staticmethod
    def frequencies_to_midi(frequencies: np.ndarray) -> np.ndarray:
        """
        Vectorised Hz -> MIDI note number conversion.

        Non-positive frequencies map to 0.
        """
        frequencies = np.asarray(frequencies, dtype=float)
        midi = np.zeros(frequencies.shape, dtype=int)
        positive = frequencies > 0
        # MIDI note number = 69 + 12*log2(f/440)
        midi[positive] = np.round(
            np.clip(69 + 12 * np.log2(frequencies[positive] / 440.0), 0, 127)
        ).astype(int)
        return midi

    def notes_to_midi(
        self,
        notes: List[Note],
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
        mid = MidiFile(type=1)
        track = MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))

        ticks_per_second = mid.ticks_per_beat * tempo / 60.0

        # (tick, order, type, note, velocity); note_off sorts before note_on at
        # the same tick so back-to-back notes of one pitch don't overlap.
        events = []
        for start_time, duration, midi_note, velocity in notes:
            start_tick = int(round(start_time * ticks_per_second))
            end_tick = int(round((start_time + duration) * ticks_per_second))
            end_tick = max(end_tick, start_tick + 1)

            events.append((start_tick, 1, 'note_on', midi_note, int(velocity)))
            events.append((end_tick, 0, 'note_off', midi_note, 0))

        events.sort(key=lambda e: (e[0], e[1]))

        last_tick = 0
        for tick, _, msg_type, note, velocity in events:
            track.append(Message(msg_type, note=note, velocity=velocity, time=tick - last_tick))
            last_tick = tick

        return mid

    def convert(
        self,
        audio_path: Path,
        output_path: Path,
        tempo: int = 120,
    ) -> MidiFile:
        """
        Full conversion pipeline: audio -> MIDI file.

        Args:
            audio_path: Input audio file path
            output_path: Output MIDI file path
            tempo: Tempo in BPM for MIDI file

        Returns:
            MidiFile object
        """
        audio, sr = self.load_audio(audio_path)

        if self.model in NOTE_MODELS:
            events = self.detect_notes(audio, sr)
            notes = self.note_events_to_notes(events)
        else:
            times, frequencies, confidences = self.detect_pitch(audio, sr)

            mask = confidences >= self.confidence_threshold
            times, frequencies, confidences = times[mask], frequencies[mask], confidences[mask]

            midi_notes = self.frequencies_to_midi(frequencies)
            notes = self.segment_notes(times, midi_notes, confidences)

        mid = self.notes_to_midi(notes, tempo=tempo)
        mid.save(str(output_path))
        return mid

    def note_events_to_notes(self, events: List[NoteEvent]) -> List[Note]:
        """
        Convert detector note events into the converter's note tuples.

        Applies the confidence (amplitude) and minimum-duration filters.

        Args:
            events: (start_time, end_time, midi_note, amplitude) tuples

        Returns:
            List of (start_time, duration, midi_note, velocity) tuples
        """
        notes = []
        for start, end, midi_note, amplitude in events:
            duration = end - start
            if amplitude < self.confidence_threshold or duration < self.min_note_duration:
                continue
            notes.append((float(start), float(duration), int(midi_note), _velocity(amplitude)))
        notes.sort(key=lambda n: n[0])
        return notes

    def segment_notes(
        self,
        times: np.ndarray,
        midi_notes: np.ndarray,
        confidences: np.ndarray,
        max_gap: Optional[float] = None,
    ) -> List[Note]:
        """
        Segment a frame-wise pitch contour into discrete notes.

        A note ends when the MIDI pitch changes or when the gap between
        consecutive voiced frames exceeds `max_gap` (a rest). Velocity is the
        mean confidence over the note's own frames.

        Args:
            times: Frame times (seconds), ascending
            midi_notes: MIDI note number per frame
            confidences: Confidence per frame
            max_gap: Largest silence (seconds) still bridged inside one note.
                Defaults to 2.5 frame periods.

        Returns:
            List of (start_time, duration, midi_note, velocity) tuples
        """
        if len(times) == 0:
            return []

        times = np.asarray(times, dtype=float)
        if len(times) > 1:
            frame_period = float(np.median(np.diff(times)))
        else:
            frame_period = self.min_note_duration
        if max_gap is None:
            max_gap = 2.5 * frame_period

        notes: List[Note] = []
        start_idx = 0

        def flush(end_idx: int, end_time: float) -> None:
            """Emit frames [start_idx, end_idx) as one note ending at end_time."""
            start = times[start_idx]
            duration = end_time - start
            if duration >= self.min_note_duration:
                conf = float(np.mean(confidences[start_idx:end_idx]))
                notes.append((float(start), float(duration), int(midi_notes[start_idx]), _velocity(conf)))

        for i in range(1, len(times)):
            gap = times[i] - times[i - 1]
            if gap > max_gap:
                # Rest: close the note one frame after its last voiced frame
                flush(i, times[i - 1] + frame_period)
                start_idx = i
            elif midi_notes[i] != midi_notes[start_idx]:
                flush(i, times[i])
                start_idx = i

        flush(len(times), times[-1] + frame_period)
        return notes

    # Backwards-compatible alias
    _segment_notes = segment_notes


def _velocity(confidence: float) -> int:
    """Map a 0-1 confidence/amplitude to a MIDI velocity in 1-127."""
    return int(np.clip(round(confidence * 127), 1, 127))
