import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

class BeatStrength(Enum):
    STRONG = 3
    MEDIUM = 2
    WEAK = 1
    VERY_WEAK = 0

@dataclass
class Note:
    pitch: str  # e.g., "C4", "Eb5"
    start_beat: float  # Beat position where note starts
    duration: float  # Duration in beats
    velocity: int = 80  # Note intensity (0-127)
    
    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration
    
    def __str__(self):
        return f"{self.pitch} (beat {self.start_beat:.1f}, dur {self.duration:.1f})"

@dataclass
class Phrase:
    notes: List[Note]
    start_beat: float
    end_beat: float
    length_bars: int
    cadence_note: Optional[Note] = None
    strong_beat_notes: List[Note] = None
    
    def __post_init__(self):
        if self.strong_beat_notes is None:
            self.strong_beat_notes = []
    
    @property
    def duration(self) -> float:
        return self.end_beat - self.start_beat
    
    def get_notes_at_strong_beats(self, time_sig: Tuple[int, int] = (4, 4)) -> List[Note]:
        """Get notes that occur on strong beats"""
        beats_per_bar = time_sig[0]
        strong_beats = [0, beats_per_bar / 2]  # Typically beats 1 and 3 in 4/4
        
        strong_notes = []
        for note in self.notes:
            # Check if note start aligns with strong beat within tolerance
            beat_in_bar = note.start_beat % beats_per_bar
            for strong_beat in strong_beats:
                if abs(beat_in_bar - strong_beat) < 0.25:  # Small tolerance
                    strong_notes.append(note)
                    break
        
        return strong_notes

