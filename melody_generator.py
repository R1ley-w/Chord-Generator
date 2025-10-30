import random
from typing import List, Dict
from dataclasses import dataclass

from JazzChord import JazzChord
from Phrase_Analysis import Note

@dataclass
class ChordTone:
    note: str
    weight: float  # How important this tone is for melody

class MelodyGenerator:
    """Generates jazz-style melodies that follow chord progressions"""
    
    def __init__(self):
        # Chord tone mappings (simplified - in practice you'd want more comprehensive)
        self.chord_tones = {
            "maj7": [
                ChordTone("1", 0.3),   # Root
                ChordTone("3", 0.4),   # Major 3rd
                ChordTone("5", 0.2),   # Perfect 5th
                ChordTone("7", 0.1),   # Major 7th
            ],
            "m7": [
                ChordTone("1", 0.3),   # Root
                ChordTone("3", 0.4),   # Minor 3rd
                ChordTone("5", 0.2),   # Perfect 5th
                ChordTone("7", 0.1),   # Minor 7th
            ],
            "7": [
                ChordTone("1", 0.25),  # Root
                ChordTone("3", 0.35),  # Major 3rd
                ChordTone("5", 0.15),  # Perfect 5th
                ChordTone("7", 0.25),  # Dominant 7th
            ],
            "m7b5": [
                ChordTone("1", 0.3),   # Root
                ChordTone("3", 0.3),   # Minor 3rd
                ChordTone("5", 0.2),   # Diminished 5th
                ChordTone("7", 0.2),   # Minor 7th
            ]
        }
        
        # Available tensions for each chord type
        self.available_tensions = {
            "maj7": ["9", "#11", "13"],
            "m7": ["9", "11", "13"],
            "7": ["b9", "9", "#9", "#11", "13"],
            "m7b5": ["9", "11", "b13"]
        }
        
        # Scale degrees to note names (C major reference)
        self.scale_degrees = {
            "1": 0, "b2": 1, "2": 2, "b3": 3, "3": 4, "4": 5,
            "b5": 6, "5": 7, "#5": 8, "6": 9, "b7": 10, "7": 11,
            "b9": 1, "9": 2, "#9": 3, "11": 5, "#11": 6, "b13": 8, "13": 9
        }
        
        # Common jazz rhythmic patterns (in beats)
        self.rhythmic_patterns = [
            [1.0, 1.0, 1.0, 1.0],  # Quarter notes
            [0.5, 0.5, 1.0, 2.0],  # Eighth notes with longer note
            [2.0, 1.0, 0.5, 0.5],  # Starting with longer note
            [1.5, 0.5, 1.0, 1.0],  # Dotted rhythm
            [0.5, 0.5, 0.5, 0.5, 1.0, 1.0],  # More active
        ]
    
    def create_melody_for_progression(self, progression: List[JazzChord], 
                                    style: str = "bebop") -> List[Note]:
        """
        Create a jazz-style melody that follows a chord progression
        
        Args:
            progression: List of JazzChord objects
            style: "bebop", "ballad", "latin", "blues"
        """
        melody_notes = []
        current_beat = 0.0
        
        for i, chord in enumerate(progression):
            # Determine how many notes for this chord (typically 2-8 notes per chord)
            notes_per_chord = self._get_notes_per_chord(style, i, len(progression))
            
            # Get rhythmic pattern for this chord
            rhythm_pattern = self._get_rhythm_pattern(style, notes_per_chord)
            
            # Generate notes for this chord
            chord_notes = self._generate_notes_for_chord(
                chord, rhythm_pattern, current_beat, style, 
                previous_note=melody_notes[-1] if melody_notes else None
            )
            
            melody_notes.extend(chord_notes)
            current_beat += 4.0  # Assume 4 beats per chord (common in jazz)
        
        return melody_notes
    
    def _get_notes_per_chord(self, style: str, chord_index: int, total_chords: int) -> int:
        """Determine how many melody notes to generate for a chord"""
        base_notes = {
            "bebop": random.randint(6, 10),     # Dense, fast-moving
            "ballad": random.randint(2, 5),     # Sparse, lyrical
            "latin": random.randint(4, 7),      # Moderate density
            "blues": random.randint(3, 6),      # Blues phrasing
        }[style]
        
        # Fewer notes at phrase boundaries
        if chord_index == 0 or chord_index == total_chords - 1:
            return max(2, base_notes - 2)
        
        return base_notes
    
    def _get_rhythm_pattern(self, style: str, num_notes: int) -> List[float]:
        """Get rhythmic pattern based on style"""
        if style == "bebop":
            # Dense, syncopated rhythms
            patterns = [[0.5] * min(8, num_notes), [0.25, 0.25, 0.5, 1.0]]
        elif style == "ballad":
            # Longer, sustained notes
            patterns = [[2.0, 2.0], [1.0, 1.0, 2.0], [3.0, 1.0]]
        elif style == "latin":
            # Syncopated but not too dense
            patterns = [[1.0, 0.5, 0.5, 2.0], [0.5, 1.5, 1.0, 1.0]]
        else:  # blues
            patterns = [[1.0, 1.0, 2.0], [0.5, 1.5, 1.0, 1.0]]
        
        pattern = random.choice(patterns)
        
        # Adjust pattern length to match requested number of notes
        while len(pattern) < num_notes:
            pattern.extend(pattern)
        
        return pattern[:num_notes]
    
    def _generate_notes_for_chord(self, chord: JazzChord, rhythm_pattern: List[float], 
                                start_beat: float, style: str, 
                                previous_note: Note = None) -> List[Note]:
        """Generate melody notes for a specific chord"""
        notes = []
        current_beat = start_beat
        
        # Choose target octave (typically 4-5 for jazz melodies)
        base_octave = 4 if style == "ballad" else 5
        
        previous_pitch = None
        if previous_note:
            previous_pitch = self._pitch_to_midi(previous_note.pitch)
        
        for duration in rhythm_pattern:
            # Choose between chord tone and tension
            if random.random() < 0.7:  # 70% chance of chord tone
                pitch = self._get_chord_tone(chord, base_octave)
            else:
                pitch = self._get_available_tension(chord, base_octave)
            
            # Smooth voice leading - avoid large leaps if possible
            if previous_pitch is not None:
                pitch = self._smooth_voice_leading(previous_pitch, pitch, style)
            
            # Add some rhythmic variation
            actual_duration = duration * random.uniform(0.9, 1.1)
            
            note = Note(
                pitch=self._midi_to_pitch(pitch),
                start_beat=current_beat,
                duration=actual_duration,
                velocity=random.randint(70, 100)
            )
            
            notes.append(note)
            current_beat += duration
            previous_pitch = pitch
        
        return notes
    
    def _get_chord_tone(self, chord: JazzChord, base_octave: int) -> int:
        """Get a chord tone for the given chord"""
        chord_type = chord.quality
        if chord_type not in self.chord_tones:
            chord_type = "maj7"  # Default fallback
        
        tones = self.chord_tones[chord_type]
        
        # Weighted random choice based on importance
        weights = [tone.weight for tone in tones]
        chosen_tone = random.choices(tones, weights=weights)[0]
        
        return self._scale_degree_to_midi(chord.root, chosen_tone.note, base_octave)
    
    def _get_available_tension(self, chord: JazzChord, base_octave: int) -> int:
        """Get an available tension note for the chord"""
        chord_type = chord.quality
        if chord_type not in self.available_tensions:
            # Fallback to common tensions
            tensions = ["9", "13"]
        else:
            tensions = self.available_tensions[chord_type]
        
        chosen_tension = random.choice(tensions)
        return self._scale_degree_to_midi(chord.root, chosen_tension, base_octave)
    
    def _scale_degree_to_midi(self, root: str, degree: str, base_octave: int) -> int:
        """Convert scale degree to MIDI note number"""
        # Root note to MIDI (simplified)
        root_midi = {
            'C': 60, 'Db': 61, 'D': 62, 'Eb': 63, 'E': 64, 'F': 65,
            'Gb': 66, 'G': 67, 'Ab': 68, 'A': 69, 'Bb': 70, 'B': 71
        }[root]
        
        degree_offset = self.scale_degrees[degree]
        return root_midi + degree_offset
    
    def _smooth_voice_leading(self, previous_pitch: int, current_pitch: int, 
                            style: str) -> int:
        """Adjust pitch to create smooth voice leading"""
        interval = abs(current_pitch - previous_pitch)
        
        # Maximum allowed leap based on style
        max_leap = {
            "bebop": 12,    # Bebop allows larger leaps
            "ballad": 8,    # Ballads prefer stepwise motion
            "latin": 10,    # Moderate leaps
            "blues": 9,     # Blues allows some leaps
        }[style]
        
        if interval > max_leap:
            # Adjust to nearest octave equivalent
            if current_pitch > previous_pitch:
                current_pitch -= 12
            else:
                current_pitch += 12
        
        # Ensure we're in a reasonable melodic range
        if current_pitch < 48:  # Too low
            current_pitch += 12
        elif current_pitch > 84:  # Too high
            current_pitch -= 12
            
        return current_pitch
    
    def _pitch_to_midi(self, pitch: str) -> int:
        """Convert pitch string to MIDI note number"""
        pitch_map = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        
        note_name = ''.join([c for c in pitch if not c.isdigit()])
        octave = int(''.join([c for c in pitch if c.isdigit()]))
        
        note_value = pitch_map.get(note_name, 0)
        return (octave + 1) * 12 + note_value
    
    def _midi_to_pitch(self, midi_note: int) -> str:
        """Convert MIDI note number to pitch string"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_name = note_names[midi_note % 12]
        return f"{note_name}{octave}"

# Simplified version for immediate use
def create_melody_for_progression(progression: List[JazzChord], 
                                style: str = "bebop") -> List[Note]:
    """
    Create a jazz-style melody that follows a chord progression
    
    Args:
        progression: List of JazzChord objects
        style: "bebop", "ballad", "latin", "blues"
    
    Returns:
        List of Note objects that form a melody
    """
    generator = MelodyGenerator()
    return generator.create_melody_for_progression(progression, style)

# Example usage and demonstration
def demo_melody_generation():
    """Demonstrate melody generation for different progressions"""
    print("=== Jazz Melody Generation Demo ===\n")
    
    # Sample chord progressions
    progressions = [
        [JazzChord("C", "maj7"), JazzChord("A", "m7"), JazzChord("D", "m7"), JazzChord("G", "7")],
        [JazzChord("F", "maj7"), JazzChord("D", "m7"), JazzChord("G", "m7"), JazzChord("C", "7")],
        [JazzChord("D", "m7"), JazzChord("G", "7"), JazzChord("C", "maj7"), JazzChord("C", "maj7")],
    ]
    
    styles = ["bebop", "ballad", "latin", "blues"]
    
    for i, progression in enumerate(progressions):
        print(f"\n--- Progression {i + 1}: {' | '.join(str(c) for c in progression)} ---")
        
        for style in styles:
            melody = create_melody_for_progression(progression, style)
            print(f"\n{style.upper()} style melody:")
            for note in melody[:8]:  # Show first 8 notes
                print(f"  {note}")
            if len(melody) > 8:
                print(f"  ... and {len(melody) - 8} more notes")

if __name__ == "__main__":
    demo_melody_generation()