"""
miniplayer.py
-------------
Compact, always-on-top floating player shown during a DPP session.
Displays subject, chapter, the overall DPP timer and the per-question timer,
with minimal controls (Prev / Pause / Next / Finish / Expand).
"""

import customtkinter as ctk

from ui import get_colors, LUX_GOLD


class MiniPlayer(ctk.CTkToplevel):
    def __init__(self, app, solving):
        super().__init__(app)
        self.app = app
        self.solving = solving
        self.title("DPP Miniplayer")
        self.geometry("330x478")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.colors = get_colors()

        # Subject (gold) + chapter (muted)
        self.sub_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color=LUX_GOLD, wraplength=300, justify="center")
        self.sub_lbl.pack(pady=(14, 0))
        self.chap_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color=self.colors["muted"],
            wraplength=300, justify="center")
        self.chap_lbl.pack(pady=(2, 0))

        # Overall DPP timer
        ctk.CTkLabel(self, text="OVERALL DPP TIME", font=ctk.CTkFont(size=11),
                     text_color=self.colors["muted"]).pack(pady=(16, 0))
        self.overall_lbl = ctk.CTkLabel(
            self, text="00:00", font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.colors["text"])
        self.overall_lbl.pack()

        # Current question timer
        self.qnum_lbl = ctk.CTkLabel(
            self, text="QUESTION 1", font=ctk.CTkFont(size=11),
            text_color=self.colors["muted"])
        self.qnum_lbl.pack(pady=(12, 0))
        self.q_lbl = ctk.CTkLabel(
            self, text="00:00", font=ctk.CTkFont(size=40, weight="bold"),
            text_color="#3fb950")
        self.q_lbl.pack()
        self.rec_lbl = ctk.CTkLabel(
            self, text="Recommended: 00:00", font=ctk.CTkFont(size=11),
            text_color=self.colors["muted"])
        self.rec_lbl.pack(pady=(2, 0))

        # Controls row 1: Prev / Pause / Next
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkButton(row1, text="⏮ Prev", width=90, height=36,
                      command=self.solving.go_prev, fg_color=self.colors["card"],
                      text_color=self.colors["text"], border_width=1,
                      border_color=self.colors["border"]).pack(
            side="left", padx=4, expand=True, fill="x")
        self.pause_btn = ctk.CTkButton(row1, text="⏸ Pause", width=90, height=36,
                      command=self.toggle_pause, fg_color=self.colors["card"],
                      text_color=self.colors["text"], border_width=1,
                      border_color=self.colors["border"])
        self.pause_btn.pack(side="left", padx=4, expand=True, fill="x")
        ctk.CTkButton(row1, text="Next ⏭", width=90, height=36,
                      command=self.solving.go_next, fg_color=self.colors["card"],
                      text_color=self.colors["text"], border_width=1,
                      border_color=self.colors["border"]).pack(
            side="left", padx=4, expand=True, fill="x")

        # Controls row 2: Finish / Expand
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(4, 8))
        ctk.CTkButton(row2, text="Finish", width=140, height=38,
                      command=self.solving.finish, fg_color="#f85149",
                      text_color="#ffffff").pack(
            side="left", padx=4, expand=True, fill="x")
        ctk.CTkButton(row2, text="Expand ↗", width=140, height=38,
                      command=self.close_mini, fg_color=LUX_GOLD,
                      text_color="#10131a").pack(
            side="left", padx=4, expand=True, fill="x")

        self.protocol("WM_DELETE_WINDOW", self.close_mini)
        # push the current state immediately
        self.solving.push_mini()

    # -------------------------------------------------------------- live updates
    def update_overall(self, text, color):
        try:
            self.overall_lbl.configure(text=text, text_color=color)
        except Exception:
            pass

    def update_question(self, text, color, qnum, rec_text):
        try:
            self.q_lbl.configure(text=text, text_color=color)
            self.qnum_lbl.configure(text=f"QUESTION {qnum}")
            self.rec_lbl.configure(text=f"Recommended: {rec_text}")
        except Exception:
            pass

    def toggle_pause(self):
        self.solving.toggle_pause()
        self.pause_btn.configure(
            text="▶ Resume" if self.solving.paused else "⏸ Pause")

    def close_mini(self):
        """Restore the main window and detach this miniplayer."""
        self.solving.mini = None
        try:
            self.app.deiconify()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass