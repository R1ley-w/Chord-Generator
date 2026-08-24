import random
import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
import numpy as np
from JazzChord import JazzChord

class MarkovChain:
    """Markov Chain for jazz chord progression generation"""

    # Chord quality names, longest first so "m7b5" wins over "m7", etc.
    _QUALITY_NAMES = ["maj7", "m7b5", "dim7", "7sus4", "7sus2", "m7", "7"]
    # Extension tokens, longest first so "b13" wins over "13", etc.
    _EXTENSION_TOKENS = ["b13", "#11", "b9", "#9", "13", "11", "9"]

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
        """Get possible next chords and their probabilities for a given state.

        Temperature is applied uniformly, including for fallback (unknown
        state) distributions, so it always has an effect.
        """
        probabilities = self._lookup_probabilities(state)
        return self._apply_temperature(probabilities, temperature)

    def _lookup_probabilities(self, state: Tuple[JazzChord, ...]) -> Dict[JazzChord, float]:
        """Return the raw transition distribution for a state, falling back to
        lower-order states and finally global frequencies."""
        if state in self._probabilities:
            return self._probabilities[state].copy()
        return self._handle_unknown_state(state)

    def _apply_temperature(self, probabilities: Dict[JazzChord, float], temperature: float) -> Dict[JazzChord, float]:
        """Rescale a distribution.

        temperature < 1.0 sharpens (more deterministic); temperature > 1.0
        flattens (more exploratory); temperature <= 0 selects the argmax.
        """
        if not probabilities:
            return {}

        chords = list(probabilities.keys())
        probs = np.array([probabilities[chord] for chord in chords], dtype=float)

        if temperature <= 0:
            scaled_probs = np.zeros_like(probs)
            scaled_probs[int(np.argmax(probs))] = 1.0
        else:
            scaled_probs = np.power(probs, 1.0 / temperature)
            scaled_probs /= np.sum(scaled_probs)

        return {chord: float(scaled_probs[i]) for i, chord in enumerate(chords)}

    def _handle_unknown_state(self, state: Tuple[JazzChord, ...]) -> Dict[JazzChord, float]:
        """Handle cases where the state hasn't been seen before.

        Backs off through progressively lower-order states before falling back
        to global chord frequencies.
        """
        for n in range(1, len(state)):
            lower_state = state[n:]
            if lower_state in self._probabilities:
                return self._probabilities[lower_state].copy()

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
    
    def _parse_chord_string(self, chord_str: str) -> Optional[JazzChord]:
        """Parse a chord symbol produced by ``str(JazzChord)``.

        Handles accidental roots (F#, Bb), every quality the model stores, and
        concatenated extensions such as "G79b9" -> JazzChord("G", "7", ["9", "b9"]).
        """
        match = re.match(r'^([A-G][#b]?)(.*)$', chord_str)
        if not match:
            return None

        root, rest = match.groups()
        quality = "maj7"
        for name in self._QUALITY_NAMES:
            if rest.startswith(name):
                quality = name
                rest = rest[len(name):]
                break

        return JazzChord(root, quality, self._parse_extensions(rest))

    def _parse_extensions(self, ext_str: str) -> List[str]:
        """Tokenize a concatenated extension string into individual tensions."""
        extensions = []
        while ext_str:
            for token in self._EXTENSION_TOKENS:
                if ext_str.startswith(token):
                    extensions.append(token)
                    ext_str = ext_str[len(token):]
                    break
            else:
                ext_str = ext_str[1:]
        return extensions

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
        """Load a previously saved model, reconstructing chord objects exactly.

        Probabilities are restored directly (no count round-trip), and state
        keys are parsed with ``_parse_chord_string`` so extended chords such as
        "G79b9" survive the round trip.
        """
        with open(filepath, 'r') as f:
            model_data = json.load(f)

        self.order = model_data['order']
        self._probabilities = {}
        self.transitions = defaultdict(Counter)
        self.chord_vocab = set()

        for state_str, probabilities in model_data['transitions'].items():
            state_chords = [self._parse_chord_string(s) for s in json.loads(state_str)]
            state_chords = [c for c in state_chords if c is not None]
            if not state_chords:
                continue

            state = tuple(state_chords)
            self._probabilities[state] = {}
            for chord in state_chords:
                self.chord_vocab.add(chord)

            for chord_str, prob in probabilities.items():
                chord = self._parse_chord_string(chord_str)
                if chord is None:
                    continue
                self._probabilities[state][chord] = float(prob)
                self.transitions[state][chord] = max(1, int(float(prob) * 100))
                self.chord_vocab.add(chord)

        self.start_states = []
        for state_list in model_data.get('start_states', []):
            chords = [self._parse_chord_string(s) for s in state_list]
            chords = [c for c in chords if c is not None]
            if chords:
                self.start_states.append(tuple(chords))

        print(f"Loaded model: {len(self._probabilities)} states, {len(self.chord_vocab)} chords")

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
    """Self-contained demo that doesn't depend on other files"""
    print("=== Markov Chain Demo ===")
    
    # Create simple test data directly in this file
    test_progressions = [
        [JazzChord("D", "m7"), JazzChord("G", "7"), JazzChord("C", "maj7")],
        [JazzChord("C", "maj7"), JazzChord("A", "m7"), JazzChord("D", "m7"), JazzChord("G", "7")],
    ]
    
    markov = MarkovChain(order=2)
    markov.train(test_progressions)
    
    # Generate a simple progression
    progression = markov.generate_sequence(length=4, temperature=1.0)
    progression_str = " | ".join(str(chord) for chord in progression)
    print(f"Generated: {progression_str}")

if __name__ == "__main__":
    demo_markov_chain()


