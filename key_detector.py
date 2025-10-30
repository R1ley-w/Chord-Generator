import math
import random
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter
import numpy as np

from JazzChord import JazzChord
from Markov_Chain_For_Chords import MarkovChain, JazzChord
from Phrase_Analysis import Note

class ScaleType(Enum):
    MAJOR = "major"
    NATURAL_MINOR = "natural_minor"
    HARMONIC_MINOR = "harmonic_minor"
    MELODIC_MINOR = "melodic_minor"
    DORIAN = "dorian"
    MIXOLYDIAN = "mixolydian"
    LYDIAN = "lydian"
    PHRYGIAN = "phrygian"
    LOCRIAN = "locrian"
    BLUES = "blues"

@dataclass
class Key:
    tonic: str  # e.g., "C", "F#", "Bb"
    scale_type: ScaleType
    confidence: float = 0.0
    
    def __str__(self):
        return f"{self.tonic} {self.scale_type.value}"

class ScaleDetector:
    """Detects musical key and scale from a collection of notes"""
    
    def __init__(self):
        # Note to index mapping
        self.note_indices = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        
        # Index to note names (prefer sharps for some, flats for others)
        self.index_notes = {
            0: 'C', 1: 'C#', 2: 'D', 3: 'Eb', 4: 'E', 5: 'F',
            6: 'F#', 7: 'G', 8: 'Ab', 9: 'A', 10: 'Bb', 11: 'B'
        }
        
        # Scale patterns (semitone intervals from tonic)
        self.scale_patterns = {
            ScaleType.MAJOR: [2, 2, 1, 2, 2, 2, 1],
            ScaleType.NATURAL_MINOR: [2, 1, 2, 2, 1, 2, 2],
            ScaleType.HARMONIC_MINOR: [2, 1, 2, 2, 1, 3, 1],
            ScaleType.MELODIC_MINOR: [2, 1, 2, 2, 2, 2, 1],
            ScaleType.DORIAN: [2, 1, 2, 2, 2, 1, 2],
            ScaleType.MIXOLYDIAN: [2, 2, 1, 2, 2, 1, 2],
            ScaleType.LYDIAN: [2, 2, 2, 1, 2, 2, 1],
            ScaleType.PHRYGIAN: [1, 2, 2, 2, 1, 2, 2],
            ScaleType.LOCRIAN: [1, 2, 2, 1, 2, 2, 2],
            ScaleType.BLUES: [3, 2, 1, 1, 3, 2]  # Blues scale (6 notes)
        }
        
        # Common jazz scales and their typical contexts
        self.jazz_scale_preferences = {
            ScaleType.MAJOR: 1.0,
            ScaleType.DORIAN: 0.9,        # Common for minor chords
            ScaleType.MIXOLYDIAN: 0.9,    # Common for dominant chords
            ScaleType.MELODIC_MINOR: 0.8,
            ScaleType.HARMONIC_MINOR: 0.7,
            ScaleType.LYDIAN: 0.6,        # For maj7#11
            ScaleType.BLUES: 0.8,         # Blues contexts
            ScaleType.NATURAL_MINOR: 0.5,
            ScaleType.PHRYGIAN: 0.3,
            ScaleType.LOCRIAN: 0.2
        }
    
    def detect_key(self, notes: List[Note], method: str = "krumhansl") -> Key:
        """
        Detect the most likely key from a collection of notes
        
        Args:
            notes: List of Note objects
            method: "krumhansl", "simple", or "correlation"
        """
        if not notes:
            return Key("C", ScaleType.MAJOR, 0.0)
        
        # Convert notes to pitch classes
        pitch_classes = self._extract_pitch_classes(notes)
        
        if method == "krumhansl":
            return self._krumhansl_schmuckler(pitch_classes)
        elif method == "simple":
            return self._simple_key_detection(pitch_classes)
        else:
            return self._correlation_method(pitch_classes)
    
    def _extract_pitch_classes(self, notes: List[Note]) -> List[int]:
        """Extract pitch classes (0-11) from notes, weighted by duration"""
        pitch_classes = []
        
        for note in notes:
            midi_note = self._pitch_to_midi(note.pitch)
            pitch_class = midi_note % 12
            
            # Weight by duration (longer notes are more important for key)
            weight = int(note.duration * 2)  # Convert duration to weight
            pitch_classes.extend([pitch_class] * weight)
        
        return pitch_classes
    
    def _pitch_to_midi(self, pitch: str) -> int:
        """Convert pitch string to MIDI note number"""
        note_name = ''.join([c for c in pitch if not c.isdigit()])
        octave = int(''.join([c for c in pitch if c.isdigit()]))
        
        note_value = self.note_indices.get(note_name, 0)
        return (octave + 1) * 12 + note_value
    
    def _krumhansl_schmuckler(self, pitch_classes: List[int]) -> Key:
        """
        Implement Krumhansl-Schmuckler key-finding algorithm
        Uses probe tone profiles for major and minor keys
        """
        # Krumhansl's key profiles (from perceptual studies)
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        # Normalize profiles
        major_profile = [x / sum(major_profile) for x in major_profile]
        minor_profile = [x / sum(minor_profile) for x in minor_profile]
        
        # Get pitch class distribution
        pc_distribution = self._get_pitch_class_distribution(pitch_classes)
        
        best_key = None
        best_correlation = -1.0
        best_scale_type = None
        
        # Test all 12 major and 12 minor keys
        for tonic in range(12):
            # Test major key
            major_corr = self._correlate_with_profile(pc_distribution, major_profile, tonic)
            if major_corr > best_correlation:
                best_correlation = major_corr
                best_key = tonic
                best_scale_type = ScaleType.MAJOR
            
            # Test minor key
            minor_corr = self._correlate_with_profile(pc_distribution, minor_profile, tonic)
            if minor_corr > best_correlation:
                best_correlation = minor_corr
                best_key = tonic
                best_scale_type = ScaleType.NATURAL_MINOR
        
        # Apply jazz scale preferences
        best_scale_type = self._apply_jazz_preferences(best_scale_type, pitch_classes)
        
        return Key(
            tonic=self.index_notes[best_key],
            scale_type=best_scale_type,
            confidence=best_correlation
        )
    
    def _get_pitch_class_distribution(self, pitch_classes: List[int]) -> List[float]:
        """Get normalized distribution of pitch classes"""
        if not pitch_classes:
            return [0.0] * 12
        
        counts = [0] * 12
        for pc in pitch_classes:
            counts[pc] += 1
        
        total = sum(counts)
        return [count / total for count in counts]
    
    def _correlate_with_profile(self, distribution: List[float], 
                              profile: List[float], shift: int) -> float:
        """Calculate correlation between distribution and shifted profile"""
        correlation = 0.0
        for i in range(12):
            profile_index = (i - shift) % 12
            correlation += distribution[i] * profile[profile_index]
        
        return correlation
    
    def _apply_jazz_preferences(self, detected_scale: ScaleType, 
                              pitch_classes: List[int]) -> ScaleType:
        """Adjust scale type based on jazz context and note content"""
        if detected_scale == ScaleType.NATURAL_MINOR:
            # In jazz, dorian is often preferred over natural minor
            if self._has_minor_sixth(pitch_classes):
                return ScaleType.DORIAN
            elif self._has_major_seventh(pitch_classes):
                return ScaleType.MELODIC_MINOR
            elif self._has_augmented_second(pitch_classes):
                return ScaleType.HARMONIC_MINOR
        
        elif detected_scale == ScaleType.MAJOR:
            # Check for lydian (#4) or mixolydian (b7) characteristics
            if self._has_raised_fourth(pitch_classes):
                return ScaleType.LYDIAN
            elif self._has_flatted_seventh(pitch_classes):
                return ScaleType.MIXOLYDIAN
        
        return detected_scale
    
    def _has_minor_sixth(self, pitch_classes: List[int]) -> bool:
        """Check if the melody suggests a minor 6th (characteristic of dorian)"""
        return any(pc == 8 for pc in pitch_classes)  # Minor 6th is 8 semitones above tonic
    
    def _has_major_seventh(self, pitch_classes: List[int]) -> bool:
        """Check for major 7th (characteristic of melodic minor)"""
        return any(pc == 11 for pc in pitch_classes)
    
    def _has_augmented_second(self, pitch_classes: List[int]) -> bool:
        """Check for augmented 2nd (characteristic of harmonic minor)"""
        # Between minor 3rd and perfect 4th
        return any(pc == 3 for pc in pitch_classes) and any(pc == 6 for pc in pitch_classes)
    
    def _has_raised_fourth(self, pitch_classes: List[int]) -> bool:
        """Check for raised 4th (characteristic of lydian)"""
        return any(pc == 6 for pc in pitch_classes)  # #4 is 6 semitones above tonic
    
    def _has_flatted_seventh(self, pitch_classes: List[int]) -> bool:
        """Check for flatted 7th (characteristic of mixolydian)"""
        return any(pc == 10 for pc in pitch_classes)  # b7 is 10 semitones above tonic
    
    def _simple_key_detection(self, pitch_classes: List[int]) -> Key:
        """Simple key detection based on note frequency and circle of fifths"""
        if not pitch_classes:
            return Key("C", ScaleType.MAJOR, 0.0)
        
        # Count occurrences of each pitch class
        pc_counter = Counter(pitch_classes)
        
        # Simple heuristic: most frequent note is likely tonic
        most_common = pc_counter.most_common(1)[0][0]
        
        # Determine major/minor based on presence of minor third
        has_minor_third = ((most_common + 3) % 12) in pc_counter
        has_major_third = ((most_common + 4) % 12) in pc_counter
        
        if has_minor_third and not has_major_third:
            scale_type = ScaleType.NATURAL_MINOR
        else:
            scale_type = ScaleType.MAJOR
        
        # Apply jazz preferences
        scale_type = self._apply_jazz_preferences(scale_type, pitch_classes)
        
        return Key(
            tonic=self.index_notes[most_common],
            scale_type=scale_type,
            confidence=pc_counter[most_common] / len(pitch_classes)
        )
    
    def _correlation_method(self, pitch_classes: List[int]) -> Key:
        """Key detection using correlation with all scale patterns"""
        pc_distribution = self._get_pitch_class_distribution(pitch_classes)
        
        best_key = None
        best_scale = None
        best_correlation = -1.0
        
        for tonic in range(12):
            for scale_type, pattern in self.scale_patterns.items():
                # Generate scale profile (1 for scale tones, 0 for non-scale tones)
                scale_profile = self._generate_scale_profile(tonic, scale_type)
                
                # Calculate correlation
                correlation = sum(pc_distribution[i] * scale_profile[i] for i in range(12))
                
                # Apply jazz preference weighting
                correlation *= self.jazz_scale_preferences.get(scale_type, 0.5)
                
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_key = tonic
                    best_scale = scale_type
        
        return Key(
            tonic=self.index_notes[best_key],
            scale_type=best_scale,
            confidence=best_correlation
        )
    
    def _generate_scale_profile(self, tonic: int, scale_type: ScaleType) -> List[float]:
        """Generate a profile for a scale (1.0 for scale tones, 0.2 for others)"""
        profile = [0.2] * 12  # Base level for non-scale tones
        
        # Get scale degrees
        scale_degrees = self.get_scale_degrees(tonic, scale_type)
        
        for degree in scale_degrees:
            profile[degree] = 1.0
        
        return profile
    
    def get_scale_degrees(self, tonic: int, scale_type: ScaleType) -> List[int]:
        """Get all scale degrees for a given tonic and scale type"""
        pattern = self.scale_patterns[scale_type]
        degrees = [tonic]
        current = tonic
        
        for interval in pattern:
            current = (current + interval) % 12
            degrees.append(current)
        
        return degrees
    
    def get_diatonic_chords(self, key: Key) -> List[JazzChord]:
        """Get all diatonic chords for a detected key"""
        scale_degrees = self.get_scale_degrees(
            self.note_indices[key.tonic], 
            key.scale_type
        )
        
        # Jazz chord qualities for each scale degree
        chord_qualities = self._get_chord_qualities_for_scale(key.scale_type)
        
        chords = []
        for i, degree in enumerate(scale_degrees[:7]):  # First 7 degrees
            root = self.index_notes[degree]
            quality = chord_qualities[i]
            chords.append(JazzChord(root, quality))
        
        return chords
    
    def _get_chord_qualities_for_scale(self, scale_type: ScaleType) -> List[str]:
        """Get jazz chord qualities for each scale degree"""
        # Returns qualities for degrees I through VII
        quality_map = {
            ScaleType.MAJOR: ["maj7", "m7", "m7", "maj7", "7", "m7", "m7b5"],
            ScaleType.NATURAL_MINOR: ["m7", "m7b5", "maj7", "m7", "m7", "maj7", "7"],
            ScaleType.DORIAN: ["m7", "m7", "maj7", "7", "m7", "m7b5", "maj7"],
            ScaleType.MIXOLYDIAN: ["7", "m7", "m7b5", "maj7", "m7", "m7", "maj7"],
            ScaleType.LYDIAN: ["maj7", "7", "m7", "m7b5", "maj7", "m7", "m7"],
            ScaleType.MELODIC_MINOR: ["m7", "m7", "maj7", "7", "7", "m7b5", "m7b5"],
            ScaleType.HARMONIC_MINOR: ["m7", "m7b5", "maj7", "m7", "7", "maj7", "dim7"],
            ScaleType.BLUES: ["7", "7", "7", "7", "7", "7", "7"]  # Simplified for blues
        }
        
        return quality_map.get(scale_type, ["maj7"] * 7)
    
    def is_chord_in_key(self, chord: JazzChord, key: Key, strict: bool = False) -> bool:
        """Check if a chord is diatonic to the key"""
        chord_root_index = self.note_indices[chord.root]
        scale_degrees = self.get_scale_degrees(
            self.note_indices[key.tonic], 
            key.scale_type
        )[:7]  # Only the first 7 degrees matter
        
        # Check if root is in scale
        if chord_root_index not in scale_degrees:
            return False
        
        if strict:
            # Strict check: chord quality must match diatonic expectation
            diatonic_chords = self.get_diatonic_chords(key)
            for diatonic_chord in diatonic_chords:
                if (diatonic_chord.root == chord.root and 
                    diatonic_chord.quality == chord.quality):
                    return True
            return False
        else:
            # Liberal check: only root needs to be in scale
            return True
    
    def get_closest_diatonic_chord(self, chord: JazzChord, key: Key) -> JazzChord:
        """Convert a chord to its closest diatonic equivalent"""
        if self.is_chord_in_key(chord, key, strict=True):
            return chord
        
        # Find closest diatonic root
        chord_root_index = self.note_indices[chord.root]
        scale_degrees = self.get_scale_degrees(
            self.note_indices[key.tonic], 
            key.scale_type
        )[:7]
        
        # Find closest scale degree
        closest_degree = min(scale_degrees, 
                           key=lambda x: min(abs(x - chord_root_index), 
                                           12 - abs(x - chord_root_index)))
        
        closest_root = self.index_notes[closest_degree]
        
        # Use appropriate quality for that scale degree
        diatonic_chords = self.get_diatonic_chords(key)
        for diatonic_chord in diatonic_chords:
            if diatonic_chord.root == closest_root:
                return diatonic_chord
        
        return JazzChord(closest_root, "maj7")  # Fallback

