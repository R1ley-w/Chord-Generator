from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from JazzChord import JazzChord
from Phrase_Analysis import Phrase, BeatStrength
from Markov_Chain_For_Chords import MarkovChain

class PhraseAwareState:
    """Enhanced state that includes phrase context"""
    previous_chords: Tuple[JazzChord, ...]  # Traditional Markov state
    phrase_position: str  # 'start', 'middle', 'end'
    current_beat_strength: BeatStrength
    is_cadence: bool
    melody_note: Optional[str] = None
    
    def __hash__(self):
        return hash((self.previous_chords, self.phrase_position, self.current_beat_strength, self.is_cadence, self.melody_note))
    
class PhraseAwareMarkovChain(MarkovChain):
    """Markov chain that incorporates phrase analysis"""
    
    def __init__(self, order: int = 2):
        super().__init__(order)
        self.phrase_transitions = defaultdict(Counter)  # Phrase-aware transitions
        self.cadence_progressions = defaultdict(Counter)  # Special cadence progressions
        
    def train_with_phrases(self, progressions: List[List[JazzChord]], 
                          phrase_analyses: List[List[Phrase]]) -> None:
        """Train the Markov chain with phrase information"""
        print("Training phrase-aware Markov chain...")
        
        for progression, phrases in zip(progressions, phrase_analyses):
            # Map beat positions to phrase context
            beat_to_phrase_context = self._create_phrase_context_map(phrases)
            
            for i in range(len(progression) - self.order):
                state = tuple(progression[i:i + self.order])
                next_chord = progression[i + 1]
                
                # Get phrase context at this position
                context = beat_to_phrase_context.get(i, {
                    'phrase_position': 'middle',
                    'beat_strength': BeatStrength.WEAK,
                    'is_cadence': False
                })
                
                # Create enhanced state
                enhanced_state = PhraseAwareState(
                    previous_chords=state,
                    phrase_position=context['phrase_position'],
                    current_beat_strength=context['beat_strength'],
                    is_cadence=context['is_cadence']
                )
                
                # Count transitions for enhanced states
                self.phrase_transitions[enhanced_state][next_chord] += 1
                
                # Special handling for cadence points
                if context['is_cadence']:
                    cadence_state = tuple(progression[max(0, i-1):i+1])  # Last 2 chords before cadence
                    self.cadence_progressions[cadence_state][next_chord] += 1
        
        self._compute_phrase_probabilities()
        
    def _create_phrase_context_map(self, phrases: List[Phrase]) -> Dict[int, Dict]:
        """Create a mapping from chord position to phrase context"""
        context_map = {}
        current_beat = 0
        
        for phrase_idx, phrase in enumerate(phrases):
            phrase_duration = len(phrase.notes)  # Simplified - use actual beat calculation
            
            for note_idx, note in enumerate(phrase.notes):
                position = current_beat + note_idx
                
                # Determine phrase position
                if note_idx == 0:
                    phrase_position = 'start'
                elif note_idx == len(phrase.notes) - 1:
                    phrase_position = 'end'
                else:
                    phrase_position = 'middle'
                
                # Determine if this is a cadence point
                is_cadence = (note_idx == len(phrase.notes) - 1 and 
                            phrase_idx == len(phrases) - 1)  # Final cadence
                
                context_map[position] = {
                    'phrase_position': phrase_position,
                    'beat_strength': phrase.analyzer._get_beat_strength(note.start_beat),
                    'is_cadence': is_cadence
                }
            
            current_beat += phrase_duration
        
        return context_map
    
    def predict_next_with_phrases(self, previous_chords: List[JazzChord], 
                                phrase_context: Dict,
                                temperature: float = 1.0) -> JazzChord:
        """
        Predict next chord with phrase context awareness
        """
        if len(previous_chords) < self.order:
            padded_chords = self._pad_sequence(previous_chords)
        else:
            padded_chords = previous_chords[-self.order:]
        
        state = tuple(padded_chords)
        
        # Create enhanced state
        enhanced_state = PhraseAwareState(
            previous_chords=state,
            phrase_position=phrase_context.get('phrase_position', 'middle'),
            current_beat_strength=phrase_context.get('beat_strength', BeatStrength.WEAK),
            is_cadence=phrase_context.get('is_cadence', False),
            melody_note=phrase_context.get('melody_note')
        )
        
        # Special handling for cadence points
        if enhanced_state.is_cadence:
            candidates = self._get_cadence_candidates(state, temperature)
        else:
            candidates = self.get_possible_next_with_phrases(enhanced_state, temperature)
        
        if not candidates:
            # Fallback to basic Markov prediction
            return self.predict_next(previous_chords, temperature)
        
        return self._weighted_choice(candidates)
    
    def get_possible_next_with_phrases(self, state: PhraseAwareState, 
                                     temperature: float = 1.0) -> Dict[JazzChord, float]:
        """Get possible next chords considering phrase context"""
        
        # Try exact phrase-aware state match first
        if state in self.phrase_transitions:
            probabilities = self._get_phrase_state_probabilities(state, temperature)
            if probabilities:
                return probabilities
        
        # Fallback strategies based on phrase position
        if state.phrase_position == 'start':
            return self._get_phrase_start_probabilities(state.previous_chords, temperature)
        elif state.phrase_position == 'end':
            return self._get_phrase_end_probabilities(state.previous_chords, temperature)
        else:
            # Middle of phrase - use basic Markov with melody awareness
            return self.get_possible_next(state.previous_chords, temperature)
    
    def _get_cadence_candidates(self, state: Tuple[JazzChord, ...], 
                              temperature: float) -> Dict[JazzChord, float]:
        """Get appropriate cadence chords"""
        if state in self.cadence_progressions:
            probabilities = self.cadence_progressions[state].copy()
            if temperature != 1.0:
                probabilities = self._apply_temperature(probabilities, temperature)
            return probabilities
        
        # Common jazz cadences as fallback
        common_cadences = {
            JazzChord("G", "7"): 0.6,    # V7
            JazzChord("C", "maj7"): 0.3, # I
            JazzChord("A", "m7"): 0.1    # vi
        }
        return common_cadences
    
