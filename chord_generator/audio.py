"""Render chord progressions to MIDI using midiutil."""

from typing import List

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