# Integration with the existing system
class KeyAwareHarmonizer:
    """Enhanced harmonizer that uses key detection"""
    
    def __init__(self):
        self.scale_detector = ScaleDetector()
        self.markov_chain = MarkovChain()  # Your existing Markov chain
    
    def harmonize_with_key_detection(self, melody_notes: List[Note], 
                                   creativity: float = 0.5) -> List[Tuple[float, JazzChord]]:
        """Harmonize a melody with key-aware chord selection"""
        
        # Step 1: Detect key
        detected_key = self.scale_detector.detect_key(melody_notes)
        print(f"Detected key: {detected_key} (confidence: {detected_key.confidence:.2f})")
        
        # Step 2: Get diatonic chords for this key
        diatonic_chords = self.scale_detector.get_diatonic_chords(detected_key)
        print(f"Diatonic chords: {' | '.join(str(c) for c in diatonic_chords)}")
        
        # Step 3: Generate progression (existing logic)
        progression = self._generate_base_progression(melody_notes, creativity)
        
        # Step 4: Filter/constrain progression to be more diatonic
        constrained_progression = self._constrain_to_key(progression, detected_key, creativity)
        
        return constrained_progression
    
    def _constrain_to_key(self, progression: List[Tuple[float, JazzChord]], 
                        key: Key, creativity: float) -> List[Tuple[float, JazzChord]]:
        """Constrain chords to be more diatonic based on creativity level"""
        constrained = []
        
        for beat, chord in progression:
            if random.random() < (1.0 - creativity * 0.7):
                # Make chord diatonic (higher creativity = more chromaticism)
                constrained_chord = self.scale_detector.get_closest_diatonic_chord(chord, key)
            else:
                # Keep original chord (allows for chromaticism)
                constrained_chord = chord
            
            constrained.append((beat, constrained_chord))
        
        return constrained

