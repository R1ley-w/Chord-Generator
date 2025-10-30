# main_app.py
import pickle
import random
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict, Counter

# Import all our modules
from Markov_Chain_For_Chords import MarkovChain, JazzChord
from key_detector import ScaleDetector, Key, ScaleType
from Phrase_Analysis import PhraseAnalyzer, Note, Phrase, BeatStrength
from melody_generator import MelodyGenerator, create_melody_for_progression
from standard_finder import JazzStandardsScraper

class CreativityLevel(Enum):
    CONSERVATIVE = 0.3
    BALANCED = 0.5
    CREATIVE = 0.7
    EXPERIMENTAL = 1.0

class RhythmStyle(Enum):
    SWING = "swing"
    BOSSA_NOVA = "bossa_nova"
    BALLAD = "ballad"
    LATIN = "latin"
    FUNK = "funk"

@dataclass
class ChordWithDuration:
    chord: JazzChord
    start_beat: float
    duration: float
    rhythm_pattern: List[float] = None
    
    def __str__(self):
        return f"{self.chord} (beats {self.start_beat:.1f}-{self.start_beat + self.duration:.1f})"

class JazzChordGeneratorApp:
    """Main application that integrates all components"""
    
    def __init__(self):
        self.markov_chain = MarkovChain(order=2)
        self.scale_detector = ScaleDetector()
        self.phrase_analyzer = PhraseAnalyzer()
        self.melody_generator = MelodyGenerator()
        self.is_trained = False
        
        # Application state
        self.current_progression = []
        self.current_melody = []
        self.current_key = None
        self.rhythm_style = RhythmStyle.SWING
        
    def train_model(self, use_sample_data: bool = True):
        """Train the Markov chain model"""
        print("Training jazz chord model...")
        
        if use_sample_data:
            # Use our sample progressions for demonstration
            from data_utils import create_sample_progressions
            progressions = create_sample_progressions()
        else:
            # In a real app, you'd load from a jazz standards database
            progressions = self._load_jazz_standards()
        
        self.markov_chain.train(progressions)
        self.is_trained = True
        print(f"Model trained on {len(progressions)} progressions!")
        
    def process_user_melody(self, melody_notes: List[Note], 
                          creativity: CreativityLevel = CreativityLevel.BALANCED,
                          use_phrases: bool = True) -> List[ChordWithDuration]:
        """
        Main method: process user melody and generate chord progression
        """
        if not self.is_trained:
            self.train_model()
        
        print("\n" + "="*50)
        print("PROCESSING MELODY...")
        print("="*50)
        
        # Step 1: Detect key and scale
        self.current_key = self.scale_detector.detect_key(melody_notes)
        print(f"🎵 Detected Key: {self.current_key} "
              f"(confidence: {self.current_key.confidence:.2f})")
        
        # Show diatonic chords for this key
        diatonic_chords = self.scale_detector.get_diatonic_chords(self.current_key)
        print(f"🎹 Diatonic chords: {' | '.join(str(c) for c in diatonic_chords)}")
        
        # Step 2: Analyze phrases (if enabled)
        phrases = []
        chord_change_points = []
        
        if use_phrases:
            phrases = self.phrase_analyzer.analyze_phrases(melody_notes)
            chord_change_points = self.phrase_analyzer.get_chord_change_points(phrases)
            
            print(f"📝 Detected {len(phrases)} musical phrases:")
            for i, phrase in enumerate(phrases):
                print(f"   Phrase {i+1}: {phrase.length_bars:.1f} bars, "
                      f"cadence: {phrase.cadence_note.pitch}")
        else:
            # Use simple equal division
            total_beats = max(note.end_beat for note in melody_notes) if melody_notes else 32
            chord_change_points = [i * 4.0 for i in range(int(total_beats / 4) + 1)]
        
        print(f"🎼 Chord change points: {chord_change_points}")
        
        # Step 3: Generate chord progression using Markov chain with key constraints
        progression = self._generate_key_aware_progression(
            melody_notes, 
            chord_change_points,
            creativity.value,
            phrases if use_phrases else []
        )
        
        self.current_progression = progression
        self.current_melody = melody_notes
        
        return progression
    
    def _generate_key_aware_progression(self, 
                                     melody_notes: List[Note],
                                     change_points: List[float],
                                     creativity: float,
                                     phrases: List[Phrase]) -> List[ChordWithDuration]:
        """Generate progression that respects key and phrase structure"""
        progression = []
        previous_chords = []
        
        for i in range(len(change_points) - 1):
            start_beat = change_points[i]
            duration = change_points[i + 1] - start_beat
            
            # Get phrase context
            phrase_context = self._get_phrase_context(phrases, start_beat)
            
            # Get current melody note (for harmonization)
            current_melody_note = self._get_melody_note_at_beat(melody_notes, start_beat)
            
            # Predict next chord
            next_chord = self.markov_chain.predict_next(
                previous_chords, 
                temperature=creativity
            )
            
            # Apply key constraints based on creativity level
            constrained_chord = self._apply_key_constraints(
                next_chord, 
                self.current_key, 
                creativity
            )
            
            # Ensure chord works with melody note
            final_chord = self._ensure_melody_harmony(constrained_chord, current_melody_note)
            
            # Add rhythm pattern based on style
            rhythm_pattern = self._get_rhythm_pattern(duration)
            
            chord_with_duration = ChordWithDuration(
                chord=final_chord,
                start_beat=start_beat,
                duration=duration,
                rhythm_pattern=rhythm_pattern
            )
            
            progression.append(chord_with_duration)
            previous_chords.append(final_chord)
            
            # Keep only last few chords for Markov state
            if len(previous_chords) > self.markov_chain.order:
                previous_chords = previous_chords[-self.markov_chain.order:]
        
        return progression
    
    def _get_phrase_context(self, phrases: List[Phrase], beat: float) -> Dict:
        """Get musical context at a specific beat"""
        if not phrases:
            return {"position": "middle", "importance": "normal"}
        
        for phrase in phrases:
            if phrase.start_beat <= beat < phrase.end_beat:
                progress = (beat - phrase.start_beat) / phrase.duration
                
                if progress < 0.25:
                    position = "start"
                    importance = "high"
                elif progress > 0.75:
                    position = "end" 
                    importance = "high"
                else:
                    position = "middle"
                    importance = "normal"
                
                return {"position": position, "importance": importance}
        
        return {"position": "middle", "importance": "normal"}
    
    def _get_melody_note_at_beat(self, melody_notes: List[Note], beat: float) -> Optional[str]:
        """Get the melody note playing at a specific beat"""
        for note in melody_notes:
            if note.start_beat <= beat < note.end_beat:
                return note.pitch
        return None
    
    def _apply_key_constraints(self, chord: JazzChord, key: Key, creativity: float) -> JazzChord:
        """Apply key-based constraints to a chord"""
        # Higher creativity = more chromatic freedom
        if random.random() < creativity:
            return chord  # Keep original chord
        
        # Lower creativity = more diatonic
        return self.scale_detector.get_closest_diatonic_chord(chord, key)
    
    def _ensure_melody_harmony(self, chord: JazzChord, melody_note: Optional[str]) -> JazzChord:
        """Ensure chord works with melody note"""
        if not melody_note:
            return chord
        
        # Simple check: if melody note is a chord tone
        # In a full implementation, you'd check if melody note is a chord tone or available tension
        return chord  # Placeholder - implement proper melody-harmony check
    
    def _get_rhythm_pattern(self, duration: float) -> List[float]:
        """Get rhythm pattern based on current style"""
        base_patterns = {
            RhythmStyle.SWING: [1.0, 1.0, 2.0],  # Typical swing pattern
            RhythmStyle.BOSSA_NOVA: [0.5, 0.5, 0.5, 0.5, 2.0],  # Bossa pattern
            RhythmStyle.BALLAD: [2.0, 2.0],  # Sustained chords
            RhythmStyle.LATIN: [0.5, 1.5, 1.0, 1.0],  # Latin rhythm
            RhythmStyle.FUNK: [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]  # Funky 16ths
        }
        
        pattern = base_patterns.get(self.rhythm_style, [duration])
        
        # Adjust pattern to fit duration
        total_pattern_duration = sum(pattern)
        if total_pattern_duration != duration:
            scale_factor = duration / total_pattern_duration
            pattern = [beat * scale_factor for beat in pattern]
        
        return pattern
    
    def set_rhythm_style(self, style: RhythmStyle):
        """Set the rhythm style for chord playback"""
        self.rhythm_style = style
        print(f"🎶 Rhythm style set to: {style.value}")
    
    def generate_demo_melody(self, style: str = "bebop") -> List[Note]:
        """Generate a demo melody for testing"""
        # Create a simple ii-V-I progression to generate melody from
        demo_progression = [
            JazzChord("D", "m7"), JazzChord("G", "7"), JazzChord("C", "maj7"),
            JazzChord("C", "maj7"), JazzChord("A", "m7"), JazzChord("D", "m7"), JazzChord("G", "7")
        ]
        
        return create_melody_for_progression(demo_progression, style)
    
    def export_progression(self, filename: str = "jazz_progression.json"):
        """Export the current progression to JSON"""
        if not self.current_progression:
            print("No progression to export!")
            return
        
        export_data = {
            "key": str(self.current_key),
            "melody_notes": [
                {
                    "pitch": note.pitch,
                    "start_beat": note.start_beat,
                    "duration": note.duration
                } for note in self.current_melody
            ],
            "chord_progression": [
                {
                    "chord": str(chord_dur.chord),
                    "start_beat": chord_dur.start_beat,
                    "duration": chord_dur.duration,
                    "rhythm_pattern": chord_dur.rhythm_pattern
                } for chord_dur in self.current_progression
            ],
            "rhythm_style": self.rhythm_style.value
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"💾 Progression exported to {filename}")
    
    def display_progression(self):
        """Display the current progression in a readable format"""
        if not self.current_progression:
            print("No progression generated yet!")
            return
        
        print("\n" + "="*50)
        print("GENERATED JAZZ PROGRESSION")
        print("="*50)
        print(f"Key: {self.current_key}")
        print(f"Rhythm: {self.rhythm_style.value}")
        print("\nChord Progression:")
        
        for i, chord_dur in enumerate(self.current_progression):
            bar_num = int(chord_dur.start_beat / 4) + 1
            beat_in_bar = chord_dur.start_beat % 4 + 1
            
            print(f"Bar {bar_num}, Beat {beat_in_bar:.0f}: {chord_dur.chord} "
                  f"({chord_dur.duration} beats)")
            
            if chord_dur.rhythm_pattern:
                print(f"       Rhythm: {chord_dur.rhythm_pattern}")
        
        print("\nSuggested voicings:")
        for chord_dur in self.current_progression[:4]:  # Show first 4 chords
            print(f"  {chord_dur.chord}: {self._suggest_voicing(chord_dur.chord)}")
    
    def _suggest_voicing(self, chord: JazzChord) -> str:
        """Suggest a piano voicing for the chord"""
        voicings = {
            "maj7": "3-5-7-9 voicing",
            "m7": "rootless 3-5-7-9", 
            "7": "3-13-b7-9",
            "m7b5": "3-b5-b7-9"
        }
        return voicings.get(chord.quality, "closed position")

# Example usage and demonstration
def demo_complete_app():
    """Demonstrate the complete application"""
    print("🎷 JAZZ CHORD GENERATOR APP DEMO 🎷")
    print("=" * 50)
    
    # Initialize app
    app = JazzChordGeneratorApp()
    
    # Train the model
    app.train_model()
    print()
    
    # Test different creativity levels
    creativity_levels = [
        (CreativityLevel.CONSERVATIVE, "Conservative"),
        (CreativityLevel.BALANCED, "Balanced"), 
        (CreativityLevel.CREATIVE, "Creative"),
        (CreativityLevel.EXPERIMENTAL, "Experimental")
    ]
    
    # Generate a demo melody
    print("🎵 Generating demo melody...")
    demo_melody = app.generate_demo_melody("bebop")
    print(f"Demo melody: {[note.pitch for note in demo_melody[:8]]}...")
    print()
    
    for creativity, label in creativity_levels:
        print(f"\n🧪 Testing {label} mode (creativity: {creativity.value}):")
        print("-" * 40)
        
        # Process melody
        progression = app.process_user_melody(
            demo_melody,
            creativity=creativity,
            use_phrases=True
        )
        
        # Display results
        app.display_progression()
        
        # Export one example
        if creativity == CreativityLevel.BALANCED:
            app.export_progression(f"jazz_progression_{label.lower()}.json")
        
        print()

