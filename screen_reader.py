"""
screen_reader.py
---------------
Capture a region of the screen and use OCR to estimate the DPP's question
count and solving time — so you never need to download the PDF.

Free / open-source only (no paid API):
  * Pillow   -> already installed (screen capture via ImageGrab)
  * easyocr  -> pip install easyocr   (downloads its models on first use)

The heavy OCR import is optional: if easyocr isn't installed the rest of the
app still runs; the Scan button just tells you to install it.
"""

import re
import threading
from PIL import ImageGrab
import numpy as np

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        # gpu=False -> works on any machine (CPU)
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def capture_region(bbox):
    """bbox = (x1, y1, x2, y2) in screen coordinates."""
    return ImageGrab.grab(bbox)


def ocr_image(img):
    reader = get_reader()
    # easyocr wants a file path / bytes / numpy array -- NOT a raw PIL image.
    arr = np.array(img)
    results = reader.readtext(arr)
    return "\n".join(r[1] for r in results)


def analyze_text(text):
    """
    Turn raw OCR/scanned text into a full AI plan (per-question type, level and
    recommended time). Delegates to utils.AIAnalyzer so the engine can be
    swapped (heuristic now; local LLM later) without touching this file.
    """
    from utils import AIAnalyzer
    return AIAnalyzer().analyze_text(text)


def analyze_region(bbox, callback):
    """Capture + OCR in a background thread, then call callback(result_dict)."""
    def worker():
        try:
            img = capture_region(bbox)
            text = ocr_image(img)
            res = analyze_text(text)
        except Exception as e:
            res = {"error": str(e)}
        callback(res)

    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------------------------
# Transparent region selector (drag to select the DPP page on screen)
# ---------------------------------------------------------------------------
import tkinter as tk
import customtkinter as ctk


class RegionSelector(ctk.CTkToplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.title("Select the DPP page")
        self.attributes("-alpha", 0.25)
        self.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        self.start = None
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.bind("<Escape>", lambda e: self.destroy())
        ctk.CTkLabel(
            self, text="Drag to select the open DPP page, then release  (Esc = cancel)",
            text_color="#ffffff", font=ctk.CTkFont(size=13),
        ).place(relx=0.5, rely=0.02, anchor="n")

    def _down(self, e):
        self.start = (e.x_root, e.y_root)
        self.rect = self.canvas.create_rectangle(
            e.x_root, e.y_root, e.x_root, e.y_root, outline="#d4af37", width=3)

    def _drag(self, e):
        if self.rect:
            self.canvas.coords(self.rect, self.start[0], self.start[1], e.x_root, e.y_root)

    def _up(self, e):
        if not self.start:
            self.destroy()
            return
        x1, y1, x2, y2 = self.start[0], self.start[1], e.x_root, e.y_root
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.destroy()  # treated as cancel
            return
        self.destroy()
        self.callback((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))