"""
report.py
---------
End-of-DPP report screen with count-up numbers and a daily quote.
"""

import customtkinter as ctk

from ui import Card, get_colors, fig_to_image, count_up_label, LUX_GOLD
from utils import format_time
from quotes import get_daily_quote


class ReportScreen(ctk.CTkFrame):
    def __init__(self, master, app, dpp_id):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.dpp_id = dpp_id
        self.colors = get_colors()
        self.dpp = app.db.get_dpp(dpp_id)
        self.questions = app.db.get_questions(dpp_id)
        self._imgs = []
        self.build()

    def build(self):
        colors = self.colors
        dpp = self.dpp

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 4))
        ctk.CTkButton(top, text="← Dashboard", width=120, height=32, command=self.app.show_dashboard, fg_color=colors["card"], text_color=colors["text"], border_width=1, border_color=colors["border"]).pack(side="left")
        ctk.CTkButton(top, text="History", width=100, height=32, command=self.app.show_history, fg_color=colors["card"], text_color=colors["text"], border_width=1, border_color=colors["border"]).pack(side="left", padx=8)

        ctk.CTkLabel(self, text="DPP Report", font=ctk.CTkFont(size=24, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=24, pady=(4, 0))
        ctk.CTkLabel(self, text=f"{dpp['subject']} • {dpp['chapter']} • {dpp['date']}", font=ctk.CTkFont(size=13), text_color=colors["muted"]).pack(anchor="w", padx=24, pady=(0, 4))
        q_text, q_author = get_daily_quote()
        ctk.CTkLabel(self, text=f"\u201C{q_text}\u201D  — {q_author}", font=ctk.CTkFont(family="Georgia", size=12, slant="italic"), text_color=LUX_GOLD).pack(anchor="w", padx=24, pady=(0, 10))

        eff = Card(self, height=110)
        eff.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(eff, text="EFFICIENCY SCORE", font=ctk.CTkFont(size=12), text_color=colors["muted"]).pack(pady=(12, 0))
        self.eff_label = ctk.CTkLabel(eff, text="0%", font=ctk.CTkFont(size=40, weight="bold"), text_color=colors["success"])
        self.eff_label.pack()
        count_up_label(eff, self.eff_label, dpp["efficiency"], duration_ms=1000, fmt=lambda v: f"{int(v)}%", start_value=0)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=6)
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        stats = [
            ("Total Time", dpp["actual_time"], lambda v: format_time(v)),
            ("Avg / Question", dpp["avg_time"], lambda v: format_time(v)),
            ("Fastest", self.fastest(), lambda v: format_time(v)),
            ("Slowest", self.slowest(), lambda v: format_time(v)),
            ("Skipped", dpp["skipped"], lambda v: str(int(v))),
            ("Above Rec.", dpp["above_recommended"], lambda v: str(int(v))),
            ("Completion", dpp["completion"], lambda v: f"{int(v)}%"),
            ("Questions", dpp["num_questions"], lambda v: str(int(v))),
        ]
        for idx, (label, value, fmt) in enumerate(stats):
            c = Card(grid, height=80)
            c.grid(row=idx // 4, column=idx % 4, padx=5, pady=5, sticky="nsew")
            vlabel = ctk.CTkLabel(c, text="0", font=ctk.CTkFont(size=18, weight="bold"), text_color=colors["text"])
            vlabel.pack(pady=(12, 0))
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=11), text_color=colors["muted"]).pack()
            count_up_label(c, vlabel, value, duration_ms=700, fmt=fmt, start_value=0)

        chart_frame = Card(self)
        chart_frame.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(chart_frame, text="Time per Question", font=ctk.CTkFont(size=13, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=14, pady=(10, 0))
        fig = self.make_chart()
        img = fig_to_image(fig, size=(820, 260))
        self._imgs.append(img)
        ctk.CTkLabel(chart_frame, text="", image=img).pack(padx=10, pady=10)

    def fastest(self):
        ts = [q["time_spent"] for q in self.questions if q["time_spent"] > 0]
        return min(ts) if ts else 0

    def slowest(self):
        ts = [q["time_spent"] for q in self.questions if q["time_spent"] > 0]
        return max(ts) if ts else 0

    def make_chart(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        nums = [q["question_number"] for q in self.questions]
        times = [q["time_spent"] for q in self.questions]
        rec = self.questions[0]["recommended_time"] if self.questions else 0
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.bar(nums, times, color="#3b82f6", label="Time spent")
        if rec > 0:
            ax.axhline(rec, color="#f59e0b", linestyle="--", linewidth=1.5, label=f"Recommended ({rec / 60:.1f} min)")
        ax.set_xlabel("Question #")
        ax.set_ylabel("Seconds")
        ax.set_title("Time Spent per Question")
        ax.legend()
        fig.tight_layout()
        return fig