def interactive_demo():
    """Interactive demo for user testing"""
    app = JazzChordGeneratorApp()
    app.train_model()
    
    print("\n🎹 Interactive Jazz Chord Generator")
    print("Enter melody notes (format: C4 0.0 1.0), or 'done' to finish:")
    
    melody_notes = []
    while True:
        user_input = input("Note (pitch start_beat duration): ").strip()
        if user_input.lower() == 'done':
            break
        
        try:
            pitch, start_beat, duration = user_input.split()
            note = Note(pitch, float(start_beat), float(duration))
            melody_notes.append(note)
            print(f"Added: {note}")
        except ValueError:
            print("Invalid format! Use: C4 0.0 1.0")
    
    if melody_notes:
        print("\nGenerating chord progression...")
        progression = app.process_user_melody(melody_notes)
        app.display_progression()
    else:
        print("No notes entered. Using demo melody...")
        demo_melody = app.generate_demo_melody()
        progression = app.process_user_melody(demo_melody)
        app.display_progression()

if __name__ == "__main__":
    # Initialize and scrape
    scraper = JazzStandardsScraper()
    standards = scraper.load_standards()  # Load existing
    if not standards:
        standards = scraper.create_sample_standards_dataset()  # Create sample data
        scraper.save_standards(standards)

    # Convert to training data
    training_data = scraper.convert_to_training_data(standards)

    # Train your Markov chain
    markov_chain = MarkovChain(order=3)
    markov_chain.train(training_data)
    # Run the complete demo
    demo_complete_app()
    
    # Uncomment to run interactive demo
    interactive_demo()