# Demonstration
def demo_key_detection():
    """Demonstrate key detection with sample melodies"""
    print("=== Key and Scale Detection Demo ===\n")
    
    detector = ScaleDetector()
    
    # Sample melodies in different keys
    test_melodies = [
        # C Major melody
        [
            Note("C4", 0.0, 1.0), Note("E4", 1.0, 1.0), Note("G4", 2.0, 1.0),
            Note("B4", 3.0, 1.0), Note("C5", 4.0, 2.0), Note("A4", 6.0, 1.0),
            Note("F4", 7.0, 1.0), Note("E4", 8.0, 2.0)
        ],
        # D Dorian melody (common in jazz)
        [
            Note("D4", 0.0, 1.0), Note("F4", 1.0, 1.0), Note("A4", 2.0, 1.0),
            Note("C5", 3.0, 1.0), Note("B4", 4.0, 1.0), Note("G4", 5.0, 1.0),
            Note("E4", 6.0, 1.0), Note("D4", 7.0, 2.0)
        ],
        # F Blues melody
        [
            Note("F4", 0.0, 1.0), Note("Ab4", 1.0, 0.5), Note("A4", 1.5, 0.5),
            Note("C5", 2.0, 1.0), Note("Bb4", 3.0, 1.0), Note("F4", 4.0, 2.0)
        ]
    ]
    
    methods = ["krumhansl", "simple", "correlation"]
    
    for i, melody in enumerate(test_melodies):
        print(f"\n--- Melody {i + 1} ---")
        print(f"Notes: {[note.pitch for note in melody]}")
        
        for method in methods:
            key = detector.detect_key(melody, method)
            diatonic_chords = detector.get_diatonic_chords(key)
            print(f"{method:12}: {key} (diatonic chords: {' | '.join(str(c) for c in diatonic_chords)})")

if __name__ == "__main__":
    demo_key_detection()