"""
utils.py
--------
Shared helpers for DPP Timer AI (no external GUI dependency).

Responsibilities:
  * Resolve paths that work both in development and inside a PyInstaller .exe
  * Format / parse time values (MM:SS, HH:MM:SS)
  * Load / save user settings (JSON)
  * Play notification beeps (Windows) with a safe cross-platform fallback
  * Provide an in-app toast alert helper
  * Provide an AI time-estimation placeholder + clean architecture for future
    paid/免费 AI features (OCR, Gemini, OpenAI, difficulty detection, ...)

Free libraries only. No paid APIs are called here.
"""

import os
import sys
import json
import re
import math
import time
import threading

# winsound is Windows-only; guard so the module imports cleanly elsewhere.
try:
    import winsound
except ImportError:  # e.g. Linux/macOS
    winsound = None


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def get_data_dir():
    """
    Return a directory where the SQLite database and settings are stored.
    In development this is the local 'database' folder of the project.
    When frozen into an .exe we use the user's Documents folder so the data
    survives upgrades / reinstalls.
    """
    if getattr(sys, "frozen", False):
        path = os.path.join(os.path.expanduser("~"), "Documents", "DPPTimerAI")
    else:
        path = os.path.join(BASE_DIR, "database")
    os.makedirs(path, exist_ok=True)
    return path


DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "dpp_timer.db")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")


