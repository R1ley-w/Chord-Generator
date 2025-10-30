from Markov_Chain_For_Chords import create_sample_progressions, create_training_data_with_phrases
from Markov_Chain_For_Chords2 import PhraseAwareMarkovChain
from JazzChord import JazzChord
from Phrase_Analysis import Note, BeatStrength, PhraseAnalyzer, Phrase
from typing import List, Tuple, Dict

from melody_generator import create_melody_for_progression


class JazzHarmonizer:
    """Main class that integrates phrase analysis with Markov chain"""
    
    def __init__(self):
        self.phrase_analyzer = PhraseAnalyzer()
        self.markov_chain = PhraseAwareMarkovChain(order=2)
    
    def harmonize_melody(self, melody_notes: List[Note], 
                        creativity: float = 0.5) -> List[Tuple[float, JazzChord]]:
        """Main method to harmonize a melody with phrase awareness"""
        
        # Step 1: Analyze phrases
        phrases = self.phrase_analyzer.analyze_phrases(melody_notes)
        chord_change_points = self.phrase_analyzer.get_chord_change_points(phrases)
        
        # Step 2: Generate chord progression with phrase awareness
        progression = []
        current_phrase_idx = 0
        
        for i, change_point in enumerate(chord_change_points):
            if i == len(chord_change_points) - 1:
                break
                
            # Get phrase context at this position
            phrase_context = self._get_phrase_context_at_beat(phrases, change_point)
            
            # Get melody note at this position
            melody_note = self._get_melody_note_at_beat(melody_notes, change_point)
            phrase_context['melody_note'] = melody_note
            
            # Predict next chord with phrase context
            next_chord = self.markov_chain.predict_next_with_phrases(
                previous_chords=[chord for _, chord in progression],
                phrase_context=phrase_context,
                temperature=0.1 + (creativity * 1.9)
            )
            
            # Add chord with duration
            chord_duration = chord_change_points[i + 1] - change_point
            progression.append((change_point, next_chord, chord_duration))
        
        return progression
    
    def _get_phrase_context_at_beat(self, phrases: List[Phrase], beat: float) -> Dict:
        """Get phrase context information at a specific beat"""
        for phrase in phrases:
            if phrase.start_beat <= beat < phrase.end_beat:
                # Calculate position within phrase
                phrase_progress = (beat - phrase.start_beat) / phrase.duration
                
                if phrase_progress < 0.25:
                    position = 'start'
                elif phrase_progress > 0.75:
                    position = 'end'
                else:
                    position = 'middle'
                
                # Check if this is a cadence point
                is_cadence = (phrase == phrases[-1] and 
                            beat >= phrase.end_beat - 2.0)  # Last 2 beats
                
                # Get beat strength
                beat_strength = self.phrase_analyzer._get_beat_strength(beat)
                
                return {
                    'phrase_position': position,
                    'beat_strength': beat_strength,
                    'is_cadence': is_cadence
                }
        
        return {'phrase_position': 'middle', 'beat_strength': BeatStrength.WEAK, 'is_cadence': False}
    
    def create_training_data_with_phrases():
        """Create training data that includes phrase analysis"""
        progressions = create_sample_progressions()
        phrase_analyses = []
        
        # For each progression, create a corresponding melodic phrase structure
        for progression in progressions:
            # Create synthetic melody that matches the progression
            melody_notes = create_melody_for_progression(progression)
            
            # Analyze phrases in the melody
            analyzer = PhraseAnalyzer()
            phrases = analyzer.analyze_phrases(melody_notes, total_bars=len(progression))
            
            phrase_analyses.append(phrases)
        
        return progressions, phrase_analyses

# Train the enhanced model
progressions, phrase_analyses = create_training_data_with_phrases()
harmonizer = JazzHarmonizer()
harmonizer.markov_chain.train_with_phrases(progressions, phrase_analyses)