from phrase_aware_markove_chain import PhraseAwareMarkovChain
from JazzChord import JazzChord
from Phrase_Analysis import Note, BeatStrength, PhraseAnalyzer, Phrase
from typing import List, Tuple, Dict

#!/usr/bin/env python3
"""
Separate script to train and save the phrase-aware Markov model
This should be run once to create the trained model file
"""

from JazzHarmonizer import JazzHarmonizer, create_training_data_with_phrases
import pickle

def train_and_save_model():
    """Train the phrase-aware model and save it to disk"""
    
    # Create the harmonizer
    harmonizer = JazzHarmonizer()
    
    # STEP 5: Create enhanced training data
    print("Loading and processing jazz standards with phrase analysis...")
    progressions, phrase_analyses = create_training_data_with_phrases()
    
    print(f"Training on {len(progressions)} progressions with phrase context...")
    
    # Train the model
    harmonizer.markov_chain.train_with_phrases(progressions, phrase_analyses)
    
    # Save the trained model
    with open('trained_jazz_model.pkl', 'wb') as f:
        pickle.dump(harmonizer.markov_chain, f)
    
    print("Model trained and saved successfully!")
    print(f"Learned {len(harmonizer.markov_chain.phrase_transitions)} phrase-aware states")
    
    return harmonizer

if __name__ == "__main__":
    train_and_save_model()