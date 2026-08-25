"""Gradio web UI for the Jazz Chord Generator."""

import os
import tempfile
from typing import List

import gradio as gr

from .app import CreativityLevel, JazzChordGeneratorApp, RhythmStyle
from .audio import render_midi_to_mp3, render_progression_to_midi
from .phrase_analysis import Note

_CREATIVITY_CHOICES = [level.name for level in CreativityLevel]
_RHYTHM_CHOICES = [style.value for style in RhythmStyle]

_app = None


def _get_app() -> JazzChordGeneratorApp:
    """Return a shared, lazily-trained app instance."""
    global _app
    if _app is None:
        _app = JazzChordGeneratorApp()
        _app.train_model()
    return _app


def _parse_melody_text(text: str) -> List[Note]:
    """Parse melody notes, one per line as ``pitch [start] [duration]``.

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


def _format_progression(app: JazzChordGeneratorApp) -> str:
    lines = [f"**Key:** {app.current_key}", f"**Rhythm:** {app.rhythm_style.value}", ""]
    for chord_dur in app.current_progression:
        bar = int(chord_dur.start_beat / 4) + 1
        beat = chord_dur.start_beat % 4 + 1
        lines.append(
            f"- Bar {bar}, Beat {beat:.0f}: `{chord_dur.chord}` ({chord_dur.duration:.1f} beats)"
        )
    return "\n".join(lines)


def _demo_melody_text() -> str:
    app = _get_app()
    melody = app.generate_demo_melody("bebop")
    return "\n".join(f"{note.pitch} {note.start_beat} {note.duration}" for note in melody)


def generate(melody_text, creativity_name, use_phrases, rhythm_style_name):
    notes = _parse_melody_text(melody_text)
    if not notes:
        raise gr.Error("Enter at least one melody note, e.g. 'C4 0.0 1.0'.")

    app = _get_app()
    app.set_rhythm_style(RhythmStyle(rhythm_style_name))
    app.process_user_melody(
        notes,
        creativity=CreativityLevel[creativity_name],
        use_phrases=use_phrases,
    )

    fd, json_path = tempfile.mkstemp(suffix=".json", prefix="progression_")
    os.close(fd)
    app.export_progression(json_path)

    fd, midi_path = tempfile.mkstemp(suffix=".mid", prefix="progression_")
    os.close(fd)
    render_progression_to_midi(app.current_progression, midi_path)

    audio_path = None
    try:
        audio_path = render_midi_to_mp3(midi_path)
    except Exception as exc:
        print(f"[audio] playback synthesis failed: {exc}")

    return (
        str(app.current_key),
        _format_progression(app),
        audio_path,
        json_path,
        midi_path,
        audio_path,
    )


def build_app() -> gr.Blocks:
    """Construct the Gradio interface."""
    with gr.Blocks(title="Jazz Chord Generator") as demo:
        gr.Markdown(
            "# Jazz Chord Generator\n"
            "Enter a melody and get a jazz chord progression that harmonizes it."
        )

        with gr.Row():
            with gr.Column():
                melody_input = gr.Textbox(
                    label="Melody notes",
                    lines=10,
                    placeholder="C4 0.0 1.0\nE4 1.0 1.0\nG4 2.0 2.0\nB4 4.0 1.0",
                )
                with gr.Row():
                    demo_btn = gr.Button("Load demo melody")
                    generate_btn = gr.Button("Generate chords", variant="primary")
                creativity = gr.Dropdown(
                    _CREATIVITY_CHOICES, value="BALANCED", label="Creativity"
                )
                rhythm = gr.Dropdown(
                    _RHYTHM_CHOICES, value="swing", label="Rhythm style"
                )
                use_phrases = gr.Checkbox(value=True, label="Use phrase analysis")

            with gr.Column():
                key_output = gr.Textbox(label="Detected key")
                progression_output = gr.Markdown()
                audio_output = gr.Audio(label="Playback", type="filepath")
                json_output = gr.File(label="Download progression (JSON)")
                midi_output = gr.File(label="Download MIDI")
                mp3_output = gr.File(label="Download audio (MP3)")

        demo_btn.click(fn=_demo_melody_text, outputs=melody_input)
        generate_btn.click(
            fn=generate,
            inputs=[melody_input, creativity, use_phrases, rhythm],
            outputs=[key_output, progression_output, audio_output,
                     json_output, midi_output, mp3_output],
        )

    return demo


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()