class PhraseAnalyzer:
    def __init__(self, time_signature: Tuple[int, int] = (4, 4), tempo: int = 120):
        self.time_signature = time_signature
        self.tempo = tempo
        self.beats_per_bar = time_signature[0]
        self.beat_value = time_signature[1]  # 4 = quarter note
        
    def analyze_phrases(self, notes: List[Note], total_bars: int = 8) -> List[Phrase]:
        """
        Main method to analyze notes and identify musical phrases
        """
        if not notes:
            return []
        
        # Sort notes by start time
        sorted_notes = sorted(notes, key=lambda x: x.start_beat)
        
        # Strategy 1: Look for natural breaks (rests)
        phrases = self._detect_phrases_by_rests(sorted_notes, total_bars)
        
        # Strategy 2: If no clear rests, divide into equal phrases
        if len(phrases) <= 1:
            phrases = self._divide_into_equal_phrases(sorted_notes, total_bars)
        
        # Analyze each phrase for musical features
        analyzed_phrases = []
        for phrase_notes in phrases:
            phrase = self._analyze_single_phrase(phrase_notes, total_bars)
            analyzed_phrases.append(phrase)
        
        return analyzed_phrases
    
    def _detect_phrases_by_rests(self, notes: List[Note], total_bars: float) -> List[List[Note]]:
        """
        Detect phrases based on rests (gaps between notes)
        """
        phrases = []
        current_phrase = []
        total_beats = total_bars * self.beats_per_bar
        
        # Threshold for considering a gap as a phrase boundary (in beats)
        rest_threshold = 1.5  # 1.5 beats of silence indicates phrase boundary
        
        for i, note in enumerate(notes):
            current_phrase.append(note)
            
            # Check if there's a significant gap after this note
            if i < len(notes) - 1:
                next_note = notes[i + 1]
                gap = next_note.start_beat - note.end_beat
                
                if gap >= rest_threshold:
                    # Significant rest found - end current phrase
                    phrases.append(current_phrase.copy())
                    current_phrase = []
        
        # Add the final phrase
        if current_phrase:
            phrases.append(current_phrase)
        
        return phrases
    
    def _divide_into_equal_phrases(self, notes: List[Note], total_bars: float) -> List[List[Note]]:
        """
        Divide melody into equal phrases (typically 2 or 4 bars)
        """
        total_beats = total_bars * self.beats_per_bar
        
        # Common phrase lengths in jazz: 2 bars or 4 bars
        if total_bars >= 8:
            phrase_length_bars = 4
        elif total_bars >= 4:
            phrase_length_bars = 2
        else:
            phrase_length_bars = 2  # Default
        
        phrase_length_beats = phrase_length_bars * self.beats_per_bar
        num_phrases = math.ceil(total_bars / phrase_length_bars)
        
        phrases = []
        for i in range(num_phrases):
            start_beat = i * phrase_length_beats
            end_beat = (i + 1) * phrase_length_beats
            
            # Find notes in this phrase
            phrase_notes = [
                note for note in notes 
                if start_beat <= note.start_beat < end_beat
            ]
            
            if phrase_notes:  # Only add non-empty phrases
                phrases.append(phrase_notes)
        
        return phrases
    
    def _analyze_single_phrase(self, phrase_notes: List[Note], total_bars: float) -> Phrase:
        """Analyze a single phrase for musical features"""
        if not phrase_notes:
            raise ValueError("Cannot analyze empty phrase")
        
        start_beat = min(note.start_beat for note in phrase_notes)
        end_beat = max(note.end_beat for note in phrase_notes)
        
        # Calculate phrase length in bars
        phrase_duration_beats = end_beat - start_beat
        length_bars = phrase_duration_beats / self.beats_per_bar
        
        # Identify cadence note (typically the last note)
        cadence_note = phrase_notes[-1]
        
        # Find notes on strong beats
        strong_beat_notes = self._find_strong_beat_notes(phrase_notes)
        
        # Find harmonically important notes
        important_notes = self._identify_important_notes(phrase_notes)
        
        phrase = Phrase(
            notes=phrase_notes,
            start_beat=start_beat,
            end_beat=end_beat,
            length_bars=length_bars,
            cadence_note=cadence_note,
            strong_beat_notes=strong_beat_notes
        )
        
        return phrase
    
    def _find_strong_beat_notes(self, notes: List[Note]) -> List[Note]:
        """Identify notes that occur on metrically strong positions"""
        strong_notes = []
        
        for note in notes:
            beat_strength = self._get_beat_strength(note.start_beat)
            
            # Consider strong and medium strength beats as harmonically important
            if beat_strength in [BeatStrength.STRONG, BeatStrength.MEDIUM]:
                strong_notes.append(note)
        
        return strong_notes
    
    def _get_beat_strength(self, beat_position: float) -> BeatStrength:
        """Determine the metric strength of a beat position"""
        beat_in_bar = beat_position % self.beats_per_bar
        
        if beat_in_bar == 0:  # Downbeat
            return BeatStrength.STRONG
        elif beat_in_bar == self.beats_per_bar / 2:  # Middle of bar (beat 3 in 4/4)
            return BeatStrength.MEDIUM
        elif beat_in_bar % 1 == 0:  # Other quarter notes
            return BeatStrength.WEAK
        else:  # Off-beats, eighth notes, etc.
            return BeatStrength.VERY_WEAK
    
    def _identify_important_notes(self, notes: List[Note]) -> List[Note]:
        """
        Identify harmonically important notes based on:
        - Metric position
        - Duration
        - Melodic peaks
        """
        if not notes:
            return []
        
        # Weight factors for importance calculation
        weights = {
            'duration': 0.4,
            'beat_strength': 0.3,
            'melodic_emphasis': 0.3
        }
        
        note_scores = []
        for note in notes:
            score = 0
            
            # Duration importance (longer notes are more important)
            duration_score = min(note.duration / 2.0, 1.0)  # Normalize
            score += duration_score * weights['duration']
            
            # Beat strength importance
            beat_strength = self._get_beat_strength(note.start_beat)
            strength_score = beat_strength.value / 3.0  # Normalize to 0-1
            score += strength_score * weights['beat_strength']
            
            # Melodic emphasis (high or low notes in phrase)
            pitches = [self._pitch_to_midi(n.pitch) for n in notes]
            current_pitch = self._pitch_to_midi(note.pitch)
            
            if max(pitches) == current_pitch or min(pitches) == current_pitch:
                score += weights['melodic_emphasis']
            
            note_scores.append((note, score))
        
        # Return top 30% of notes by importance, or at least 2 notes
        note_scores.sort(key=lambda x: x[1], reverse=True)
        num_important = max(2, len(notes) // 3)
        
        return [note for note, score in note_scores[:num_important]]
    
    def _pitch_to_midi(self, pitch: str) -> int:
        """Convert pitch string to MIDI note number (simplified)"""
        pitch_map = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        
        # Simple parser for pitches like "C4", "Eb5", etc.
        note_name = ''.join([c for c in pitch if not c.isdigit()])
        octave = int(''.join([c for c in pitch if c.isdigit()]))
        
        note_value = pitch_map.get(note_name, 0)
        return (octave + 1) * 12 + note_value
    
    def get_chord_change_points(self, phrases: List[Phrase]) -> List[float]:
        """
        Determine optimal points to change chords based on phrase analysis
        Returns beat positions where chords should change
        """
        change_points = []
        
        for phrase in phrases:
            # Always change chord at phrase boundaries
            change_points.append(phrase.start_beat)
            
            # For longer phrases, consider changing chords on strong beats within phrase
            if phrase.length_bars >= 2:
                strong_beats = self._get_strong_beats_in_phrase(phrase)
                change_points.extend(strong_beats)
        
        # Also change chord at the very end
        if phrases:
            change_points.append(phrases[-1].end_beat)
        
        # Remove duplicates and sort
        return sorted(set(change_points))
    
    def _get_strong_beats_in_phrase(self, phrase: Phrase) -> List[float]:
        """Get strong beat positions within a phrase"""
        strong_beats = []
        current_beat = phrase.start_beat
        
        while current_beat < phrase.end_beat:
            beat_strength = self._get_beat_strength(current_beat)
            if beat_strength in [BeatStrength.STRONG, BeatStrength.MEDIUM]:
                strong_beats.append(current_beat)
            current_beat += 1  # Check every beat
        
        return strong_beats
    
    def generate_phrase_report(self, phrases: List[Phrase]) -> Dict:
        """Generate a comprehensive analysis report"""
        report = {
            "total_phrases": len(phrases),
            "phrase_lengths": [f"{p.length_bars} bars" for p in phrases],
            "cadence_notes": [str(p.cadence_note.pitch) for p in phrases],
            "chord_change_points": self.get_chord_change_points(phrases),
            "phrase_details": []
        }
        
        for i, phrase in enumerate(phrases):
            phrase_info = {
                "phrase_number": i + 1,
                "start_beat": phrase.start_beat,
                "end_beat": phrase.end_beat,
                "length_bars": phrase.length_bars,
                "cadence_note": str(phrase.cadence_note),
                "strong_beat_notes": [str(note) for note in phrase.strong_beat_notes],
                "total_notes": len(phrase.notes)
            }
            report["phrase_details"].append(phrase_info)
        
        return report

# Example usage and demonstration
def create_sample_melody() -> List[Note]:
    """Create a sample 8-bar melody for testing"""
    # A simple jazz-like melody in C major
    notes = [
        Note("E4", 0.0, 1.0),   # Bar 1
        Note("G4", 1.0, 1.0),
        Note("C5", 2.0, 2.0),   # Long note on strong beat
        
        Note("B4", 4.0, 1.0),   # Bar 3 - new phrase
        Note("A4", 5.0, 1.0),
        Note("G4", 6.0, 2.0),   # Cadence note
        
        Note("F4", 8.0, 0.5),   # Bar 5
        Note("G4", 8.5, 0.5),
        Note("A4", 9.0, 1.0),
        Note("G4", 10.0, 2.0),  # Long note
        
        Note("E4", 12.0, 1.0),  # Bar 7 - final phrase
        Note("C4", 13.0, 1.0),
        Note("D4", 14.0, 1.0),
        Note("C4", 15.0, 1.0),  # Final cadence
    ]
    return notes

def demo_phrase_analysis():
    """Demonstrate the phrase analysis system"""
    print("=== Phrase-Based Melody Analysis Demo ===\n")
    
    # Create analyzer and sample melody
    analyzer = PhraseAnalyzer(time_signature=(4, 4), tempo=120)
    melody = create_sample_melody()
    
    print("Original Melody Notes:")
    for note in melody:
        print(f"  {note}")
    
    # Analyze phrases
    phrases = analyzer.analyze_phrases(melody, total_bars=8)
    
    print(f"\nDetected {len(phrases)} phrases:")
    
    for i, phrase in enumerate(phrases):
        print(f"\nPhrase {i + 1}:")
        print(f"  Bars: {phrase.length_bars:.1f} (beats {phrase.start_beat:.1f}-{phrase.end_beat:.1f})")
        print(f"  Cadence note: {phrase.cadence_note}")
        print(f"  Strong beat notes: {[str(n) for n in phrase.strong_beat_notes]}")
        print(f"  Total notes in phrase: {len(phrase.notes)}")
    
    # Generate analysis report
    report = analyzer.generate_phrase_report(phrases)
    
    print(f"\n=== Analysis Report ===")
    print(f"Recommended chord change points (beats): {report['chord_change_points']}")
    print(f"Phrase cadence notes: {report['cadence_notes']}")
    
    print(f"\nSuggested chord rhythm based on phrases:")
    change_points = report['chord_change_points']
    for i in range(len(change_points) - 1):
        start = change_points[i]
        end = change_points[i + 1]
        duration = end - start
        print(f"  Chord at beat {start:.1f}, hold for {duration:.1f} beats")

if __name__ == "__main__":
    demo_phrase_analysis()