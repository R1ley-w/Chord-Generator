from typing import List


class JazzChord:
    """Represents a jazz chord with root, quality, and extensions"""
    
    def __init__(self, root: str, quality: str = "maj7", extensions: List[str] = None):
        self.root = root
        self.quality = quality
        self.extensions = extensions or []
        
    def normalize(self) -> 'JazzChord':
        """Convert to standard representation"""
        # Standardize quality names
        quality_map = {
            "Δ": "maj7", "ma7": "maj7", "MA7": "maj7",
            "mi7": "m7", "-7": "m7", "min7": "m7",
            "ø": "m7b5", "hdim7": "m7b5",
            "o": "dim7", "dim": "dim7"
        }
        
        normalized_quality = quality_map.get(self.quality, self.quality)
        return JazzChord(self.root, normalized_quality, self.extensions)
    
    def simplify(self) -> 'JazzChord':
        """Remove extensions for basic analysis"""
        # Keep only basic chord quality
        return JazzChord(self.root, self.quality)
    
    def __str__(self):
        ext_str = "".join(self.extensions) if self.extensions else ""
        return f"{self.root}{self.quality}{ext_str}"
    
    def __repr__(self):
        return f"JazzChord('{self.root}', '{self.quality}', {self.extensions})"
    
    def __eq__(self, other):
        if not isinstance(other, JazzChord):
            return False
        return (self.root == other.root and 
                self.quality == other.quality and 
                self.extensions == other.extensions)
    
    def __hash__(self):
        return hash((self.root, self.quality, tuple(sorted(self.extensions))))