# dissonant_melodies.py
from Phrase_Analysis import Note
from typing import List

def create_dissonant_test_melodies() -> List[List[Note]]:
    """Create a collection of dissonant melodies to test the model"""
    
    return [
        # 1. Chromatic Cluster - Very dissonant
        create_chromatic_cluster(),
        
        # 2. Whole Tone Scale - Ambiguous, dreamlike
        create_whole_tone_melody(),
        
        # 3. Tritone Heavy - The "devil's interval"
        create_tritone_melody(),
        
        # 4. Quarter Tone Microtonal - Ultra-dissonant
        create_microtonal_melody(),
        
        # 5. Atonal/Schoenberg-style - No tonal center
        create_atonal_melody(),
        
        # 6. Polytonal - Multiple keys at once
        create_polytonal_melody(),
        
        # 7. Cluster Chords Melody - Dense note clusters
        create_cluster_melody(),
        
        # 8. Free Jazz Style - Wild, unpredictable
        create_free_jazz_melody(),
        
        # 9. Augmented/Diminished Heavy - Unresolved tension
        create_augmented_melody(),
        
        # 10. Mixed Meters - Rhythmic dissonance
        create_mixed_meter_melody()
    ]

def create_chromatic_cluster() -> List[Note]:
    """Chromatic cluster - all notes close together creating maximum dissonance"""
    return [
        Note("C4", 0.0, 1.0), Note("C#4", 1.0, 1.0), Note("D4", 2.0, 1.0),
        Note("D#4", 3.0, 1.0), Note("E4", 4.0, 1.0), Note("F4", 5.0, 1.0),
        Note("F#4", 6.0, 1.0), Note("G4", 7.0, 1.0)
    ]

def create_whole_tone_melody() -> List[Note]:
    """Whole tone scale - no perfect fifths, very ambiguous"""
    return [
        Note("C4", 0.0, 1.0), Note("D4", 1.0, 1.0), Note("E4", 2.0, 1.0),
        Note("F#4", 3.0, 1.0), Note("G#4", 4.0, 1.0), Note("A#4", 5.0, 1.0),
        Note("C5", 6.0, 1.0), Note("D5", 7.0, 1.0)
    ]

def create_tritone_melody() -> List[Note]:
    """Tritone-heavy melody - the most dissonant interval"""
    return [
        Note("C4", 0.0, 2.0), Note("F#4", 2.0, 2.0),  # Tritone
        Note("G4", 4.0, 1.0), Note("C#5", 5.0, 1.0),   # Another tritone
        Note("D4", 6.0, 1.0), Note("G#4", 7.0, 1.0),   # And another
        Note("A4", 8.0, 2.0), Note("D#5", 10.0, 2.0)   # Final tritone
    ]

def create_microtonal_melody() -> List[Note]:
    """Quarter-tone melody - notes between the standard 12-tone scale"""
    # Using pitch bend approximations since we can't do actual quarter tones
    return [
        Note("C4", 0.0, 1.0), Note("C4", 1.0, 1.0),  # Slightly sharp C
        Note("Eb4", 2.0, 1.0), Note("E4", 3.0, 1.0),  # Between Eb and E
        Note("F#4", 4.0, 1.0), Note("G4", 5.0, 1.0),  # Between F# and G
        Note("A4", 6.0, 1.0), Note("Bb4", 7.0, 1.0)   # Between A and Bb
    ]

def create_atonal_melody() -> List[Note]:
    """Atonal melody - no tonal center, Schoenberg-style"""
    return [
        Note("E4", 0.0, 0.5), Note("G4", 0.5, 0.5), Note("Bb4", 1.0, 1.0),
        Note("C#4", 2.0, 0.5), Note("F4", 2.5, 0.5), Note("A4", 3.0, 1.0),
        Note("D4", 4.0, 0.5), Note("F#4", 4.5, 0.5), Note("B4", 5.0, 1.0),
        Note("Eb4", 6.0, 0.5), Note("G#4", 6.5, 0.5), Note("C5", 7.0, 1.0)
    ]

def create_polytonal_melody() -> List[Note]:
    """Polytonal melody - suggests multiple keys simultaneously"""
    # Mixing C major and F# major
    return [
        Note("C4", 0.0, 1.0), Note("E4", 1.0, 1.0),   # C major
        Note("F#4", 2.0, 1.0), Note("A#4", 3.0, 1.0), # F# major
        Note("G4", 4.0, 1.0), Note("B4", 5.0, 1.0),   # C major
        Note("C#5", 6.0, 1.0), Note("E#5", 7.0, 1.0)  # F# major (E# = F)
    ]

def create_cluster_melody() -> List[Note]:
    """Cluster melody - dense groups of adjacent notes"""
    return [
        Note("C4", 0.0, 0.5), Note("C#4", 0.0, 0.5), Note("D4", 0.0, 0.5),  # Cluster
        Note("F4", 1.5, 0.5), Note("F#4", 1.5, 0.5), Note("G4", 1.5, 0.5),  # Cluster
        Note("A4", 3.0, 0.5), Note("A#4", 3.0, 0.5), Note("B4", 3.0, 0.5),  # Cluster
        Note("C5", 4.5, 0.5), Note("C#5", 4.5, 0.5), Note("D5", 4.5, 0.5)   # Cluster
    ]

