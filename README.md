# Jazz Chord Generator

Generate a jazz chord progression that harmonizes any melody. A Markov chain
trained on jazz standards proposes chords, which key detection, phrase analysis,
and a creativity level then shape.

## Quick start

```bash
pip install -r requirements.txt
uvicorn web.app:app --reload
```

Open http://127.0.0.1:8000. Enter a melody on the note grid or as text, pick a
creativity level, and generate. You can preview the melody, then download the
result as JSON, MIDI, or MP3.

Or run with Docker:

```bash
docker build -t chord-generator .
docker run -p 8000:8000 chord-generator
```

## Audio playback

MP3 playback uses FluidSynth, which needs a system package and a SoundFont:

```bash
brew install fluid-synth lame        # macOS
sudo apt install fluidsynth lame     # Debian/Ubuntu
./scripts/download_soundfont.sh      # downloads a GM SoundFont
```

Without these, the JSON and MIDI downloads still work.

## Command line

```bash
python main.py                # run the demo
python main.py --interactive  # enter notes interactively
python webapp.py              # alternative Gradio UI
```

## Library

```python
from chord_generator import JazzChordGeneratorApp, CreativityLevel, Note

app = JazzChordGeneratorApp()
app.train_model()

melody = [Note("E4", 0, 1), Note("G4", 1, 1), Note("C5", 2, 2)]
progression = app.process_user_melody(melody, creativity=CreativityLevel.BALANCED)
app.display_progression()
app.export_progression("my_progression.json")
```

## Creativity levels

| Level        | Behavior                                |
| ------------ | ---------------------------------------- |
| CONSERVATIVE | deterministic, strictly diatonic        |
| BALANCED     | mostly diatonic, occasional tensions     |
| CREATIVE     | chromatic freedom, frequent tensions     |
| EXPERIMENTAL | exploratory, tritone subs, heavy color   |

## Training a new model

```python
from chord_generator.standard_finder import JazzStandardsTrainer

trainer = JazzStandardsTrainer()
markov = trainer.train_from_json("path/to/JazzStandards.json")
markov.save_model("data/trained_jazz_model.json")
```

## License

MIT. See LICENSE.
