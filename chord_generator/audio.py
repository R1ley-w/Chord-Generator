"""Render chord progressions to MIDI and to audio (MP3 via FluidSynth)."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from midi2audio import DEFAULT_SOUND_FONT, FluidSynth
from midiutil import MIDIFile

from .chords import JazzChord

_NOTE_TO_PC = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
    'A#': 10, 'Bb': 10, 'B': 11,
}

_CHORD_TONES = {
    'maj7': [0, 4, 7, 11],
    'm7': [0, 3, 7, 10],
    '7': [0, 4, 7, 10],
    'm7b5': [0, 3, 6, 10],
    'dim7': [0, 3, 6, 9],
    '7sus4': [0, 5, 7, 10],
    '7sus2': [0, 2, 7, 10],
}

_EXTENSION_INTERVALS = {
    'b9': 13, '9': 14, '#9': 15, '11': 17, '#11': 18, 'b13': 20, '13': 21,
}

_BASS_OCTAVE = 3
_CHORD_OCTAVE = 4
_EXTENSION_OCTAVE = 5


def _pitch_class(root: str) -> int:
    return _NOTE_TO_PC.get(root, 0)


def _chord_notes(chord: JazzChord) -> List[int]:
    """Return the MIDI notes for a simple voicing of a chord."""
    root_pc = _pitch_class(chord.root)

    notes = [(_BASS_OCTAVE + 1) * 12 + root_pc]

    for interval in _CHORD_TONES.get(chord.quality, [0, 4, 7]):
        notes.append((_CHORD_OCTAVE + 1) * 12 + root_pc + interval)

    for extension in chord.extensions:
        interval = _EXTENSION_INTERVALS.get(extension)
        if interval is not None:
            notes.append((_EXTENSION_OCTAVE + 1) * 12 + root_pc + interval)

    return notes


def render_progression_to_midi(progression, filepath: str,
                               tempo: int = 120, program: int = 0,
                               volume: int = 100) -> str:
    """Write a progression of ``ChordWithDuration`` objects to a MIDI file.

    Each chord is voiced (bass + closed-position chord tones + extensions) and
    held for its full duration. Returns ``filepath``.
    """
    midi = MIDIFile(1)
    track = 0
    channel = 0
    midi.addTempo(track, 0, tempo)
    midi.addProgramChange(track, channel, 0, program)

    for item in progression:
        for pitch in _chord_notes(item.chord):
            midi.addNote(track, channel, pitch, item.start_beat, item.duration, volume)

    with open(filepath, 'wb') as f:
        midi.writeFile(f)

    return filepath


# SoundFont resolution: an explicit path, an env var, a project-local
# data/soundfonts/ directory, or midi2audio's default location.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SOUNDFONT_DIR = _DATA_DIR / "soundfonts"
_SOUNDFONT_NAMES = ["FluidR3_GM.sf2", "GeneralUser GS v1.471.sf2", "TimGM6mb.sf2", "gm.sf2"]


class _FluidSynth(FluidSynth):
    """midi2audio's FluidSynth, fixed for fluidsynth >= 2.x argument order.

    midi2audio places ``-F``/``-r`` after the soundfont and midifile, which
    fluidsynth 2.x rejects. The options must precede the positional arguments.
    """

    def midi_to_audio(self, midi_file: str, audio_file: str) -> None:
        subprocess.run(
            ["fluidsynth", "-ni", "-F", audio_file, "-r", str(self.sample_rate),
             self.sound_font, midi_file],
            check=True, capture_output=True,
        )


def find_soundfont(explicit_path: str = None) -> str:
    """Return the path to an available SoundFont, or raise FileNotFoundError."""
    if explicit_path:
        if Path(explicit_path).exists():
            return str(explicit_path)
        raise FileNotFoundError(f"SoundFont not found: {explicit_path}")

    env = os.environ.get("CHORD_GENERATOR_SOUNDFONT")
    if env and Path(env).exists():
        return env

    if _SOUNDFONT_DIR.exists():
        for name in _SOUNDFONT_NAMES:
            candidate = _SOUNDFONT_DIR / name
            if candidate.exists():
                return str(candidate)
        for candidate in sorted(_SOUNDFONT_DIR.glob("*.sf2")):
            return str(candidate)

    default = Path(os.path.expanduser(DEFAULT_SOUND_FONT))
    if default.exists():
        return str(default)

    raise FileNotFoundError(
        "No SoundFont found. Place a .sf2 file in data/soundfonts/ (e.g. "
        "TimGM6mb.sf2) or set the CHORD_GENERATOR_SOUNDFONT environment variable."
    )


def _new_temp_path(suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="progression_")
    os.close(fd)
    return path


def _find_mp3_encoder() -> str:
    return shutil.which("lame") or shutil.which("ffmpeg")


def _encode_mp3(encoder: str, wav_path: str, mp3_path: str, bitrate: str) -> None:
    if encoder.endswith("lame"):
        subprocess.run([encoder, "--silent", "-b", bitrate, wav_path, mp3_path], check=True)
    else:  # ffmpeg
        subprocess.run(
            [encoder, "-y", "-loglevel", "error", "-i", wav_path,
             "-codec:a", "libmp3lame", "-b:a", f"{bitrate}k", mp3_path],
            check=True,
        )


def render_midi_to_mp3(midi_path: str, sound_font: str = None,
                       sample_rate: int = 44100, bitrate: str = "192") -> str:
    """Synthesize a MIDI file to MP3 and return the output file path.

    MIDI is rendered to WAV with FluidSynth (via midi2audio) and then encoded to
    MP3 with ``lame`` (or ``ffmpeg``). If no MP3 encoder is installed the WAV
    file is returned instead so playback still works.
    """
    sf = find_soundfont(sound_font)

    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_path = os.path.join(tmp_dir, "render.wav")
        _FluidSynth(sound_font=sf, sample_rate=sample_rate).midi_to_audio(midi_path, wav_path)

        encoder = _find_mp3_encoder()
        if encoder:
            out_path = _new_temp_path(".mp3")
            _encode_mp3(encoder, wav_path, out_path, bitrate)
        else:
            out_path = _new_temp_path(".wav")
            shutil.copyfile(wav_path, out_path)

    return out_path
