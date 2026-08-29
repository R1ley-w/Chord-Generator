"""FastAPI + HTMX web app for the Jazz Chord Generator."""

import os
import shutil
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chord_generator import (
    CreativityLevel,
    JazzChordGeneratorApp,
    Note,
    RhythmStyle,
)
from chord_generator.audio import render_midi_to_mp3, render_progression_to_midi

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))
GENERATED_DIR = PROJECT_DIR / "data" / "generated"

_ALLOWED_FILES = {"progression.json", "progression.mid"}

_app = None
_lock = threading.Lock()


def _get_app() -> JazzChordGeneratorApp:
    global _app
    if _app is None:
        _app = JazzChordGeneratorApp()
        _app.train_model()
    return _app


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_app()
    yield


app = FastAPI(title="Jazz Chord Generator", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def parse_melody_text(text: str) -> list[Note]:
    """Parse one note per line as ``pitch [start] [duration]``.

    When ``start``/``duration`` are omitted, notes are placed one beat apart.
    """
    notes = []
    auto_start = 0.0
    for line in text.strip().splitlines():
        line = line.replace(",", " ").strip()
        if not line:
            continue

        parts = line.split()
        pitch = parts[0]
        if len(parts) == 1:
            start, duration = auto_start, 1.0
        elif len(parts) == 2:
            start, duration = float(parts[1]), 1.0
        else:
            start, duration = float(parts[1]), float(parts[2])

        notes.append(Note(pitch, start, duration))
        auto_start = start + duration

    return notes


def _chord_rows(app: JazzChordGeneratorApp) -> list[dict]:
    rows = []
    for cd in app.current_progression:
        rows.append({
            "chord": str(cd.chord),
            "bar": int(cd.start_beat / 4) + 1,
            "beat": cd.start_beat % 4 + 1,
            "duration": cd.duration,
        })
    return rows


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


@app.get("/guide", response_class=HTMLResponse)
def guide(request: Request):
    return TEMPLATES.TemplateResponse("guide.html", {"request": request})


@app.get("/license", response_class=HTMLResponse)
def license_page(request: Request):
    return TEMPLATES.TemplateResponse("license.html", {"request": request})


@app.get("/demo-melody")
def demo_melody():
    with _lock:
        melody = _get_app().generate_demo_melody("bebop")
    return JSONResponse([
        {"pitch": n.pitch, "start": n.start_beat, "duration": n.duration}
        for n in melody
    ])


@app.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    melody: str = Form(...),
    creativity: str = Form("BALANCED"),
    rhythm: str = Form("swing"),
    use_phrases: str = Form("false"),
):
    notes = parse_melody_text(melody)
    if not notes:
        return HTMLResponse(
            '<p class="notice">Enter at least one melody note.</p>'
        )

    try:
        level = CreativityLevel[creativity]
    except KeyError:
        level = CreativityLevel.BALANCED

    try:
        style = RhythmStyle(rhythm)
    except ValueError:
        style = RhythmStyle.SWING

    token = uuid.uuid4().hex
    token_dir = GENERATED_DIR / token
    token_dir.mkdir(parents=True, exist_ok=True)

    with _lock:
        app_instance = _get_app()
        app_instance.set_rhythm_style(style)
        app_instance.process_user_melody(
            notes,
            creativity=level,
            use_phrases=(use_phrases.lower() in {"true", "1", "on", "yes"}),
        )

        json_path = token_dir / "progression.json"
        app_instance.export_progression(str(json_path))

        midi_path = token_dir / "progression.mid"
        render_progression_to_midi(app_instance.current_progression, str(midi_path))

        audio_name = None
        try:
            rendered = render_midi_to_mp3(str(midi_path))
            audio_name = "audio" + os.path.splitext(rendered)[1]
            shutil.move(rendered, str(token_dir / audio_name))
        except Exception as exc:  # FluidSynth/SoundFont unavailable
            print(f"[audio] synthesis failed: {exc}")

        context = {
            "request": request,
            "key": str(app_instance.current_key),
            "rhythm": style.value,
            "chords": _chord_rows(app_instance),
            "json_url": f"/files/{token}/progression.json",
            "midi_url": f"/files/{token}/progression.mid",
            "audio_url": f"/files/{token}/{audio_name}" if audio_name else None,
        }

    return TEMPLATES.TemplateResponse("partials/results.html", context)


@app.get("/files/{token}/{name}")
def files(token: str, name: str):
    if not token.isalnum():
        return HTMLResponse(status_code=404)
    if name != "progression.json" and name != "progression.mid" and not name.startswith("audio"):
        return HTMLResponse(status_code=404)

    path = (GENERATED_DIR / token / name).resolve()
    if GENERATED_DIR.resolve() not in path.parents:
        return HTMLResponse(status_code=404)
    if not path.is_file():
        return HTMLResponse(status_code=404)

    media = "audio/mpeg" if name.endswith(".mp3") else None
    return FileResponse(str(path), media_type=media)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
