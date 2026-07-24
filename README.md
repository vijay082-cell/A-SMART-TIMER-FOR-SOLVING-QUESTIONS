# DPP Timer AI

> A beautiful, intelligent desktop timer built especially for **JEE aspirants**
> to solve Daily Practice Problems (DPPs) while tracking time smartly.

Built with **Python + CustomTkinter + SQLite + PyMuPDF + Matplotlib**.
100% free libraries, no paid APIs. Clean architecture ready for future AI
features (OCR, Gemini, OpenAI, difficulty detection, adaptive timing).

---

## Features

- **Dashboard** — Start New DPP, History, Statistics, Settings, Dark Mode.
- **New DPP** — Manual entry (subject / chapter / questions / target time) **or**
  upload a PDF (auto page detection).
- **AI Estimated Plan** — Recommended time per question + easy/medium/hard split
  (heuristic today; slot in AI later without changing callers).
- **Solving Mode** — Overall countdown, per-question timer with
  Green / Yellow / Red color coding vs recommended time, progress bar,
  Previous / Next / Skip / Pause / Resume / Finish.
- **Smart Alerts** — "Too much time", "Consider skipping", "Excellent speed",
  "Ahead of schedule" (with optional sound).
- **End Report** — Total time, average/question, fastest, slowest, skipped,
  questions above recommended, efficiency score, completion %, and a chart.
  Saved automatically to SQLite.
- **Statistics** — Daily / weekly / monthly study time, average speed per
  subject, average efficiency per subject, best & worst performance.
- **History** — Search, view, and delete past reports.
- **Settings** — Theme (Dark/Light), accent color, notification sound,
  default target time, auto-save.
- **Extras** — Keyboard shortcuts (Space = pause, Enter = next,
  Backspace = previous, S = skip), Fullscreen, Always-on-Top.

---

## Folder Structure

```
dpp_timer_ai/
├── main.py              # App entry point + screen navigation
├── database.py          # SQLite persistence (dpp + question tables)
├── timer.py             # Background-thread Timer (stopwatch / countdown)
├── ui.py                # Reusable widgets, theming, toasts, logo
├── dashboard.py         # Home screen
├── new_dpp.py           # New DPP (manual + PDF)
├── solving.py           # Solving Mode (core)
├── report.py            # End-of-DPP report
├── history.py           # History browser
├── stats.py             # Charts & analytics (named to avoid clashing with stdlib `statistics`)
├── pdf_reader.py        # PyMuPDF page counting / text extraction
├── utils.py             # Paths, time, settings, AI-estimate placeholder
├── settings.py          # Settings screen
├── requirements.txt     # pip dependencies
├── README.md            # This file
├── assets/              # Logo & future assets (auto-created)
└── database/            # SQLite DB + settings.json (auto-created on first run)
```

---

## Installation

You need **Python 3.10+** (3.11 recommended) on Windows.

1. Install Python from https://www.python.org/downloads/ (tick
   *Add Python to PATH* during install).

2. Open a terminal in this folder and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Or individually:

   ```bash
   pip install customtkinter Pillow PyMuPDF matplotlib
   ```

3. Run the app:

   ```bash
   python main.py
   ```

The first run creates the `database/` folder (with `dpp_timer.db` and
`settings.json`) and the `assets/logo.png` automatically.

---

## Building a Windows .exe (PyInstaller)

1. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. From the project folder, build a single-file windowed executable:

   ```bash
   pyinstaller --noconfirm --onefile --windowed ^
       --name "DPP Timer AI" ^
       --icon "assets/logo.png" ^
       --add-data "assets;assets" ^
       main.py
   ```

   (On PowerShell use backticks `` ` `` instead of `^`; on bash use `\`.)

3. The executable appears in `dist/DPP Timer AI.exe`.
   - In `--onefile` mode the database is stored in your
     `Documents/DPPTimerAI` folder so your data persists across updates.
   - If you prefer the DB next to the exe, build with `--onedir` instead of
     `--onefile`.

---

## Keyboard Shortcuts (Solving Mode)

| Key         | Action          |
|-------------|-----------------|
| Space       | Pause / Resume  |
| Enter       | Next question   |
| Backspace   | Previous question |
| S           | Skip question   |

---

## Future AI Features (architecture ready)

The `AIAnalyzer` class in `utils.py` is the integration point. Planned (no paid
APIs used yet):

- OCR-based question extraction from PDFs / images
- Gemini / OpenAI difficulty detection
- Automatic question counting
- Chapter detection
- Difficulty & personal-speed prediction
- Adaptive recommended time

To add a provider later, implement `AIAnalyzer.analyze_pdf(...)` / `.estimate(...)`
and call it from `new_dpp.py` — the rest of the app stays unchanged.

---

## License

Free to use and modify for educational purposes.
