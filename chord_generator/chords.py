"""Chord model and chord-symbol parsing."""

import re
from typing import List, Optional

# Canonical chord qualities. Longest first so "m7b5" wins over "m7" when parsing.
QUALITY_NAMES = ["maj7", "m7b5", "dim7", "7sus4", "7sus2", "m7", "7"]

# Every spelling accepted across the codebase, mapped to a canonical quality.
QUALITY_SYNONYMS = {
    "maj7": "maj7", "maj": "maj7", "M7": "maj7", "M": "maj7", "Δ": "maj7",
    "ma7": "maj7", "MA7": "maj7", "6": "maj7",
    "m7": "m7", "m": "m7", "min": "m7", "mi": "m7", "mi7": "m7", "min7": "m7",
    "-": "m7", "-7": "m7",
    "7": "7", "dom": "7", "dom7": "7",
    "m7b5": "m7b5", "ø": "m7b5", "hdim": "m7b5", "hdim7": "m7b5", "min7b5": "m7b5",
    "dim7": "dim7", "dim": "dim7", "°": "dim7", "°7": "dim7", "o": "dim7",
    "7sus4": "7sus4", "sus4": "7sus4", "sus": "7sus4",
    "7sus2": "7sus2", "sus2": "7sus2",
}

# Extension tokens, longest first so "b13" wins over "13" when parsing.
EXTENSION_TOKENS = ["b13", "#11", "b9", "#9", "13", "11", "9"]

_SYNONYM_KEYS = sorted(QUALITY_SYNONYMS.keys(), key=len, reverse=True)


class JazzChord:
    """Represents a jazz chord with root, quality, and extensions"""

    def __init__(self, root: str, quality: str = "maj7", extensions: List[str] = None):
        self.root = root
        self.quality = quality
        self.extensions = extensions or []

    def normalize(self) -> 'JazzChord':
        """Return a chord whose quality uses a canonical name."""
        return JazzChord(
            self.root,
            QUALITY_SYNONYMS.get(self.quality, self.quality),
            self.extensions,
        )

    def simplify(self) -> 'JazzChord':
        """Return the chord without extensions."""
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


def parse_chord_symbol(symbol: str) -> Optional[JazzChord]:
    """Parse a chord symbol like 'G79b9', 'F#m7b5', or 'CΔ' into a JazzChord.

    Handles accidental roots, every quality the model stores, and concatenated
    extensions such as "G79b9" -> JazzChord("G", "7", ["9", "b9"]).
    """
    match = re.match(r'^([A-G][#b]?)(.*)$', symbol.strip())
    if not match:
        return None

    root, rest = match.groups()

    quality = "maj7"
    for key in _SYNONYM_KEYS:
        if rest.startswith(key):
            quality = QUALITY_SYNONYMS[key]
            rest = rest[len(key):]
            break
    else:
        # Bare extension (e.g. "C13", "C9") means a dominant seventh chord.
        if rest and rest[0].isdigit():
            quality = "7"

    return JazzChord(root, quality, _parse_extensions(rest))


def _parse_extensions(ext_str: str) -> List[str]:
    """Tokenize a concatenated extension string into individual tensions."""
    extensions = []
    while ext_str:
        for token in EXTENSION_TOKENS:
            if ext_str.startswith(token):
                extensions.append(token)
                ext_str = ext_str[len(token):]
                break
        else:
            ext_str = ext_str[1:]
    return extensions
