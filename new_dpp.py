"""
new_dpp.py
----------
Screen to create a new DPP. Two modes:

  Option 1 - Manual Entry : subject, chapter, #questions, target time
  Option 2 - Upload PDF   : pick a PDF, auto page detection
  Option 3 - Scan Page    : drag-select the open DPP page on screen,
                            OCR it, and auto-detect questions + time estimate
                            (no PDF download needed)

Shows a live "AI Estimated Plan" preview + a per-question breakdown. On Start,
builds a config dict and launches the Solving screen.
"""

import os
import customtkinter as ctk
from tkinter import filedialog

from ui import Card, accent_button, get_colors, Toast
from utils import format_time, AIAnalyzer
from pdf_reader import count_pdf_pages as _count_pages
import screen_reader
from screen_reader import RegionSelector


class NewDPPScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.colors = get_colors()
        self.pdf_path = None
        self.pages = 0
        self.scan_estimate = None
        self.questions_plan = None
        self.build()
        self.update_preview()

    # -------------------------------------------------------------------- build
    def build(self):
        colors = self.colors

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 4))
        accent_button(
            top, "← Back", command=self.app.show_dashboard, primary=False,
            width=90, height=32, font=ctk.CTkFont(size=13),
        ).pack(side="left")
        ctk.CTkLabel(top, text="New DPP", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=colors["text"]).pack(side="left", padx=14)

        self.seg = ctk.CTkSegmentedButton(
            self, values=["Manual Entry", "Upload PDF"], command=self.switch_mode)
        self.seg.pack(padx=24, pady=10, anchor="w")
        self.seg.set("Manual Entry")

        # Scrollable body: the form + AI plan live here so they can never push
        # the Start button off-screen. The Start button sits in a pinned footer.
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True, padx=8, pady=4)

        self.manual_frame = Card(self.body)
        self.manual_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.build_manual()

        self.pdf_frame = Card(self.body)
        self.build_pdf()

        # Live AI estimated plan (also inside the scrollable body)
        self.preview = Card(self.body)
        self.preview.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self.preview, text="AI Estimated Plan",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=colors["text"]).pack(anchor="w", padx=16, pady=(10, 0))
        self.preview_text = ctk.CTkLabel(
            self.preview, text="", font=ctk.CTkFont(size=13),
            text_color=colors["muted"], justify="left")
        self.preview_text.pack(anchor="w", padx=16, pady=(4, 12))

        # Per-question AI breakdown (filled in after a successful scan)
        self.breakdown = Card(self.body)
        self.breakdown.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self.breakdown, text="Question Breakdown (AI)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=colors["text"]).pack(anchor="w", padx=16, pady=(10, 0))
        self.breakdown_text = ctk.CTkLabel(
            self.breakdown, text="Scan a page to see per-question type, level & time.",
            font=ctk.CTkFont(size=12), text_color=colors["muted"], justify="left")
        self.breakdown_text.pack(anchor="w", padx=16, pady=(4, 12))

        # Pinned footer: Start DPP is ALWAYS visible, even after a scan fills
        # the form and the AI plan grows taller.
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(4, 16))
        accent_button(
            footer, "Start DPP  →", command=self.start_dpp, height=46,
            font=ctk.CTkFont(size=16, weight="bold")).pack(fill="x")

    # ------------------------------------------------------------------ manual
    def build_manual(self):
        colors = self.colors
        self.sub_var = ctk.StringVar(value="Physics")

        ctk.CTkLabel(self.manual_frame, text="Subject", text_color=colors["muted"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(16, 2))
        ctk.CTkComboBox(
            self.manual_frame,
            values=["Physics", "Chemistry", "Mathematics", "Biology", "Other"],
            variable=self.sub_var, state="readonly", height=38,
        ).pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.manual_frame, text="Chapter", text_color=colors["muted"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(6, 2))
        self.ch_entry = ctk.CTkEntry(self.manual_frame, placeholder_text="e.g. Rotational Motion", height=38)
        self.ch_entry.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.manual_frame, text="Number of Questions", text_color=colors["muted"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(6, 2))
        self.q_entry = ctk.CTkEntry(self.manual_frame, placeholder_text="e.g. 30", height=38)
        self.q_entry.pack(fill="x", padx=20, pady=(0, 8))
        self.q_entry.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(self.manual_frame, text="Target Time (minutes)", text_color=colors["muted"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(6, 2))
        self.t_entry = ctk.CTkEntry(
            self.manual_frame, placeholder_text=f"default {self.app.settings.get('default_target_minutes', 60)}",
            height=38)
        self.t_entry.pack(fill="x", padx=20, pady=(0, 8))
        self.t_entry.bind("<KeyRelease>", self.update_preview)

        # Scan open page (no PDF needed)
        self.scan_btn = accent_button(
            self.manual_frame, "📷 Scan Open Page (auto-detect)",
            command=self.scan_page, height=38)
        self.scan_btn.pack(fill="x", padx=20, pady=(2, 16))
        ctk.CTkLabel(
            self.manual_frame,
            text="Can't download the PDF? Open the DPP in your browser/viewer, "
                 "click this, then drag a box around the page.",
            text_color=colors["muted"], font=ctk.CTkFont(size=11), justify="left").pack(
            anchor="w", padx=20, pady=(0, 12))

    # --------------------------------------------------------------------- pdf
    def build_pdf(self):
        colors = self.colors
        ctk.CTkLabel(self.pdf_frame, text="Upload DPP PDF", text_color=colors["muted"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(16, 4))
        accent_button(self.pdf_frame, "Choose PDF File", command=self.choose_pdf,
                      width=180, height=38).pack(anchor="w", padx=20, pady=(0, 8))
        self.pdf_info = ctk.CTkLabel(self.pdf_frame, text="No file selected", text_color=colors["muted"])
        self.pdf_info.pack(anchor="w", padx=20)

        ctk.CTkLabel(self.pdf_frame, text="Questions (defaults to pages, editable)",
                     text_color=colors["muted"], font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=20, pady=(12, 2))
        self.pdf_q_entry = ctk.CTkEntry(self.pdf_frame, placeholder_text="auto from pages", height=38)
        self.pdf_q_entry.pack(fill="x", padx=20, pady=(0, 8))
        self.pdf_q_entry.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(self.pdf_frame, text="Target Time (minutes, optional)",
                     text_color=colors["muted"], font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=20, pady=(6, 2))
        self.pdf_t_entry = ctk.CTkEntry(
            self.pdf_frame, placeholder_text=f"default {self.app.settings.get('default_target_minutes', 60)}",
            height=38)
        self.pdf_t_entry.pack(fill="x", padx=20, pady=(0, 8))
        self.pdf_t_entry.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(
            self.pdf_frame,
            text="(Future AI: difficulty detection & auto question counting will use this PDF.)",
            text_color=colors["muted"], font=ctk.CTkFont(size=11)).pack(
            anchor="w", padx=20, pady=(4, 16))

    # ------------------------------------------------------------------ actions
    def switch_mode(self, value):
        if value == "Upload PDF":
            self.manual_frame.pack_forget()
            self.pdf_frame.pack(fill="both", expand=True, padx=4, pady=4, in_=self.body)
        else:
            self.pdf_frame.pack_forget()
            self.manual_frame.pack(fill="both", expand=True, padx=4, pady=4, in_=self.body)
        self.update_preview()

    def choose_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_path = path
            self.pages = _count_pages(path)
            self.pdf_info.configure(
                text=f"Selected: {os.path.basename(path)}  ({self.pages} pages)")
            self.pdf_q_entry.delete(0, "end")
            self.pdf_q_entry.insert(0, str(self.pages))
            self.update_preview()

    # --------------------------------------------------------- screen scanning
    def scan_page(self):
        if not screen_reader.EASYOCR_AVAILABLE:
            Toast.show("Need easyocr", "Run:  pip install easyocr", "warning")
            return
        self.scan_btn.configure(text="Drag a box around the DPP page…")
        RegionSelector(self._on_region_selected)

    def _on_region_selected(self, bbox):
        if not bbox:
            self.scan_btn.configure(text="📷 Scan Open Page (auto-detect)")
            return
        # analyze_region runs OCR in a background thread, so its callback fires
        # OFF the main thread. We marshal the UI update back onto the main
        # thread (Tkinter widgets must only be touched from the main thread) to
        # avoid random UI corruption (e.g. the Start button disappearing).
        screen_reader.analyze_region(bbox, self._on_scan_done)

    def _on_scan_done(self, res):
        self.after(0, lambda: self._apply_scan(res))

    def _apply_scan(self, res):
        self.scan_btn.configure(text="📷 Scan Open Page (auto-detect)")
        if "error" in res:
            Toast.show("Scan failed", res["error"], "danger")
            return
        n = res["num_questions"]
        total = res["total_minutes"]
        self.scan_estimate = res
        self.questions_plan = res.get("questions")

        self.q_entry.delete(0, "end")
        self.q_entry.insert(0, str(n))
        self.t_entry.delete(0, "end")
        self.t_entry.insert(0, str(total))
        if res.get("chapter"):
            self.ch_entry.delete(0, "end")
            self.ch_entry.insert(0, res["chapter"])
        self.update_preview()
        Toast.show("Page scanned — please verify",
                   f"Detected ~{n} questions • ~{total} min. Edit if wrong.",
                   "success")

    # ------------------------------------------------------------------ preview
    def update_preview(self, *_):
        try:
            n = int(self.q_entry.get() or 0)
        except ValueError:
            n = 0
        try:
            t = int(self.t_entry.get() or self.app.settings.get("default_target_minutes", 60))
        except ValueError:
            t = self.app.settings.get("default_target_minutes", 60)

        if self.seg.get() == "Upload PDF" and self.pdf_path:
            try:
                n = int(self.pdf_q_entry.get() or self.pages)
            except ValueError:
                n = self.pages
            try:
                t = int(self.pdf_t_entry.get() or t)
            except ValueError:
                pass

        if n > 0:
            if self.scan_estimate:
                se = self.scan_estimate
                avg = (se["total_minutes"] / n) if n else 2.0
                note = "" if se.get("per_question_accurate") \
                    else " — page not split cleanly, levels are approximate"
                txt = (
                    f"Questions: {n}   |   Source: on-screen scan\n"
                    f"Avg per question: {format_time(avg * 60)}\n"
                    f"Difficulty split → Easy: {se['easy']}   Medium: {se['medium']}   Hard: {se['hard']}\n"
                    f"AI total estimate: ~{se['total_minutes']:.0f} min\n"
                    f"(engine: {se['source']}{note})"
                )
            else:
                per = (t * 60 / n) if t > 0 else 120
                est = AIAnalyzer().estimate(
                    n, target_minutes=t, subject=self.sub_var.get(),
                    chapter=self.ch_entry.get())
                txt = (
                    f"Questions: {n}   |   Target: {t} min\n"
                    f"Recommended: {format_time(per)} per question\n"
                    f"Est. split → Easy: {est['easy']}   Medium: {est['medium']}   Hard: {est['hard']}\n"
                    f"Approx solving time: {est['total_minutes']:.0f} min (heuristic)"
                )
            self.preview_text.configure(text=txt)
            # Per-question breakdown list
            if self.scan_estimate and self.scan_estimate.get("questions"):
                lines = [f"Q{q['index']}  [{q['type']} · {q['level']}]  ~{q['minutes']}m"
                         for q in self.scan_estimate["questions"]]
                self.breakdown_text.configure(text="\n".join(lines))
            else:
                self.breakdown_text.configure(
                    text="Scan a page to see per-question type, level & time.")
        else:
            self.preview_text.configure(text="Enter the number of questions to see the AI plan.")
            self.breakdown_text.configure(
                text="Scan a page to see per-question type, level & time.")

    # ----------------------------------------------------------------- start
    def start_dpp(self):
        if self.seg.get() == "Upload PDF":
            if not self.pdf_path:
                Toast.show("Missing PDF", "Please upload a PDF first.", "warning")
                return
            try:
                n = int(self.pdf_q_entry.get() or self.pages)
            except ValueError:
                n = self.pages
            t = self.app.settings.get("default_target_minutes", 60)
            try:
                t = int(self.pdf_t_entry.get() or t)
            except ValueError:
                pass
            per = (t * 60 / n) if (t and n) else 120
            config = {
                "subject": "PDF",
                "chapter": os.path.basename(self.pdf_path),
                "num_questions": n,
                "target_minutes": t,
                "source": "pdf",
                "pdf_path": self.pdf_path,
                "pdf_name": os.path.basename(self.pdf_path),
                "pages": self.pages,
                "recommended_per_question": per,
            }
            self.app.show_solving(config)
            return

        # Manual entry
        sub = self.sub_var.get()
        chap = self.ch_entry.get().strip() or "—"
        try:
            n = int(self.q_entry.get() or 0)
        except ValueError:
            n = 0
        if n <= 0:
            Toast.show("Invalid", "Enter a valid number of questions.", "warning")
            return
        try:
            t = int(self.t_entry.get() or 0)
        except ValueError:
            t = 0
        per = (t * 60 / n) if t > 0 else 120
        config = {
            "subject": sub,
            "chapter": chap,
            "num_questions": n,
            "target_minutes": t,
            "source": "scan" if self.scan_estimate else "manual",
            "recommended_per_question": per,
            "questions": self.questions_plan if self.scan_estimate else None,
        }
        self.app.show_solving(config)