from JazzChord import JazzChord


def diagnose_model(app):
    """Run diagnostics on the loaded model"""
    print("\n" + "="*50)
    print("MODEL DIAGNOSTICS")
    print("="*50)
    
    markov = app.markov_chain
    
    # Check key properties
    print(f"Transitions count: {len(markov.transitions)}")
    print(f"Probabilities count: {len(markov._probabilities)}")
    print(f"Chord vocabulary: {len(markov.chord_vocab)}")
    print(f"Start states: {len(markov.start_states)}")
    
    # Test if generation works
    print(f"\n🧪 Testing generation:")
    try:
        progression = markov.generate_sequence(length=4, temperature=0.5)
        print(f"   Generated: {' | '.join(str(chord) for chord in progression)}")
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
    
    # Check if we have extended chords in vocabulary
    extended_chords = []
    for chord in markov.chord_vocab:
        if chord.extensions or 'b' in chord.quality or '#' in chord.quality:
            extended_chords.append(str(chord))
    
    print(f"\n🎹 Extended chords in vocabulary:")
    if extended_chords:
        for chord in extended_chords[:10]:  # Show first 10
            print(f"   • {chord}")
    else:
        print("   ⚠️ No extended chords found!")
    
    # Test specific state predictions
    print(f"\n🔍 Testing state predictions:")
    test_state = (JazzChord("D", "m7"), JazzChord("G", "7"))
    if test_state in markov._probabilities:
        predictions = markov.get_possible_next(test_state, temperature=1.0)
        print(f"   Dm7 → G7 → ? :")
        for chord, prob in sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"      {chord}: {prob:.3f}")
    else:
        print("   ⚠️ Test state not found in model")