def create_free_jazz_melody() -> List[Note]:
    """Free jazz style - wild leaps and unpredictable rhythm"""
    return [
        Note("C3", 0.0, 0.3), Note("G5", 0.3, 0.2),   # Huge leap
        Note("Eb4", 0.7, 0.4), Note("B6", 1.2, 0.1),  # Another huge leap
        Note("F#2", 1.5, 0.5), Note("A5", 2.1, 0.3),  # Extreme range
        Note("D4", 2.5, 0.2), Note("F7", 2.8, 0.4),   # Very high note
        Note("G#3", 3.3, 0.6), Note("C8", 4.0, 0.1)   # Extreme high C
    ]

def create_augmented_melody() -> List[Note]:
    """Augmented and diminished heavy - constant tension"""
    return [
        Note("C4", 0.0, 1.0), Note("E4", 1.0, 1.0),   # Major third
        Note("G#4", 2.0, 1.0),                        # Augmented triad
        Note("B4", 3.0, 1.0), Note("D5", 4.0, 1.0),   # Diminished feel
        Note("F#4", 5.0, 1.0), Note("A4", 6.0, 1.0),  # Another augmented
        Note("C#5", 7.0, 1.0)                         # Leading nowhere
    ]

def create_mixed_meter_melody() -> List[Note]:
    """Rhythmic dissonance with mixed meters"""
    return [
        Note("C4", 0.0, 0.75), Note("E4", 0.75, 0.25),  # 3/4 feel
        Note("G4", 1.0, 0.5), Note("Bb4", 1.5, 0.5),    # 2/4 feel  
        Note("C#5", 2.0, 0.33), Note("E5", 2.33, 0.33), Note("G5", 2.66, 0.34),  # 3/8
        Note("A4", 3.0, 1.0),                          # Back to 4/4
        Note("F4", 4.0, 0.2), Note("F#4", 4.2, 0.2), Note("G4", 4.4, 0.2),  # 5/8
        Note("G#4", 4.6, 0.2), Note("A4", 4.8, 0.2)
    ]

# Test function
def test_dissonant_melodies(app):
    """Test the model with all dissonant melodies"""
    melodies = create_dissonant_test_melodies()
    melody_names = [
        "Chromatic Cluster",
        "Whole Tone Scale", 
        "Tritone Heavy",
        "Microtonal",
        "Atonal",
        "Polytonal",
        "Cluster Chords",
        "Free Jazz",
        "Augmented/Diminished",
        "Mixed Meter"
    ]
    
    print("🧪 TESTING DISSONANT MELODIES")
    print("=" * 60)
    
    for i, (melody, name) in enumerate(zip(melodies, melody_names)):
        print(f"\n🎵 Test {i+1}: {name}")
        print(f"   Notes: {[note.pitch for note in melody[:6]]}...")
        
        # Test with conservative setting first
        progression = app.process_user_melody(melody, creativity=0.3)
        
        if progression:
            chords_str = " | ".join(str(chord) for chord in progression[:6])
            print(f"   🎹 Generated: {chords_str}...")
            
            # Analyze how well it handled the dissonance
            analyze_dissonance_handling(progression, melody)
        else:
            print("   ❌ No progression generated")

def analyze_dissonance_handling(progression, melody):
    """Analyze how well the model handled the dissonant melody"""
    # Simple analysis - check if progression uses extended harmonies
    extended_chords = 0
    chromatic_chords = 0
    
    for chord in progression:
        # Count chords with extensions
        if chord.extensions:
            extended_chords += 1
        
        # Count chords that might be chromatic alterations
        if any('b' in ext or '#' in ext for ext in chord.extensions):
            chromatic_chords += 1
        if chord.quality in ['m7b5', 'dim7']:
            chromatic_chords += 1
    
    total_chords = len(progression)
    
    print(f"   📊 Analysis:")
    print(f"      • {extended_chords}/{total_chords} chords have extensions")
    print(f"      • {chromatic_chords}/{total_chords} chords are chromatic/altered")
    
    if extended_chords > total_chords * 0.5:
        print("      ✅ Good: Using extended harmonies for dissonance")
    if chromatic_chords > total_chords * 0.3:
        print("      ✅ Good: Using chromaticism to match melody")

# Quick usage in your main app
def add_dissonance_testing_to_app(app):
    """Add dissonance testing to your existing app"""
    
    def test_dissonance():
        print("\n" + "="*50)
        print("DISSONANCE TESTING MODE")
        print("="*50)
        
        test_dissonant_melodies(app)
    
    # Add this method to your app
    app.test_dissonant_melodies = test_dissonance
    return app

# Example usage:
if __name__ == "__main__":
    # Assuming you have your app instance
    from main_app2 import JazzChordGeneratorApp
    
    app = JazzChordGeneratorApp("trained_jazz_model.json", order = 3)
    app = add_dissonance_testing_to_app(app)
    
    # Run the tests
    app.test_dissonant_melodies()