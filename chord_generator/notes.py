"""Note representation and pitch conversion."""

import re
from dataclasses import dataclass

NOTE_TO_PC = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
    'A#': 10, 'Bb': 10, 'B': 11,
}

PC_TO_NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@dataclass
class Note:
    pitch: str  # e.g., "C4", "Eb5"
    start_beat: float
    duration: float
    velocity: int = 80

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration

    def __str__(self):
        return f"{self.pitch} (beat {self.start_beat:.1f}, dur {self.duration:.1f})"


def pitch_to_midi(pitch: str):
    """Convert a note string like 'C4' or 'Eb5' to a MIDI number, or None."""
    match = re.match(r'^([A-G][#b]?)(-?\d+)$', pitch)
    if not match:
        return None
    pc = NOTE_TO_PC.get(match.group(1))
    if pc is None:
        return None
    return (int(match.group(2)) + 1) * 12 + pc


def midi_to_pitch(midi: int) -> str:
    """Convert a MIDI number to a note string, spelling black keys with sharps."""
    return f"{PC_TO_NOTE[midi % 12]}{midi // 12 - 1}"
