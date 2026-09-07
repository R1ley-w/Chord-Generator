# Jazz Chord Generator

Given a melody (any sequence of notes), generate a jazz chord progression that
harmonizes it. A Markov chain trained on jazz standards proposes chords, which
are then shaped by key detection, phrase analysis, and a user-controlled
"creativity" factor.

## How it works

The app has three main pillars:

1. **Input** — a user-defined sequence of notes (a melody).
2. **Processing** — a model that generates a *context-aware chord progression*
   (harmony) based on the melody and a creativity level.
3. **Output** — a rhythmic arrangement of the generated progression for
   playback and experimentation.

The processing pipeline is:

```
melody notes
    ├─ key detection      → detect the key/scale (Krumhansl-Schmuckler)
    ├─ phrase analysis    → find phrases and chord-change points
    └─ Markov chain       → propose chords, then...
         ├─ key constraints   → snap to diatonic chords (low creativity)
         ├─ harmonic color    → add tensions / tritone subs (high creativity)
         └─ melody harmony    → re-harmonize if a chord clashes with the melody
```

## Project structure

```
.
├── main.py                     # CLI entry point (demo / interactive)
├── webapp.py                   # Gradio web UI entry point
├── chord_generator/            # the source package
│   ├── __init__.py             # public API
│   ├── app.py                  # JazzChordGeneratorApp (orchestration)
│   ├── gradio_app.py           # Gradio web UI
│   ├── audio.py                # MIDI + MP3 rendering (midiutil/FluidSynth)
│   ├── chords.py               # JazzChord data model
│   ├── markov_chain.py         # MarkovChain (training + prediction)
│   ├── key_detector.py         # ScaleDetector, Key, ScaleType
│   ├── phrase_analysis.py      # Note, Phrase, PhraseAnalyzer
│   ├── melody_generator.py     # MelodyGenerator
│   ├── data_utils.py           # bundled sample progressions
│   └── standard_finder.py      # jazz standards scraper / parser / trainer
├── web/                        # FastAPI + HTMX web application
│   ├── app.py                  # FastAPI app and routes
│   ├── templates/              # HTML templates (base, index, guide, license)
│   └── static/                 # CSS, JS, vendored htmx
├── data/
│   ├── trained_jazz_model.json # pre-trained Markov model (4136 states)
│   └── soundfonts/             # SoundFont(s) for MP3 synthesis (gitignored)
├── scripts/
│   └── download_soundfont.sh   # fetch a GM SoundFont for playback
├── Dockerfile                  # containerized web app
├── LICENSE                     # MIT
├── requirements.txt            # runtime deps
├── requirements-scrape.txt     # optional: scraping/training deps
└── README.md
```

## Installation

Requires Python 3.8+.

```bash
pip install -r requirements.txt
```

The core runtime needs `numpy`, `gradio`, `midiutil`, and `midi2audio`. The
optional `requirements-scrape.txt` (`requests`, `beautifulsoup4`) is only needed
to scrape jazz standards online when training a brand-new model.

### Audio playback (MP3)

In-browser playback synthesizes MP3 from the generated MIDI using FluidSynth, so
it needs two extra things:

1. **FluidSynth** — a system package, not a pip package:
   - macOS: `brew install fluid-synth`
   - Debian/Ubuntu: `sudo apt install fluidsynth`
2. **An MP3 encoder** — `lame` (or `ffmpeg`):
   - macOS: `brew install lame`
   - Debian/Ubuntu: `sudo apt install lame`
3. **A SoundFont** — download one with the bundled helper:

   ```bash
   ./scripts/download_soundfont.sh
   ```

   The app looks for a SoundFont in `data/soundfonts/`, the
   `CHORD_GENERATOR_SOUNDFONT` environment variable, or
   `~/.fluidsynth/default_sound_font.sf2`. Without one, playback is skipped but
   JSON/MIDI download still works.

## Usage

### Web app (recommended)

The FastAPI + HTMX app serves a custom interface with a clickable note grid and
a text input, plus guide and license pages.

```bash
uvicorn web.app:app --reload
```

Then open http://127.0.0.1:8000 in your browser.

You can:

- enter a melody on the note grid or as text (one note per line:
  `pitch start_beat duration`),
- pick a creativity level and rhythm style,
- generate the chord progression and play it back as MP3, and download it as
  JSON, MIDI, or MP3.

### Run with Docker

```bash
docker build -t chord-generator .
docker run -p 8000:8000 chord-generator
```

The image installs FluidSynth, `lame`, and a GM SoundFont, so MP3 playback works
out of the box.

### Gradio app (alternative)

```bash
python webapp.py
```

This opens the older Gradio interface with the same generation and playback
features.

### Run the demo

```bash
python main.py
```

This loads the pre-trained model and generates a progression for a demo melody
at each creativity level.

### Interactive session

```bash
python main.py --interactive
```

Enter melody notes as `pitch start_beat duration` (e.g. `C4 0.0 1.0`), then
type `done` to generate the progression.

### Use as a library

```python
from chord_generator import (
    JazzChordGeneratorApp,
    CreativityLevel,
    Note,
)

app = JazzChordGeneratorApp()
app.train_model()  # loads data/trained_jazz_model.json by default

melody = [
    Note("E4", 0.0, 1.0),
    Note("G4", 1.0, 1.0),
    Note("C5", 2.0, 2.0),
    Note("B4", 4.0, 1.0),
    Note("A4", 5.0, 1.0),
    Note("G4", 6.0, 2.0),
]

progression = app.process_user_melody(
    melody,
    creativity=CreativityLevel.BALANCED,
    use_phrases=True,
)
app.display_progression()
app.export_progression("my_progression.json")
```

## Creativity levels

Creativity controls both the Markov sampling temperature and how much
chromatic/colored harmony is allowed:

| Level        | Value | Temperature | Behaviour                                   |
| ------------ | ----- | ----------- | ------------------------------------------- |
| CONSERVATIVE | 0.0   | 0.1         | deterministic, strictly diatonic chords     |
| BALANCED     | 0.4   | 0.86        | mostly diatonic, occasional tensions        |
| CREATIVE     | 0.7   | 1.43        | chromatic freedom, frequent tensions        |
| EXPERIMENTAL | 1.0   | 2.0         | exploratory sampling, tritone subs, heavy color |

## Training your own model

The app trains from a bundled sample set by default unless a pre-trained model
is present. To train from jazz standards:

```python
app = JazzChordGeneratorApp()
app.train_model(use_sample_data=False)   # loads data/trained_jazz_model.json
```

To build a new model from a rich JSON of standards (sections/endings format):

```python
from chord_generator.standard_finder import JazzStandardsTrainer

trainer = JazzStandardsTrainer()
markov = trainer.train_from_json("path/to/JazzStandards.json")
markov.save_model("data/trained_jazz_model.json")
```

## Diagnostics

```python
app = JazzChordGeneratorApp()
app.train_model()
app.diagnose()   # model stats + sample predictions
```

Individual module demos can be run with `python -m`, e.g.
`python -m chord_generator.key_detector`.
