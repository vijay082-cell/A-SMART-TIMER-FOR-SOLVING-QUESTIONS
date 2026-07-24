"""
solving.py
----------
The Solving Mode — the heart of DPP Timer AI.

Features:
  * Overall countdown (or elapsed-stopwatch when no target is set)
  * Per-question stopwatch with Green / Yellow / Red color coding vs recommended
  * Recommended vs Current vs Difference display
  * Average time per question + remaining questions
  * Progress bar, Previous / Next / Skip / Pause-Resume / Finish
  * Smart alerts (in-app banner + optional beep)
  * Keyboard shortcuts: Space=pause, Enter=next, Backspace=prev, S=skip
  * Fullscreen & Always-on-Top toggles
  * Miniplayer: compact always-on-top floating window (see miniplayer.py)
"""

import customtkinter as ctk

from ui import Card, accent_button, get_colors, Toast
from utils import format_time, clamp, play_beep
from timer import Timer
from miniplayer import MiniPlayer


class SolvingScreen(ctk.CTkFrame):
    def __init__(self, master, app, config):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.config = config
        self.colors = get_colors()
        self.mini = None  # MiniPlayer instance (None when closed)

        # ----- session state -----
        self.n = max(1, int(config.get("num_questions", 1)))
        self.subject = config.get("subject", "General")
        self.chapter = config.get("chapter", "")
        self.target_seconds = (config.get("target_minutes", 0) or 0) * 60
        self.recommended = config.get("recommended_per_question", 120)  # seconds (fallback)

        # Session state must exist BEFORE we compute per-question times.
        self.current = 1
        self.times = [0.0] * self.n
        self.skipped = [False] * self.n
        self.paused = False
        self.finished = False
        self.last_q_status = "green"
        self._timeup = False

        # Per-question recommended times from an AI scan (if available).
        qs = config.get("questions")
        if isinstance(qs, list) and len(qs) == self.n:
            self.recommended_list = [max(30, int(round(q.get("minutes", 2) * 60)))
                                     for q in qs]
        else:
            self.recommended_list = [self.recommended] * self.n
        self._sync_recommended()

        # ----- timers -----
        self.overall = Timer(
            duration=self.target_seconds,
            mode="countdown" if self.target_seconds > 0 else "stopwatch",
            on_tick=self._on_overall_tick,
            master=self.app,
        )
        self.qtimer = None

        self.build()
        self.overall.start()
        self._start_qtimer()
        self.refresh_all()
        self.focus_set()

    # ====================================================================== UI
    def build(self):
        colors = self.colors

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 4))
        ctk.CTkLabel(
            top, text=f"{self.subject}  •  {self.chapter}",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=colors["text"],
        ).pack(side="left")
        self.mini_btn = ctk.CTkButton(
            top, text="🗗 Miniplayer", command=self.open_mini, height=32,
            fg_color=colors["card"], text_color=colors["text"],
            border_width=1, border_color=colors["border"])
        self.mini_btn.pack(side="right", padx=4)
        self.fs_btn = ctk.CTkButton(
            top, text="⛶ Fullscreen", width=110, height=32, command=self.toggle_fullscreen,
            fg_color=colors["card"], text_color=colors["text"],
            border_width=1, border_color=colors["border"])
        self.fs_btn.pack(side="right", padx=4)
        self.top_btn = ctk.CTkButton(
            top, text="📌 On Top", width=100, height=32, command=self.toggle_ontop,
            fg_color=colors["card"], text_color=colors["text"],
            border_width=1, border_color=colors["border"])
        self.top_btn.pack(side="right", padx=4)

        # Overall card
        ov = Card(self, height=120)
        ov.pack(fill="x", padx=24, pady=8)
        title = "TIME REMAINING" if self.target_seconds > 0 else "TIME ELAPSED"
        ctk.CTkLabel(ov, text=title, font=ctk.CTkFont(size=12),
                     text_color=colors["muted"]).pack(pady=(12, 0))
        self.overall_label = ctk.CTkLabel(
            ov, text=format_time(self.target_seconds) if self.target_seconds > 0 else "00:00",
            font=ctk.CTkFont(size=44, weight="bold"), text_color=colors["text"])
        self.overall_label.pack()
        self.overall_sub = ctk.CTkLabel(
            ov, text=f"Target: {self.config.get('target_minutes', 0)} min",
            font=ctk.CTkFont(size=12), text_color=colors["muted"])
        self.overall_sub.pack()

        # Progress
        self.progress = ctk.CTkProgressBar(self, height=14, corner_radius=7)
        self.progress.pack(fill="x", padx=24, pady=(4, 8))
        self.progress.set(0)

        # Main grid
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=4)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = Card(main, height=240)
        left.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(left, text="CURRENT QUESTION", font=ctk.CTkFont(size=12),
                     text_color=colors["muted"]).pack(pady=(16, 0))
        self.qnum_label = ctk.CTkLabel(
            left, text=f"Q{self.current}", font=ctk.CTkFont(size=40, weight="bold"),
            text_color=colors["text"])
        self.qnum_label.pack(pady=(4, 0))
        ctk.CTkLabel(left, text="TIME ON QUESTION", font=ctk.CTkFont(size=12),
                     text_color=colors["muted"]).pack(pady=(20, 0))
        self.q_label = ctk.CTkLabel(
            left, text="00:00", font=ctk.CTkFont(size=48, weight="bold"),
            text_color=colors["success"])
        self.q_label.pack()

        right = Card(main, height=240)
        right.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(right, text="TRACKING", font=ctk.CTkFont(size=12),
                     text_color=colors["muted"]).pack(anchor="w", padx=16, pady=(14, 4))
        self.rec_label = self._stat_row(right, "Recommended")
        self.cur_label = self._stat_row(right, "Current")
        self.diff_label = self._stat_row(right, "Difference")
        self.avg_label = self._stat_row(right, "Avg / Q")
        self.rem_label = self._stat_row(right, "Remaining")

        # Smart alert banner
        self.alert_frame = ctk.CTkFrame(
            self, fg_color=colors["card"], corner_radius=12,
            border_width=1, border_color=colors["border"])
        self.alert_frame.pack(fill="x", padx=24, pady=(0, 8))
        self.alert_label = ctk.CTkLabel(
            self.alert_frame, text="Solve at your own pace. Stay sharp!",
            text_color=colors["muted"], font=ctk.CTkFont(size=13))
        self.alert_label.pack(padx=16, pady=10)

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=8)
        self.prev_btn = accent_button(btns, "← Prev", command=self.go_prev, primary=False,
                                      width=10, font=ctk.CTkFont(size=13))
        self.prev_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.skip_btn = accent_button(btns, "Skip (S)", command=self.skip, primary=False,
                                      width=10, font=ctk.CTkFont(size=13))
        self.skip_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.pause_btn = accent_button(btns, "⏸ Pause", command=self.toggle_pause, primary=False,
                                       width=10, font=ctk.CTkFont(size=13))
        self.pause_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.next_btn = accent_button(btns, "Next (↵) →", command=self.go_next, width=10,
                                      font=ctk.CTkFont(size=13))
        self.next_btn.pack(side="left", padx=4, expand=True, fill="x")
        self.finish_btn = accent_button(btns, "Finish", command=self.finish, width=10,
                                       font=ctk.CTkFont(size=13))
        self.finish_btn.pack(side="left", padx=4, expand=True, fill="x")

        # Keyboard shortcuts (guarded by current screen + finished flag)
        self.app.bind("<space>", self._kb_space)
        self.app.bind("<Return>", self._kb_enter)
        self.app.bind("<BackSpace>", self._kb_back)
        self.app.bind("<s>", self._kb_skip)
        self.app.bind("<S>", self._kb_skip)

    def _stat_row(self, parent, label):
        colors = self.colors
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text=label, text_color=colors["muted"],
                     font=ctk.CTkFont(size=12), width=120, anchor="w").pack(side="left")
        val = ctk.CTkLabel(row, text="—", text_color=colors["text"],
                           font=ctk.CTkFont(size=13, weight="bold"))
        val.pack(side="left")
        return val

    # ================================================================== mini
    def open_mini(self):
        if self.mini is not None:
            return
        self.mini = MiniPlayer(self.app, self)
        try:
            self.app.withdraw()  # hide the full window; mini stays on top
        except Exception:
            pass

    def push_mini(self):
        if not self.mini:
            return
        try:
            self.mini.update_overall(
                self.overall_label.cget("text"), self.overall_label.cget("text_color"))
            self.mini.update_question(
                self.q_label.cget("text"), self.q_label.cget("text_color"),
                self.current, format_time(self.recommended))
        except Exception:
            pass

    # ================================================================== timers
    def _on_overall_tick(self, elapsed):
        self.after(0, self._update_overall, elapsed)

    def _update_overall(self, elapsed):
        if self.target_seconds > 0:
            remaining = max(0, self.target_seconds - elapsed)
            self.overall_label.configure(text=format_time(remaining))
            if remaining <= 0:
                self.overall_label.configure(text_color=self.colors["danger"])
                if not self._timeup:
                    self._timeup = True
                    self.show_alert("Time's up! Finish whenever you're ready.", "danger")
                    if self.app.settings.get("notification_sound"):
                        play_beep(660, 300)
            else:
                self.overall_label.configure(text_color=self.colors["text"])
        else:
            self.overall_label.configure(text=format_time(elapsed))
        self.push_mini()

    def _on_q_tick(self, elapsed):
        self.after(0, self._update_q, elapsed)

    def _update_q(self, elapsed):
        self.times[self.current - 1] = elapsed
        status = self._status_for(elapsed)
        color_map = {
            "green": self.colors["success"],
            "yellow": self.colors["warning"],
            "red": self.colors["danger"],
        }
        self.q_label.configure(text_color=color_map[status])
        if status != self.last_q_status:
            self.last_q_status = status
            self._maybe_alert(status)
        self.refresh_all()

    def _start_qtimer(self):
        # Stop any existing per-question timer first.
        if self.qtimer:
            try:
                self.qtimer.stop()
            except Exception:
                pass
        # ALWAYS create a fresh Timer before starting it.
        # (This is the fix for the 'NoneType' has no attribute 'start' error.)
        self.qtimer = Timer(duration=0, mode="stopwatch",
                            on_tick=self._on_q_tick, interval=0.1, master=self.app)
        self.qtimer.start()
        if self.paused:
            self.qtimer.pause()

    # ================================================================== status
    def _status_for(self, elapsed):
        if elapsed > self.recommended * 1.5:
            return "red"
        if elapsed > self.recommended:
            return "yellow"
        return "green"

    def _ahead_of_schedule(self):
        if self.target_seconds <= 0:
            return False
        expected = (self.current / self.n) * self.target_seconds
        return self.overall.get_elapsed() < expected * 0.9

    def _sync_recommended(self):
        """Keep self.recommended pointing at the CURRENT question's plan."""
        self.recommended = self.recommended_list[self.current - 1]

    def _maybe_alert(self, status):
        if status == "red":
            self.show_alert("You've spent too much time here. Consider skipping.", "danger")
            if self.app.settings.get("notification_sound"):
                play_beep(330, 220)
        elif status == "yellow":
            self.show_alert("Over the recommended time — keep moving.", "warning")
        elif status == "green" and self._ahead_of_schedule():
            self.show_alert("Excellent speed! You're ahead of schedule.", "success")

    def show_alert(self, msg, kind):
        colors = self.colors
        col = {
            "danger": colors["danger"],
            "warning": colors["warning"],
            "success": colors["success"],
            "info": colors["text"],
        }.get(kind, colors["text"])
        self.alert_label.configure(text=msg, text_color=col)
        self.alert_frame.configure(border_color=col)

    # ================================================================== actions
    def _commit_current_question(self):
        if self.qtimer:
            self.times[self.current - 1] += self.qtimer.get_elapsed()

    def go_next(self):
        if self.finished:
            return
        self._commit_current_question()
        if self.current < self.n:
            self.current += 1
            self._sync_recommended()
            self.last_q_status = "green"
            self._start_qtimer()
            self.refresh_all()
        else:
            self.finish()
        self.focus_set()

    def go_prev(self):
        if self.finished:
            return
        self._commit_current_question()
        if self.current > 1:
            self.current -= 1
            self._sync_recommended()
            self.last_q_status = "green"
            self._start_qtimer()
            self.refresh_all()
        self.focus_set()

    def skip(self):
        if self.finished:
            return
        self._commit_current_question()
        self.skipped[self.current - 1] = True
        self.show_alert("Question skipped.", "warning")
        if self.current < self.n:
            self.current += 1
            self._sync_recommended()
            self.last_q_status = "green"
            self._start_qtimer()
            self.refresh_all()
        else:
            self.finish()
        self.focus_set()

    def toggle_pause(self):
        if self.finished:
            return
        if not self.paused:
            self.overall.pause()
            self.qtimer.pause()
            self.paused = True
            self.pause_btn.configure(text="▶ Resume")
            self.show_alert("Paused.", "info")
        else:
            self.overall.resume()
            self.qtimer.resume()
            self.paused = False
            self.pause_btn.configure(text="⏸ Pause")
            self.show_alert("Resumed.", "info")
        self.focus_set()

    def finish(self):
        if self.finished:
            return
        # close miniplayer first (restores the main window)
        if self.mini is not None:
            self.mini.close_mini()
        # remove keyboard bindings
        for k in ("<space>", "<Return>", "<BackSpace>", "<s>", "<S>"):
            try:
                self.app.unbind(k)
            except Exception:
                pass
        self._commit_current_question()
        self.overall.stop()
        if self.qtimer:
            self.qtimer.stop()
        self.finished = True
        self.save_and_report()

    # ================================================================== display
    def refresh_all(self):
        colors = self.colors
        elapsed = self.times[self.current - 1]

        self.qnum_label.configure(text=f"Q{self.current}")
        self.q_label.configure(text=format_time(elapsed))
        self.cur_label.configure(text=format_time(elapsed))

        diff = elapsed - self.recommended
        sign = "+" if diff >= 0 else "-"
        self.diff_label.configure(text=f"{sign}{format_time(abs(diff))}")
        self.diff_label.configure(
            text_color=colors["danger"] if diff > 0 else colors["success"])

        answered = [t for t in self.times if t > 0]
        avg = sum(answered) / len(answered) if answered else 0
        self.avg_label.configure(text=format_time(avg))
        self.rem_label.configure(text=f"{max(0, self.n - self.current)} left")

        done = sum(1 for i in range(self.n) if self.times[i] > 0 or self.skipped[i])
        self.progress.set(done / self.n if self.n else 0)
        self.rec_label.configure(text=format_time(self.recommended))
        self.push_mini()

    # ================================================================== persist
    def save_and_report(self):
        actual = self.overall.get_elapsed()
        answered = sum(1 for t in self.times if t > 0)
        skipped_count = sum(1 for s in self.skipped if s)
        completion = round(answered / self.n * 100) if self.n else 0
        above = sum(1 for i, t in enumerate(self.times)
                    if t > 0 and t > self.recommended * 1.5)
        avg = sum(self.times) / self.n if self.n else 0
        nonzero = [t for t in self.times if t > 0]
        fastest = min(nonzero) if nonzero else 0
        slowest = max(nonzero) if nonzero else 0

        if self.target_seconds == 0:
            speed_score = 100
        elif actual > 0:
            speed_score = clamp((self.target_seconds / actual) * 100, 0, 120)
        else:
            speed_score = 100
        efficiency = round(0.5 * completion + 0.5 * min(100, speed_score))

        dpp_id = self.app.db.add_dpp(
            subject=self.subject,
            chapter=self.chapter,
            num_questions=self.n,
            target_time=self.target_seconds,
            actual_time=actual,
            avg_time=avg,
            efficiency=efficiency,
            completion=completion,
            skipped=skipped_count,
            above_recommended=above,
            source=self.config.get("source", "manual"),
            pdf_name=self.config.get("pdf_name", ""),
            pages=self.config.get("pages", 0),
        )
        for i in range(self.n):
            self.app.db.add_question(
                dpp_id, i + 1, self.times[i], self.skipped[i], self.recommended_list[i])

        self.app._current_dpp_id = dpp_id
        self.app.show_report(dpp_id)

    # ================================================================== extras
    def toggle_fullscreen(self):
        self._fs = not getattr(self, "_fs", False)
        self.app.attributes("-fullscreen", self._fs)
        self.fs_btn.configure(text="🗗 Exit FS" if self._fs else "⛶ Fullscreen")

    def toggle_ontop(self):
        self._ontop = not getattr(self, "_ontop", False)
        self.app.attributes("-topmost", self._ontop)
        self.top_btn.configure(text="📌 On Top ✓" if self._ontop else "📌 On Top")

    # ------------------------------------------------------------ key handlers
    def _kb_space(self, _event):
        if self.app.current != "solving" or self.finished:
            return
        self.toggle_pause()

    def _kb_enter(self, _event):
        if self.app.current != "solving" or self.finished:
            return
        self.go_next()

    def _kb_back(self, _event):
        if self.app.current != "solving" or self.finished:
            return
        self.go_prev()

    def _kb_skip(self, _event):
        if self.app.current != "solving" or self.finished:
            return
        self.skip()