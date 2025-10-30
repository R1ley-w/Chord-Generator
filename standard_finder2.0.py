# json_standards_parser.py
import json
import re
from typing import List, Dict, Any
from Markov_Chain_For_Chords import JazzChord, MarkovChain

class JazzStandardsParser:
    """Parser for the jazz standards JSON format with sections and chords"""
    
    def __init__(self):
        self.chord_mappings = {
            # Major chords
            "6": "maj7", "M": "maj7", "M7": "maj7", "Δ": "maj7",
            # Minor chords
            "m": "m7", "mi": "m7", "min": "m7", "-": "m7",
            # Dominant chords
            "dom": "7", "dom7": "7",
            # Half-diminished
            "ø": "m7b5", "hdim": "m7b5", "min7b5": "m7b5",
            # Diminished
            "dim": "dim7", "°": "dim7",
            # Suspended
            "sus": "7sus4", "sus4": "7sus4", "sus2": "7sus2"
        }
    
    def parse_json_file(self, file_path: str) -> List[List[JazzChord]]:
        """Parse the JSON file and extract chord progressions for training"""
        print(f"🎷 Parsing jazz standards from {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_progressions = []
            
            for standard in data:
                title = standard.get("Title", "Unknown")
                composer = standard.get("Composer", "Unknown")
                sections = standard.get("Sections", [])
                
                # Extract chords from all sections
                progression = self._extract_chords_from_sections(sections)
                
                if progression:
                    all_progressions.append(progression)
                    print(f"  ✓ {title} - {len(progression)} chords")
                else:
                    print(f"  ⚠ {title} - No chords extracted")
            
            print(f"✅ Extracted {len(all_progressions)} progressions from {len(data)} standards")
            return all_progressions
            
        except Exception as e:
            print(f"❌ Error parsing JSON file: {e}")
            return []
    
    def _extract_chords_from_sections(self, sections: List[Dict]) -> List[JazzChord]:
        """Extract chords from all sections of a standard"""
        all_chords = []
        
        for section in sections:
            # Process main segment
            main_segment = section.get("MainSegment", {})
            if main_segment and "Chords" in main_segment:
                chords = self._parse_chord_string(main_segment["Chords"])
                all_chords.extend(chords)
            
            # Process endings
            endings = section.get("Endings", [])
            for ending in endings:
                if "Chords" in ending:
                    chords = self._parse_chord_string(ending["Chords"])
                    all_chords.extend(chords)
        
        return all_chords
    
    def _parse_chord_string(self, chord_string: str) -> List[JazzChord]:
        """Parse a chord string like 'D9|Fm6|D9|Fm6|C|C7,B7,Bb7,A7' into JazzChord objects"""
        chords = []
        
        # Split by bars (|) and then by chords within bars (,)
        bars = chord_string.split('|')
        
        for bar in bars:
            bar = bar.strip()
            if not bar:
                continue
            
            # Split multiple chords in same bar (comma-separated)
            bar_chords = bar.split(',')
            
            for chord_str in bar_chords:
                chord_str = chord_str.strip()
                if chord_str:
                    jazz_chord = self._parse_single_chord(chord_str)
                    if jazz_chord:
                        chords.append(jazz_chord)
        
        return chords
    
    def _parse_single_chord(self, chord_str: str):
        """Parse a single chord symbol into JazzChord object"""
        try:
            # Clean the chord string
            chord_str = chord_str.strip()
            if not chord_str:
                return None
            
            # Extract root note (first character plus optional # or b)
            root_match = re.match(r'^([A-G][#b]?)', chord_str)
            if not root_match:
                return None
            
            root = root_match.group(1)
            rest = chord_str[len(root):]
            
            # Handle special cases and map to standard quality
            quality = self._determine_chord_quality(rest)
            
            # Extract extensions
            extensions = self._extract_extensions(rest)
            
            return JazzChord(root, quality, extensions)
            
        except Exception as e:
            print(f"    Warning: Could not parse chord '{chord_str}': {e}")
            return None
    
    def _determine_chord_quality(self, rest: str) -> str:
        """Determine the chord quality from the remaining part of the chord symbol"""
        # Default to dominant 7th if no quality specified but has extensions
        if not rest:
            return "7"
        
        # Check for specific quality indicators
        quality_indicators = {
            # Major types
            "6": "maj7",  # In jazz, 6 often implies maj7 context
            "M7": "maj7", "M": "maj7", "Δ": "maj7",
            # Minor types  
            "m7": "m7", "m": "m7", "mi": "m7", "min": "m7", "-7": "m7", "-": "m7",
            # Dominant types
            "7": "7", "9": "7", "11": "7", "13": "7",
            # Half-diminished
            "m7b5": "m7b5", "ø": "m7b5", "hdim": "m7b5",
            # Diminished
            "dim": "dim7", "°": "dim7",
            # Suspended
            "sus": "7sus4", "sus4": "7sus4", "sus2": "7sus2"
        }
        
        # Look for quality indicators in order of specificity
        for indicator, quality in quality_indicators.items():
            if indicator in rest:
                return quality
        
        # If we have a number but no other quality, assume dominant
        if any(char.isdigit() for char in rest):
            return "7"
        
        # Default to major 7th for chords with just a root
        return "maj7"
    
    def _extract_extensions(self, rest: str) -> List[str]:
        """Extract chord extensions from the chord symbol"""
        extensions = []
        
        extension_patterns = {
            "9": "9", "11": "11", "13": "13",
            "b9": "b9", "#9": "#9", 
            "#11": "#11", 
            "b13": "b13"
        }
        
        for pattern, ext_name in extension_patterns.items():
            if pattern in rest:
                extensions.append(ext_name)
        
        return extensions

class JazzStandardsTrainer:
    """Trains Markov chain using jazz standards data"""
    
    def __init__(self):
        self.parser = JazzStandardsParser()
        self.markov_chain = MarkovChain(order=2)
    
    def train_from_json(self, json_file_path: str) -> MarkovChain:
        """Train Markov chain from JSON standards file"""
        print("🎯 Training Markov chain from jazz standards...")
        
        # Parse the JSON file
        training_data = self.parser.parse_json_file(json_file_path)
        
        if not training_data:
            print("❌ No training data found!")
            return self.markov_chain
        
        # Train the Markov chain
        self.markov_chain.train(training_data)
        
        # Print training statistics
        self._print_training_stats(training_data)
        
        return self.markov_chain
    
    def _print_training_stats(self, training_data: List[List[JazzChord]]):
        """Print statistics about the training data"""
        total_standards = len(training_data)
        total_chords = sum(len(prog) for prog in training_data)
        avg_chords = total_chords / total_standards if total_standards > 0 else 0
        
        print(f"\n📊 Training Statistics:")
        print(f"   • {total_standards} jazz standards")
        print(f"   • {total_chords} total chords")
        print(f"   • {avg_chords:.1f} chords per standard")
        print(f"   • {len(self.markov_chain.transitions)} Markov states learned")
        
        # Show chord distribution
        chord_counts = {}
        for progression in training_data:
            for chord in progression:
                chord_str = str(chord)
                chord_counts[chord_str] = chord_counts.get(chord_str, 0) + 1
        
        print(f"\n🎹 Most common chords:")
        for chord, count in sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {chord}: {count} times")
    
    def test_generation(self, num_sequences: int = 5):
        """Test chord progression generation"""
        print(f"\n🧪 Generating {num_sequences} sample progressions:")
        
        for i in range(num_sequences):
            progression = self.markov_chain.generate_sequence(
                length=8, 
                temperature=0.5 + (i * 0.1)  # Vary creativity
            )
            chords_str = " | ".join(str(chord) for chord in progression)
            print(f"   {i+1}. {chords_str}")

# Example usage with your specific JSON format
def main():
    """Main function to train from JSON standards file"""
    
    # Initialize trainer
    trainer = JazzStandardsTrainer()
    
    # Path to your JSON file - update this to your actual file path
    json_file_path = "/Users/rileywade/Documents/MUSIC APP/Chord-Generator/JazzStandards/JazzStandards.json"  # Change this to your actual file path
    
    # Train the model
    markov_chain = trainer.train_from_json(json_file_path)
    
    # Test generation
    trainer.test_generation()
    
    # Save the trained model
    markov_chain.save_model("trained_jazz_model.json")
    print(f"\n💾 Model saved to 'trained_jazz_model.json'")
    
    return markov_chain

# Alternative: If you want to use this in your main app
def integrate_with_main_app(json_file_path: str):
    """Integrate this parser with your main application"""
    trainer = JazzStandardsTrainer()
    markov_chain = trainer.train_from_json(json_file_path)
    
    # Now you can use markov_chain in your main app
    return markov_chain

if __name__ == "__main__":
    main()