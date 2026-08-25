#!/usr/bin/env bash
set -euo pipefail

# Download a small General MIDI SoundFont so the web app can synthesize MP3
# playback from MIDI. Output goes to data/soundfonts/, which the app searches.

DEST_DIR="$(cd "$(dirname "$0")/.." && pwd)/data/soundfonts"
mkdir -p "$DEST_DIR"

URL="https://raw.githubusercontent.com/arbruijn/TimGM6mb/master/TimGM6mb.sf2"
OUT="$DEST_DIR/TimGM6mb.sf2"

if [[ -f "$OUT" ]]; then
  echo "SoundFont already present: $OUT"
  exit 0
fi

echo "Downloading TimGM6mb.sf2 (~6 MB)..."
curl -L "$URL" -o "$OUT"
echo "Downloaded: $OUT"
