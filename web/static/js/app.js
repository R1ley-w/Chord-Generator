// Interactive note grid and melody text sync for the Jazz Chord Generator.

(function () {
  "use strict";

  var PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  var MIN_MIDI = 48; // C3
  var MAX_MIDI = 84; // C6
  var BEATS = 32;

  var gridEl = document.getElementById("note-grid");
  var textEl = document.getElementById("melody");
  var demoBtn = document.getElementById("demo-btn");
  var clearBtn = document.getElementById("clear-btn");
  var playBtn = document.getElementById("play-btn");

  if (!gridEl || !textEl) {
    return;
  }

  // notes: [{ pitch: int (midi), start: number, duration: number }]
  var notes = [];
  var editingText = false;

  var SECONDS_PER_BEAT = 0.5; // 120 BPM
  var audioCtx = null;

  function getAudioContext() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function midiToFreq(midi) {
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  function playNote(midi, durationSeconds, whenSeconds) {
    var ctx = getAudioContext();
    var t0 = ctx.currentTime + (whenSeconds || 0);
    var end = Math.max(durationSeconds || 0.2, 0.1);

    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = "triangle";
    osc.frequency.value = midiToFreq(midi);

    gain.gain.setValueAtTime(0, t0);
    gain.gain.linearRampToValueAtTime(0.3, t0 + 0.02);
    gain.gain.setValueAtTime(0.3, Math.max(t0 + 0.02, t0 + end - 0.05));
    gain.gain.linearRampToValueAtTime(0, t0 + end);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(t0);
    osc.stop(t0 + end + 0.05);
  }

  function playMelody() {
    for (var i = 0; i < notes.length; i++) {
      var note = notes[i];
      playNote(note.pitch, note.duration * SECONDS_PER_BEAT, note.start * SECONDS_PER_BEAT);
    }
  }

  function midiToName(midi) {
    return PITCH_NAMES[midi % 12] + (Math.floor(midi / 12) - 1);
  }

  function buildGrid() {
    gridEl.style.setProperty("--beats", BEATS);
    gridEl.innerHTML = "";

    // Header row: empty corner + beat numbers.
    var corner = document.createElement("div");
    corner.className = "grid-label";
    gridEl.appendChild(corner);
    for (var b = 0; b < BEATS; b++) {
      var head = document.createElement("div");
      head.className = "grid-beat-header";
      head.textContent = b % 4 === 0 ? String(b) : "";
      gridEl.appendChild(head);
    }

    // Pitch rows, top to bottom (highest first).
    for (var midi = MAX_MIDI; midi >= MIN_MIDI; midi--) {
      var label = document.createElement("div");
      label.className = "grid-label";
      label.textContent = midiToName(midi);
      gridEl.appendChild(label);

      for (var beat = 0; beat < BEATS; beat++) {
        var cell = document.createElement("div");
        cell.className = "grid-cell";
        cell.dataset.pitch = String(midi);
        cell.dataset.beat = String(beat);
        gridEl.appendChild(cell);
      }
    }
  }

  function noteCovers(note, midi, beat) {
    return note.pitch === midi && beat >= note.start && beat < note.start + note.duration;
  }

  function renderGrid() {
    var cells = gridEl.querySelectorAll(".grid-cell");
    for (var i = 0; i < cells.length; i++) {
      var cell = cells[i];
      var midi = parseInt(cell.dataset.pitch, 10);
      var beat = parseInt(cell.dataset.beat, 10);
      var on = false;
      for (var j = 0; j < notes.length; j++) {
        if (noteCovers(notes[j], midi, beat)) {
          on = true;
          break;
        }
      }
      cell.classList.toggle("on", on);
    }
  }

  function formatNote(note) {
    return midiToName(note.pitch) + " " + note.start + " " + note.duration;
  }

  function renderText() {
    textEl.value = notes.map(formatNote).join("\n");
  }

  function parseText() {
    var parsed = [];
    var autoStart = 0;
    textEl.value.replace(",", " ").split("\n").forEach(function (line) {
      var trimmed = line.trim();
      if (!trimmed) {
        return;
      }
      var parts = trimmed.split(/\s+/);
      var pitch = parts[0];
      var midi = nameToMidi(pitch);
      if (midi === null) {
        return;
      }
      var start = parts.length >= 2 ? parseFloat(parts[1]) : autoStart;
      var duration = parts.length >= 3 ? parseFloat(parts[2]) : 1;
      parsed.push({ pitch: midi, start: start, duration: duration });
      autoStart = start + duration;
    });
    return parsed;
  }

  function nameToMidi(name) {
    var match = /^([A-G])([#b]?)(-?\d+)$/.exec(name);
    if (!match) {
      return null;
    }
    var pc = PITCH_NAMES.indexOf(match[1]);
    if (match[2] === "#") {
      pc += 1;
    } else if (match[2] === "b") {
      pc -= 1;
    }
    pc = ((pc % 12) + 12) % 12;
    return (parseInt(match[3], 10) + 1) * 12 + pc;
  }

  function loadDemo() {
    fetch("/demo-melody")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        notes = data.map(function (n) {
          var midi = nameToMidi(n.pitch);
          return { pitch: midi === null ? 60 : midi, start: n.start, duration: n.duration };
        });
        renderGrid();
        renderText();
      })
      .catch(function () {
        notes = [
          { pitch: 64, start: 0, duration: 1 },
          { pitch: 67, start: 1, duration: 1 },
          { pitch: 72, start: 2, duration: 2 },
          { pitch: 71, start: 4, duration: 1 },
          { pitch: 69, start: 5, duration: 1 },
          { pitch: 67, start: 6, duration: 2 }
        ];
        renderGrid();
        renderText();
      });
  }

  gridEl.addEventListener("click", function (event) {
    var cell = event.target.closest(".grid-cell");
    if (!cell) {
      return;
    }
    var midi = parseInt(cell.dataset.pitch, 10);
    var beat = parseInt(cell.dataset.beat, 10);

    var index = -1;
    for (var i = 0; i < notes.length; i++) {
      if (noteCovers(notes[i], midi, beat)) {
        index = i;
        break;
      }
    }

    if (index >= 0) {
      notes.splice(index, 1);
    } else {
      notes.push({ pitch: midi, start: beat, duration: 1 });
      playNote(midi, 0.25, 0);
    }

    renderGrid();
    renderText();
  });

  textEl.addEventListener("focus", function () { editingText = true; });
  textEl.addEventListener("blur", function () {
    editingText = false;
    notes = parseText();
    renderGrid();
  });

  if (demoBtn) {
    demoBtn.addEventListener("click", loadDemo);
  }
  if (playBtn) {
    playBtn.addEventListener("click", playMelody);
  }
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      notes = [];
      renderGrid();
      renderText();
    });
  }

  buildGrid();
})();
