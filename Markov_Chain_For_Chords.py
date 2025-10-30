import random
import json
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import numpy as np
from JazzChord import JazzChord
from JazzHarmonizer import JazzHarmonizer
from Phrase_Analysis import PhraseAnalyzer
from melody_generator import create_melody_for_progression

class MarkovChain:
    """Markov Chain for jazz chord progression generation"""
    
    def __init__(self, order: int = 2):
        self.order = order
        self.transitions = defaultdict(Counter)  # state -> Counter({next_chord: count})
        self.chord_vocab = set()
        self.start_states = []
        self._probabilities = {}  # Cached probabilities
        
    def train(self, progressions: List[List[JazzChord]]) -> None:
        """Train the Markov chain on chord progressions"""
        print(f"Training Markov chain (order {self.order}) on {len(progressions)} progressions...")
        
        # Build vocabulary and count transitions
        transition_counts = 0
        for progression in progressions:
            # Add chords to vocabulary
            self.chord_vocab.update(progression)
            
            # Count transitions for each state sequence
            for i in range(len(progression) - self.order):
                state = tuple(progression[i:i + self.order])
                next_chord = progression[i + self.order]
                
                self.transitions[state][next_chord] += 1
                transition_counts += 1
        
        print(f"Learned {transition_counts} transitions across {len(self.transitions)} states")
        print(f"Vocabulary size: {len(self.chord_vocab)}")
        
        # Convert counts to probabilities
        self._compute_probabilities()
        
        # Identify common starting sequences
        self._find_common_start_states(progressions)
    
    def _compute_probabilities(self) -> None:
        """Convert transition counts to probabilities"""
        self._probabilities = {}
        
        for state, next_chords in self.transitions.items():
            total = sum(next_chords.values())
            self._probabilities[state] = {
                chord: count / total 
                for chord, count in next_chords.items()
            }
    
    def _find_common_start_states(self, progressions: List[List[JazzChord]]) -> None:
        """Find common starting sequences in the training data"""
        start_counter = Counter()
        
        for progression in progressions:
            if len(progression) >= self.order:
                start_state = tuple(progression[:self.order])
                start_counter[start_state] += 1
        
        # Get most common starting sequences
        self.start_states = [state for state, count in start_counter.most_common(10)]
        print(f"Found {len(self.start_states)} common starting sequences")
    
    def predict_next(self, previous_chords: List[JazzChord], temperature: float = 1.0) -> JazzChord:
        """
        Predict the next chord given previous chords
        
        Args:
            previous_chords: List of previous chords (length should be >= order)
            temperature: Controls randomness (0.1 = conservative, 2.0 = creative)
        """
        if len(previous_chords) < self.order:
            # Pad with common starting chords if needed
            padded_chords = self._pad_sequence(previous_chords)
        else:
            padded_chords = previous_chords[-self.order:]
        
        state = tuple(padded_chords)
        candidates = self.get_possible_next(state, temperature)
        
        if not candidates:
            # Fallback: return a random diatonic chord
            return self._get_random_diatonic_fallback(previous_chords[-1] if previous_chords else None)
        
        return self._weighted_choice(candidates)
    
    def get_possible_next(self, state: Tuple[JazzChord, ...], temperature: float = 1.0) -> Dict[JazzChord, float]:
        """Get possible next chords and their probabilities for a given state"""
        if state not in self._probabilities:
            # Try to find similar states or use fallback
            return self._handle_unknown_state(state)
        
        probabilities = self._probabilities[state].copy()
        
        # Apply temperature
        if temperature != 1.0:
            probabilities = self._apply_temperature(probabilities, temperature)
        
        return probabilities
    
    def _apply_temperature(self, probabilities: Dict[JazzChord, float], temperature: float) -> Dict[JazzChord, float]:
        """Apply temperature to probability distribution"""
        # Convert to list for processing
        chords = list(probabilities.keys())
        probs = np.array([probabilities[chord] for chord in chords])
        
        # Apply temperature scaling
        if temperature > 0:
            scaled_probs = np.power(probs, 1.0 / temperature)
            scaled_probs = scaled_probs / np.sum(scaled_probs)
        else:
            # If temperature is 0, use the most probable chord
            scaled_probs = np.zeros_like(probs)
            scaled_probs[np.argmax(probs)] = 1.0
        
        return {chord: float(scaled_probs[i]) for i, chord in enumerate(chords)}
    
    def _handle_unknown_state(self, state: Tuple[JazzChord, ...]) -> Dict[JazzChord, float]:
        """Handle cases where the state hasn't been seen before"""
        # Strategy 1: Try lower-order Markov chain
        if len(state) > 1:
            lower_state = state[1:]
            if lower_state in self._probabilities:
                return self._probabilities[lower_state]
        
        # Strategy 2: Return global chord frequencies
        return self._get_global_frequencies()
    
    def _get_global_frequencies(self) -> Dict[JazzChord, float]:
        """Get global frequency of all chords in training data"""
        all_chords = []
        for state_probs in self._probabilities.values():
            all_chords.extend(state_probs.keys())
        
        chord_counts = Counter(all_chords)
        total = sum(chord_counts.values())
        return {chord: count / total for chord, count in chord_counts.items()}
    
    def _weighted_choice(self, weighted_dict: Dict[JazzChord, float]) -> JazzChord:
        """Make a weighted random choice"""
        chords, probabilities = zip(*weighted_dict.items())
        return random.choices(chords, weights=probabilities, k=1)[0]
    
    def _pad_sequence(self, chords: List[JazzChord]) -> List[JazzChord]:
        """Pad a sequence to the required order length"""
        if not chords and self.start_states:
            # Use a random common starting sequence
            return list(random.choice(self.start_states))
        
        # Repeat the last chord or use common starts
        while len(chords) < self.order:
            if self.start_states and len(chords) == 0:
                start_chord = random.choice(self.start_states)[0]
                chords.append(start_chord)
            else:
                chords.append(chords[-1] if chords else JazzChord("C", "maj7"))
        
        return chords
    
    def _get_random_diatonic_fallback(self, previous_chord: JazzChord = None) -> JazzChord:
        """Fallback to a random common jazz chord"""
        common_chords = [
            JazzChord("C", "maj7"), JazzChord("D", "m7"), JazzChord("G", "7"),
            JazzChord("A", "m7"), JazzChord("F", "maj7"), JazzChord("E", "m7"),
            JazzChord("A", "7"), JazzChord("B", "m7b5")
        ]
        
        if previous_chord and previous_chord in common_chords:
            # Try to choose a chord that commonly follows the previous one
            common_progressions = {
                "Dm7": "G7", "G7": "Cmaj7", "Am7": "Dm7", 
                "Em7": "A7", "A7": "Dm7", "Bm7b5": "E7"
            }
            prev_str = str(previous_chord)
            if prev_str in common_progressions:
                next_str = common_progressions[prev_str]
                return self._parse_chord_string(next_str)
        
        return random.choice(common_chords)
    
    def _parse_chord_string(self, chord_str: str) -> JazzChord:
        """Parse a chord string into JazzChord object (simplified)"""
        # Simple parser for common chord symbols
        if "m7b5" in chord_str or "ø" in chord_str:
            root = chord_str.replace("m7b5", "").replace("ø", "")
            return JazzChord(root, "m7b5")
        elif "m7" in chord_str or "-7" in chord_str:
            root = chord_str.replace("m7", "").replace("-7", "")
            return JazzChord(root, "m7")
        elif "maj7" in chord_str or "Δ" in chord_str:
            root = chord_str.replace("maj7", "").replace("Δ", "")
            return JazzChord(root, "maj7")
        elif "7" in chord_str:
            root = chord_str.replace("7", "")
            return JazzChord(root, "7")
        else:
            return JazzChord(chord_str, "maj7")  # Default assumption
    
    def generate_sequence(self, length: int = 8, temperature: float = 1.0, 
                         start_sequence: List[JazzChord] = None) -> List[JazzChord]:
        """Generate a complete chord progression"""
        if start_sequence:
            progression = start_sequence.copy()
        else:
            # Start with a common starting sequence
            if self.start_states:
                progression = list(random.choice(self.start_states))
            else:
                progression = [JazzChord("C", "maj7"), JazzChord("F", "maj7")]
        
        while len(progression) < length:
            next_chord = self.predict_next(progression, temperature)
            progression.append(next_chord)
        
        return progression
    
    def get_state_info(self, state: Tuple[JazzChord, ...]) -> Dict:
        """Get information about a particular state"""
        if state in self._probabilities:
            probs = self._probabilities[state]
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            return {
                "state": [str(chord) for chord in state],
                "possible_next": [{"chord": str(chord), "probability": prob} 
                                for chord, prob in sorted_probs[:5]]  # Top 5
            }
        else:
            return {"state": [str(chord) for chord in state], "possible_next": []}
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model to a file"""
        model_data = {
            'order': self.order,
            'transitions': {
                json.dumps([str(chord) for chord in state]): 
                {str(chord): float(prob) for chord, prob in probs.items()}
                for state, probs in self._probabilities.items()
            },
            'chord_vocab': [str(chord) for chord in self.chord_vocab],
            'start_states': [[str(chord) for chord in state] for state in self.start_states]
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """Load a trained model from a file"""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        self.order = model_data['order']
        
        # Reconstruct transitions
        self._probabilities = {}
        for state_str, probs in model_data['transitions'].items():
            state_chords = [self._parse_chord_string(chord_str) 
                          for chord_str in json.loads(state_str)]
            self._probabilities[tuple(state_chords)] = {
                self._parse_chord_string(chord_str): prob 
                for chord_str, prob in probs.items()
            }
        
        # Reconstruct vocabulary and start states
        self.chord_vocab = {self._parse_chord_string(chord_str) 
                          for chord_str in model_data['chord_vocab']}
        self.start_states = [[tuple(self._parse_chord_string(chord_str)) for chord_str in state]
                            for state in model_data['start_states']]

# Example usage and testing
def create_sample_progressions() -> List[List[JazzChord]]:
    """Create sample jazz progressions for testing"""
    
    # Common jazz progressions
    progressions = [
        # ii-V-I progressions in different keys
        [JazzChord("D", "m7"), JazzChord("G", "7"), JazzChord("C", "maj7")],
        [JazzChord("E", "m7"), JazzChord("A", "7"), JazzChord("D", "maj7")],
        [JazzChord("A", "m7"), JazzChord("D", "7"), JazzChord("G", "maj7")],
        
        # Rhythm changes snippet
        [JazzChord("C", "maj7"), JazzChord("A", "7"), JazzChord("D", "m7"), JazzChord("G", "7")],
        [JazzChord("C", "maj7"), JazzChord("A", "7"), JazzChord("D", "m7"), JazzChord("G", "7")],
        
        # Autumn Leaves progression
        [JazzChord("C", "m7"), JazzChord("F", "7"), JazzChord("Bb", "maj7"), JazzChord("Eb", "maj7")],
        [JazzChord("A", "m7b5"), JazzChord("D", "7"), JazzChord("G", "m7")],
        
        # Blues progression snippet
        [JazzChord("C", "7"), JazzChord("F", "7"), JazzChord("C", "7")],
        [JazzChord("G", "7"), JazzChord("F", "7"), JazzChord("C", "7")],
    ]
    
    return progressions

def demo_markov_chain():
    """Demonstrate the Markov chain in action"""
    print("=== Jazz Chord Markov Chain Demo ===\n")
    
    # Create and train the model
    markov = MarkovChain(order=2)
    training_data = create_sample_progressions()
    markov.train(training_data)
    
    # Generate some progressions with different temperatures
    print("\n--- Generated Progressions ---")
    
    temperatures = [0.1, 0.5, 1.0, 1.5, 2.0]
    for temp in temperatures:
        progression = markov.generate_sequence(length=6, temperature=temp)
        progression_str = " | ".join(str(chord) for chord in progression)
        print(f"Temperature {temp:.1f}: {progression_str}")
    
    # Show state information
    print("\n--- State Analysis ---")
    sample_state = (JazzChord("D", "m7"), JazzChord("G", "7"))
    state_info = markov.get_state_info(sample_state)
    print(f"State: {' -> '.join(state_info['state'])}")
    print("Possible next chords:")
    for next_chord in state_info['possible_next']:
        print(f"  {next_chord['chord']}: {next_chord['probability']:.3f}")
    
    # Test prediction
    print("\n--- Prediction Test ---")
    test_sequence = [JazzChord("C", "maj7"), JazzChord("A", "m7")]
    next_chord = markov.predict_next(test_sequence, temperature=1.0)
    sequence_str = " -> ".join(str(chord) for chord in test_sequence)
    print(f"Given: {sequence_str}")
    print(f"Predicted next: {next_chord}")

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


if __name__ == "__main__":
    demo_markov_chain()


