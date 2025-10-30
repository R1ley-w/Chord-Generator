# jazz_standards_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, urlparse
import os
from Markov_Chain_For_Chords import JazzChord
from key_detector import ScaleDetector
import random

class JazzStandardsScraper:
    """Scrapes jazz standards from public archives and converts to training data"""
    
    def __init__(self, data_dir: str = "jazz_standards_data"):
        self.data_dir = data_dir
        self.scale_detector = ScaleDetector()
        os.makedirs(data_dir, exist_ok=True)
        
        # Common jazz chord mappings for normalization
        self.chord_mappings = {
            # Major chords
            "maj": "maj7", "M": "maj7", "M7": "maj7", "Δ": "maj7", "ma7": "maj7",
            # Minor chords  
            "m": "m7", "min": "m7", "mi": "m7", "mi7": "m7", "-": "m7", "-7": "m7",
            # Dominant chords
            "dom": "7", "dom7": "7",
            # Half-diminished
            "ø": "m7b5", "hdim": "m7b5", "min7b5": "m7b5",
            # Diminished
            "dim": "dim7", "°": "dim7", "°7": "dim7",
            # Suspended
            "sus": "7sus4", "sus4": "7sus4", "sus2": "7sus2"
        }
    
    def scrape_jazzstandards_com(self) -> List[Dict]:
        """Scrape from jazzstandards.com"""
        print("Scraping jazzstandards.com...")
        
        base_url = "http://www.jazzstandards.com"
        standards = []
        
        try:
            # Get the list of standards by year
            years = [1910, 1920, 1930, 1940, 1950, 1960]

            indices = []
            
            for year in years:
                url = f"{base_url}/compositions/{year}.htm"
                print(f"  Scraping {year}s standards...")
                
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find links to individual standards
                links = soup.find_all('a', href=re.compile(r'^/compositions/'))
                
                for link in links:
                    if link.text.strip():
                        standard_info = self._scrape_individual_standard(base_url, link['href'])
                        if standard_info:
                            standards.append(standard_info)
                            print(f"    ✓ {standard_info['title']}")
                        
                        time.sleep(1)  # Be polite
                
                time.sleep(2)
                
        except Exception as e:
            print(f"Error scraping jazzstandards.com: {e}")
        
        return standards
    
    def _scrape_individual_standard(self, base_url: str, path: str) -> Optional[Dict]:
        """Scrape an individual standard page"""
        try:
            url = urljoin(base_url, path)
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            if not title:
                return None
                
            title = title.text.strip()
            
            # Look for chord progression (this is site-specific)
            progression = self._extract_chords_from_jazzstandards(soup)
            
            if progression:
                return {
                    'title': title,
                    'progression': progression,
                    'source': 'jazzstandards.com',
                    'url': url
                }
            
        except Exception as e:
            print(f"Error scraping {path}: {e}")
        
        return None
    
    def scrape_wikifonia_archives(self) -> List[Dict]:
        """Scrape from Wikifonia archives (public domain)"""
        print("Scraping Wikifonia archives...")
        
        # Wikifonia was a public domain sheet music repository
        # We'll use archived versions
        standards = []
        
        # Known Wikifonia mirror sites
        mirrors = [
            "http://wikifonia.org",
            "https://wikifonia.github.io"
        ]
        
        for mirror in mirrors:
            try:
                response = requests.get(mirror, timeout=10)
                if response.status_code == 200:
                    print(f"  Found active mirror: {mirror}")
                    # Implementation would depend on the specific mirror structure
                    break
            except:
                continue
        
        # For now, return empty - we'll use MusicXML parsing instead
        return standards
    
    def scrape_music_xml_repositories(self) -> List[Dict]:
        """Scrape from MusicXML repositories"""
        print("Searching for MusicXML files...")
        
        # Some public repositories with jazz standards in MusicXML
        repositories = [
            "https://github.com/cuthbertLab/music21/tree/master/music21/corpus",
            "https://freemusicarchive.org/genre/Jazz/",
        ]
        
        # This would require more complex implementation
        # For now, we'll use a simpler approach with known standards
        
        return []
    
    def parse_music_xml_file(self, file_path: str) -> Optional[Dict]:
        """Parse a MusicXML file to extract chords and melody"""
        try:
            # This would use music21 library for proper MusicXML parsing
            # For now, we'll implement a simpler version
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple chord extraction from MusicXML
            chords = self._extract_chords_from_musicxml(content)
            
            if chords:
                return {
                    'title': os.path.basename(file_path).replace('.xml', ''),
                    'progression': chords,
                    'source': 'musicxml',
                    'file_path': file_path
                }
                
        except Exception as e:
            print(f"Error parsing MusicXML {file_path}: {e}")
        
        return None
    
    def scrape_ireal_pro_formats(self) -> List[Dict]:
        """Scrape from iReal Pro format repositories"""
        print("Searching for iReal Pro formats...")
        
        # iReal Pro uses a specific text format for chord progressions
        ireal_urls = [
            "https://www.irealpro.com/main-playlists",
            "https://github.com/topics/ireal-pro",
        ]
        
        standards = []
        
        # Sample iReal Pro format parser
        sample_ireal = "Autumn Leaves=1b2-5|Cm7|F7|BbM7|EbM7|Am7b5|D7|Gm7"
        parsed = self._parse_ireal_pro_format(sample_ireal)
        if parsed:
            standards.append(parsed)
        
        return standards
    
    def _parse_ireal_pro_format(self, ireal_text: str) -> Optional[Dict]:
        """Parse iReal Pro text format"""
        try:
            # Format: "Song Title=Style|Chord1|Chord2|..."
            if '=' not in ireal_text:
                return None
            
            title_part, chords_part = ireal_text.split('=', 1)
            title = title_part.strip()
            
            # Split by | and ignore style code
            chords_str = chords_part.split('|')[1:]  # Skip style code
            
            chords = []
            for chord_str in chords_str:
                if chord_str.strip():
                    jazz_chord = self._parse_chord_symbol(chord_str.strip())
                    if jazz_chord:
                        chords.append(jazz_chord)
            
            if chords:
                return {
                    'title': title,
                    'progression': chords,
                    'source': 'ireal_pro'
                }
                
        except Exception as e:
            print(f"Error parsing iReal format: {e}")
        
        return None
    
    def _parse_chord_symbol(self, chord_str: str) -> Optional[JazzChord]:
        """Parse a chord symbol into JazzChord object"""
        try:
            # Remove parentheses and other non-essential characters
            chord_str = re.sub(r'[()]', '', chord_str)
            
            # Extract root note
            root_match = re.match(r'^([A-G][#b]?)', chord_str)
            if not root_match:
                return None
                
            root = root_match.group(1)
            rest = chord_str[len(root):]
            
            # Map to standard quality
            quality = "maj7"  # Default
            
            # Check for specific quality patterns
            for pattern, standard_quality in self.chord_mappings.items():
                if pattern in rest:
                    quality = standard_quality
                    break
            
            # Handle extensions
            extensions = []
            ext_patterns = {
                '9': '9', '11': '11', '13': '13',
                'b9': 'b9', '#9': '#9', '#11': '#11', 'b13': 'b13'
            }
            
            for ext_pattern, ext_name in ext_patterns.items():
                if ext_pattern in rest:
                    extensions.append(ext_name)
            
            return JazzChord(root, quality, extensions)
            
        except Exception as e:
            print(f"Error parsing chord '{chord_str}': {e}")
            return None
    
    def _extract_chords_from_jazzstandards(self, soup) -> List[JazzChord]:
        """Extract chords from jazzstandards.com page (site-specific)"""
        chords = []
        
        try:
            # Look for chord progression in various common formats
            text_elements = soup.find_all(['p', 'div', 'pre'])
            
            for element in text_elements:
                text = element.get_text()
                
                # Common chord progression patterns
                chord_patterns = [
                    r'[A-G][#b]?(?:maj7?|m7?|7|m7b5|dim7?|sus[24]?)(?:[#b]?\d+)*',
                    r'[A-G][#b]?(?:-7?|Δ|ø|°)(?:[#b]?\d+)*'
                ]
                
                for pattern in chord_patterns:
                    chord_matches = re.findall(pattern, text)
                    for chord_match in chord_matches:
                        jazz_chord = self._parse_chord_symbol(chord_match)
                        if jazz_chord:
                            chords.append(jazz_chord)
                
                # If we found chords, break
                if chords:
                    break
                    
        except Exception as e:
            print(f"Error extracting chords: {e}")
        
        return chords
    
    def create_sample_standards_dataset(self) -> List[Dict]:
        """Create a sample dataset of well-known jazz standards"""
        print("Creating sample jazz standards dataset...")
        
        sample_standards = [
            {
                'title': "Autumn Leaves",
                'progression': [
                    JazzChord("C", "m7"), JazzChord("F", "7"), 
                    JazzChord("Bb", "maj7"), JazzChord("Eb", "maj7"),
                    JazzChord("A", "m7b5"), JazzChord("D", "7"), 
                    JazzChord("G", "m7")
                ],
                'source': 'sample'
            },
            {
                'title': "All The Things You Are",
                'progression': [
                    JazzChord("F", "m7"), JazzChord("Bb", "m7"), 
                    JazzChord("Eb", "7"), JazzChord("Ab", "maj7"),
                    JazzChord("Db", "maj7"), JazzChord("C", "7"),
                    JazzChord("F", "maj7"), JazzChord("Bb", "7")
                ],
                'source': 'sample'
            },
            {
                'title': "Blue Bossa",
                'progression': [
                    JazzChord("C", "m7"), JazzChord("F", "m7"),
                    JazzChord("D", "m7b5"), JazzChord("G", "7"),
                    JazzChord("Eb", "m7"), JazzChord("Ab", "7"),
                    JazzChord("Db", "maj7"), JazzChord("Db", "maj7")
                ],
                'source': 'sample'
            },
            {
                'title': "Take The A Train",
                'progression': [
                    JazzChord("C", "maj7"), JazzChord("C", "maj7"),
                    JazzChord("D", "m7"), JazzChord("G", "7"),
                    JazzChord("D", "m7"), JazzChord("G", "7"),
                    JazzChord("E", "m7"), JazzChord("A", "7")
                ],
                'source': 'sample'
            },
            {
                'title': "So What",
                'progression': [
                    JazzChord("D", "m7"), JazzChord("D", "m7"),
                    JazzChord("D", "m7"), JazzChord("D", "m7"),
                    JazzChord("Eb", "m7"), JazzChord("Eb", "m7"),
                    JazzChord("D", "m7"), JazzChord("D", "m7")
                ],
                'source': 'sample'
            },
            {
                'title': "Blue Monk",
                'progression': [
                    JazzChord("Bb", "7"), JazzChord("Eb", "7"),
                    JazzChord("Bb", "7"), JazzChord("Bb", "7"),
                    JazzChord("Eb", "7"), JazzChord("Eb", "7"),
                    JazzChord("Bb", "7"), JazzChord("G", "7"),
                    JazzChord("C", "7"), JazzChord("F", "7")
                ],
                'source': 'sample'
            }
        ]
        
        # Add more standards
        more_standards = [
            ("Summertime", ["Am7", "Em7", "Am7", "Em7", "C", "G", "Am7", "Em7"]),
            ("All Blues", ["G7", "G7", "G7", "G7", "C7", "C7", "G7", "G7"]),
            ("Mr. PC", ["Cm7", "Cm7", "Cm7", "Cm7", "Fm7", "Fm7", "Cm7", "Cm7"]),
            ("Song For My Father", ["F#m7", "F#m7", "B7", "B7", "F#m7", "F#m7", "C#7", "C#7"]),
            ("Watermelon Man", ["Cm7", "Cm7", "Cm7", "Cm7", "F7", "F7", "Cm7", "Cm7"]),
        ]
        
        for title, chord_strings in more_standards:
            progression = []
            for chord_str in chord_strings:
                jazz_chord = self._parse_chord_symbol(chord_str)
                if jazz_chord:
                    progression.append(jazz_chord)
            
            if progression:
                sample_standards.append({
                    'title': title,
                    'progression': progression,
                    'source': 'sample'
                })
        
        print(f"Created {len(sample_standards)} sample standards")
        return sample_standards
    
    def save_standards(self, standards: List[Dict], filename: str = "jazz_standards.json"):
        """Save standards to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
        # Convert to serializable format
        serializable_standards = []
        for standard in standards:
            serializable_standard = standard.copy()
            serializable_standard['progression'] = [
                {
                    'root': chord.root,
                    'quality': chord.quality,
                    'extensions': chord.extensions
                }
                for chord in standard['progression']
            ]
            serializable_standards.append(serializable_standard)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_standards, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(standards)} standards to {filepath}")
    
    def load_standards(self, filename: str = "jazz_standards.json") -> List[Dict]:
        """Load standards from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert back to JazzChord objects
            standards = []
            for item in data:
                progression = [
                    JazzChord(
                        chord_data['root'],
                        chord_data['quality'],
                        chord_data.get('extensions', [])
                    )
                    for chord_data in item['progression']
                ]
                
                standard = {
                    'title': item['title'],
                    'progression': progression,
                    'source': item.get('source', 'unknown')
                }
                if 'url' in item:
                    standard['url'] = item['url']
                
                standards.append(standard)
            
            print(f"Loaded {len(standards)} standards from {filepath}")
            return standards
            
        except FileNotFoundError:
            print(f"File {filepath} not found")
            return []
        except Exception as e:
            print(f"Error loading standards: {e}")
            return []
    
    def convert_to_training_data(self, standards: List[Dict]) -> List[List[JazzChord]]:
        """Convert standards to training data format for Markov chain"""
        training_data = []
        
        for standard in standards:
            progression = standard['progression']
            if len(progression) >= 3:  # Need at least 3 chords for meaningful sequences
                training_data.append(progression)
        
        print(f"Converted {len(training_data)} progressions to training data")
        return training_data
    
    def analyze_standards(self, standards: List[Dict]):
        """Analyze the collected standards"""
        print("\n" + "="*50)
        print("JAZZ STANDARDS ANALYSIS")
        print("="*50)
        
        total_standards = len(standards)
        total_chords = sum(len(std['progression']) for std in standards)
        
        print(f"Total standards: {total_standards}")
        print(f"Total chords: {total_chords}")
        print(f"Average chords per standard: {total_chords/total_standards:.1f}")
        
        # Analyze chord distribution
        chord_counts = {}
        for standard in standards:
            for chord in standard['progression']:
                chord_str = str(chord)
                chord_counts[chord_str] = chord_counts.get(chord_str, 0) + 1
        
        print(f"\nMost common chords:")
        for chord, count in sorted(chord_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {chord}: {count} times")
        
        # Analyze progression lengths
        lengths = [len(std['progression']) for std in standards]
        print(f"\nProgression length stats:")
        print(f"  Min: {min(lengths)} chords")
        print(f"  Max: {max(lengths)} chords") 
        print(f"  Avg: {sum(lengths)/len(lengths):.1f} chords")

def main():
    """Main function to run the scraper"""
    scraper = JazzStandardsScraper()
    
    print("🎷 Jazz Standards Scraper")
    print("=" * 40)
    
    # Try to scrape from online sources
    print("1. Scraping online sources...")
    online_standards = []
    
    online_standards.extend(scraper.scrape_jazzstandards_com())
    online_standards.extend(scraper.scrape_ireal_pro_formats())
    
    # Create sample dataset (fallback)
    print("\n2. Creating sample dataset...")
    sample_standards = scraper.create_sample_standards_dataset()
    
    # Combine all standards
    all_standards = online_standards + sample_standards
    
    print(f"\n3. Total collected: {len(all_standards)} standards")
    
    # Save standards
    scraper.save_standards(all_standards)
    
    # Analyze standards
    scraper.analyze_standards(all_standards)
    
    # Convert to training data
    training_data = scraper.convert_to_training_data(all_standards)
    
    print(f"\n4. Training data: {len(training_data)} progressions")
    
    # Save training data
    training_file = os.path.join(scraper.data_dir, "training_data.json")
    with open(training_file, 'w') as f:
        json.dump([[str(chord) for chord in progression] for progression in training_data], f)
    
    print(f"✅ Training data saved to {training_file}")
    print("\n🎉 Scraping complete! Ready to train your model.")

if __name__ == "__main__":
    main()