def resource_path(relative_path):
    """
    Resolve a path to a bundled asset. PyInstaller exposes bundled files via
    sys._MEIPASS; otherwise we resolve relative to the project folder.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------
def format_time(seconds):
    """Format seconds as HH:MM:SS (or MM:SS when under an hour)."""
    if seconds is None:
        return "00:00"
    seconds = int(round(seconds))
    if seconds < 0:
        seconds = 0
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def parse_time_to_seconds(text):
    """Parse 'MM:SS', 'HH:MM:SS' or plain minutes into seconds."""
    text = (text or "").strip()
    if not text:
        return 0
    try:
        parts = [int(p) for p in text.split(":")]
    except ValueError:
        return 0
    if len(parts) == 1:
        return parts[0] * 60
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def clamp(value, low, high):
    """Restrict a value to the [low, high] range."""
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "theme": "dark",                 # "dark" | "light"
    "accent": "#3b82f6",             # hex accent color
    "notification_sound": True,      # play a beep on smart alerts
    "default_target_minutes": 60,    # default target time for a new DPP
    "questions_per_target": 30,      # helper used by heuristic estimates
    "auto_save": True,  
    "ai_backend": "heuristic",                 
    "ollama_model": "llama3.2:latest",             # automatically save reports to DB
}


def load_settings():
    """Load settings from JSON, merging with defaults for forward-compat."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """Persist settings to JSON."""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


# ---------------------------------------------------------------------------
# Sound & Alerts
# ---------------------------------------------------------------------------
def play_beep(frequency=880, duration=150):
    """
    Play a short beep. Uses the Windows winmm beep; safely no-ops elsewhere.
    frequency: Hz, duration: milliseconds.
    """
    if winsound is None:
        return
    try:
        winsound.Beep(frequency, duration)
    except Exception:
        pass


def notify(title, message):
    """
    Show an in-app toast alert. Delayed import of ui avoids circular imports.
    """
    try:
        from ui import Toast
        Toast.show(title, message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# AI time estimation & difficulty analysis
# ---------------------------------------------------------------------------
# Baseline minutes an AVERAGE JEE/NEET-style student needs per question, by level.
_LEVEL_MINUTES = {"easy": 1.5, "medium": 2.5, "hard": 4.0}


def count_questions(text):
    """Estimate the number of questions on a scanned DPP page.

    OCR is imperfect (it often merges the whole page into one text block), so
    we try several heuristics and pick the most reliable signal. The result is
    only a *suggestion* -- the user verifies/edits it in the form.
    """
    if not text or not text.strip():
        return 1

    # 1) Explicit labels: "Q.1", "Q 2", "Question 3"
    q_marks = re.findall(r"(?i)(?<![A-Za-z0-9])(?:q\.?\s*\d+|question\s+\d+)", text)
    if len(q_marks) >= 2:
        return len(q_marks)

    # 2) Numbers at the start of a line: "1." or "2)". Keep the longest
    #    consecutive run beginning at 1 (this ignores reset option lists
    #    like 1-4 that belong to a single question).
    line_nums = re.findall(r"(?m)(?:^|\n)\s*(\d+)\s*[\.\)]", text)
    run = _longest_run_from_1(line_nums)
    if run >= 2:
        return run

    # 2b) If options are numbered "1)".."4)", each question contributes one
    #     "1)", so counting those gives the question count.
    first_opt = re.findall(r"(?m)(?:^|\n)\s*1[\.\)]", text)
    if len(first_opt) >= 2:
        return len(first_opt)

    # 3) Inline questions even if OCR merged lines: "1. The", "2. A" ...
    inline = re.findall(r"(?<!\d\.)\b(\d+)\.\s+[A-Z]", text)
    run = _longest_run_from_1(inline)
    if run >= 2:
        return run

    # 4) Last resort: rough estimate from word count (never absurdly low).
    words = len(text.split())
    return max(1, min(60, round(words / 55)))


def _longest_run_from_1(nums):
    """Length of the longest consecutive run of integers starting at 1.

    e.g. [1,2,3,4,5] -> 5 ; [1,2,3,4,1,2,3] -> 4 (run breaks at the reset).
    """
    try:
        s = sorted(set(int(x) for x in nums))
    except ValueError:
        return 0
    run = 0
    for i, v in enumerate(s):
        if i == 0 and v != 1:
            break
        if i == 0 or v == s[i - 1] + 1:
            run += 1
        else:
            break
    return run


def estimate_time(num_questions, target_minutes=None, subject=None,
                  chapter=None, history=None, pdf_info=None):
    """
    Estimate solving time for a DPP (uniform heuristic, used for manual entry).

    FUTURE: replace the heuristic below with OCR + Gemini/OpenAI difficulty
    detection. The function signature is intentionally rich so future code
    can be slotted in without touching the callers.

    Returns a dict with:
        total_minutes, per_question_minutes, easy, medium, hard, source
    """
    if target_minutes:
        recommended_total = float(target_minutes)
    elif history:
        recommended_total = sum(h["actual_time"] for h in history) / max(1, len(history)) / 60.0
    else:
        recommended_total = num_questions * 2.0  # sensible default: 2 min/q

    per_q = (recommended_total / num_questions) if num_questions else 2.0

    # Rough difficulty split (heuristic). Future AI will refine this.
    easy = round(num_questions * 0.4)
    medium = round(num_questions * 0.4)
    hard = num_questions - easy - medium

    return {
        "total_minutes": recommended_total,
        "per_question_minutes": per_q,
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "source": "heuristic",
    }


class AIAnalyzer:
    """Difficulty & time analysis engine.

    Backends (selected via settings['ai_backend']):
      * "heuristic" - free, offline, rule-based. Works today, no downloads.
      * "ollama"    - free LOCAL open-source LLM via Ollama (no paid API).
                      Used only if `ollama` is installed + a model is pulled;
                      otherwise it automatically falls back to "heuristic".

    The analyzer turns raw OCR/scanned text into a per-question plan:
        {num_questions, questions:[{type,level,minutes,...}], total_minutes,
         easy, medium, hard, source, per_question_accurate, chapter}
    """

    def __init__(self, backend=None):
        settings = load_settings()
        self.backend = backend or settings.get("ai_backend", "heuristic")
        self.ollama_model = settings.get("ollama_model", "llama3.2:latest")

    # ---- public entry ----
    def analyze_text(self, text):
        plan = None
        if self.backend == "ollama":
            try:
                plan = self._analyze_ollama(text)
            except Exception:
                plan = None  # fall back to heuristic below
        if plan is None:
            plan = self._analyze_heuristic(text)
        return plan

    # ---- heuristic backend (free, offline, works today) ----
    def _analyze_heuristic(self, text):
        n = count_questions(text)
        blocks = self._split_questions(text)
        # If we could split cleanly into the same number of questions, analyze
        # each one individually; otherwise analyze the whole page once.
        if 1 < len(blocks) == n:
            questions = [self._analyze_block(b, i + 1) for i, b in enumerate(blocks)]
            accurate = True
        else:
            blk = self._analyze_block(text, 0)
            questions = [{
                "index": i + 1,
                "type": blk["type"],
                "level": blk["level"],
                "minutes": blk["minutes"],
                "confidence": "low",
            } for i in range(n)]
            accurate = False
        # Always return exactly n question entries.
        while len(questions) < n:
            questions.append({"index": len(questions) + 1, "type": "Standard",
                              "level": "medium", "minutes": 2.5, "confidence": "low"})
        questions = questions[:n]

        total = round(sum(q["minutes"] for q in questions), 1)
        easy = sum(1 for q in questions if q["level"] == "easy")
        medium = sum(1 for q in questions if q["level"] == "medium")
        hard = sum(1 for q in questions if q["level"] == "hard")
        return {
            "num_questions": n,
            "questions": questions,
            "total_minutes": total,
            "easy": easy, "medium": medium, "hard": hard,
            "source": "heuristic",
            "per_question_accurate": accurate,
            "chapter": self._detect_chapter(text),
        }

    def _split_questions(self, text):
        # Split on question starts: "1.", "2)", "Q.3", "Question 4"
        parts = re.split(
            r"(?im)(?=(?:^|\n)\s*(?:\d+\s*[\.\)]|q\.?\s*\d+|question\s+\d+))", text)
        return [p.strip() for p in parts if p and p.strip()]

    def _analyze_block(self, block, index):
        # strip the leading "1." / "2)" question number so it doesn't inflate counts
        clean = re.sub(r"^\s*\d+\s*[\.\)]\s*", "", block)
        wc = len(clean.split())
        low = block.lower()

        # --- question type ---
        opt_alpha = len(re.findall(r"(?:^|[^A-Za-z])\(?[A-Da-d]\)", block))
        opt_num = len(re.findall(r"(?m)(?:^|\n)\s*\(?\d\)", block))
        has_options = opt_alpha >= 3 or opt_num >= 3
        if re.search(r"(?i)assertion.*reason|reason.*assertion", block):
            qtype = "Assertion-Reason"
        elif has_options:
            qtype = "MCQ"
        elif re.search(r"(?i)\b(integer|numerical|0\s*to\s*9|single digit|two digit)\b", block):
            qtype = "Numerical"
        elif re.search(r"(?i)\b(prove|derive|show that|explain|justify|discuss|establish)\b", block):
            qtype = "Subjective"
        else:
            qtype = "Standard"

        # --- difficulty scoring (average-student perspective) ---
        score = 0
        if wc >= 80:
            score += 3
        elif wc >= 40:
            score += 2
        elif wc >= 18:
            score += 1
        math_syms = len(re.findall(r"[+\-*/=^√∝∂∫∑∏πθαβγλμ≤≥≈→⇔∈∀∃]", clean))
        digits = len(re.findall(r"\d", clean))
        if (math_syms + digits) >= 12 or (wc and (math_syms + digits) / wc > 0.25):
            score += 1
        # multi-part indicators only (NOT the a/b/c/d option labels of an MCQ)
        parts = len(re.findall(r"(?i)(?:\(i+\)|\(iv\)|\bOR\b|part\s*[A-D]\b)", clean))
        if parts >= 2:
            score += 1
        if re.search(r"(?i)(diagram|figure|graph|circuit|shown (?:below|above)|plot)", block):
            score += 1
        if re.search(r"(?i)\b(prove|derive|show that|establish|justify|explain how|explain why)\b", block):
            score += 1
        if re.search(r"(?i)\b(state|name|define|list|identify|write the)\b", block) and score <= 1:
            score -= 1

        if score <= 0:
            level = "easy"
        elif score <= 2:
            level = "medium"
        else:
            level = "hard"

        return {
            "index": index,
            "type": qtype,
            "level": level,
            "minutes": _LEVEL_MINUTES.get(level, 2.5),
            "confidence": "medium" if wc >= 8 else "low",
        }

    def _detect_chapter(self, text):
        m = re.search(r"(?i)chapter\s*[:\-]?\s*([A-Za-z0-9 &]+)", text)
        return m.group(1).strip() if m else ""

    # ---- local LLM backend (free, no paid API; optional) ----
    def _analyze_ollama(self, text):
        """Free LOCAL model via Ollama. Returns a plan dict or raises.

        Requires:  pip install ollama   (and `ollama serve` running with a
        model pulled, e.g. `ollama pull llama3.2`). If anything is missing this
        raises and the caller falls back to the heuristic engine automatically.
        """
        import ollama  # local import: the app never hard-depends on it

        prompt = (
            "You are an AI tutor for JEE/NEET style exam prep. "
            "Given the text of a DPP (Daily Practice Problem) page, analyze EACH question.\n"
            "For every question return: type (MCQ | Numerical | Assertion-Reason | "
            "Subjective | Standard), level (easy | medium | hard) from an AVERAGE "
            "student's perspective, and recommended_minutes (easy~1.5, medium~2.5, hard~4.0).\n"
            'Respond ONLY with strict JSON: {"questions":[{"type":"...","level":"...",'
            '"recommended_minutes":2.5}, ...]}\n\nPAGE TEXT:\n' + text
        )
        resp = ollama.chat(
            model=self.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        obj = json.loads(resp["message"]["content"])
        qs = obj.get("questions", [])
        questions = []
        for i, q in enumerate(qs):
            lvl = str(q.get("level", "medium")).lower()
            if lvl not in ("easy", "medium", "hard"):
                lvl = "medium"
            minutes = float(q.get("recommended_minutes", _LEVEL_MINUTES.get(lvl, 2.5)))
            questions.append({
                "index": i + 1,
                "type": str(q.get("type", "Standard")),
                "level": lvl,
                "minutes": round(minutes, 1),
                "confidence": "high",
            })
        n = len(questions)
        total = round(sum(q["minutes"] for q in questions), 1)
        easy = sum(1 for q in questions if q["level"] == "easy")
        medium = sum(1 for q in questions if q["level"] == "medium")
        hard = sum(1 for q in questions if q["level"] == "hard")
        return {
            "num_questions": n,
            "questions": questions,
            "total_minutes": total,
            "easy": easy, "medium": medium, "hard": hard,
            "source": "ollama",
            "per_question_accurate": True,
            "chapter": self._detect_chapter(text),
        }

    # ---- legacy / future hooks (kept for backward compatibility) ----
    def analyze_pdf(self, pdf_path):
        """Future: extract text via OCR then classify question difficulty."""
        return None

    def estimate(self, num_questions, target_minutes=None, subject=None,
                 chapter=None, history=None, pdf_info=None):
        """Public estimate entry point used by the New DPP screen (manual mode)."""
        return estimate_time(
            num_questions,
            target_minutes=target_minutes,
            subject=subject,
            chapter=chapter,
            history=history,
            pdf_info=pdf_info,
        )