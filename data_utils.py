# data_utils.py
import random
from typing import List
from Markov_Chain_For_Chords import JazzChord

def create_sample_progressions() -> List[List[JazzChord]]:
    """Create sample jazz progressions for testing"""
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

def create_training_data_with_phrases():
    """Placeholder - you'll implement this later"""
    print("Warning: create_training_data_with_phrases not fully implemented yet")
    return create_sample_progressions(), []