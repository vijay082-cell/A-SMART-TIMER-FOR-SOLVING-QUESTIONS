"""
statistics.py
-------------
Beautiful analytics: daily / weekly / monthly study time, average speed per
subject, average efficiency per subject, plus best & worst performance cards.
Charts are rendered with Matplotlib and embedded as CTkImages.
"""

import customtkinter as ctk

from ui import Card, get_colors, fig_to_image
from utils import format_time


class StatisticsScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.colors = get_colors()
        self._imgs = []
        self.build()

    # -------------------------------------------------------------------- build
    def build(self):
        colors = self.colors
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 4))
        ctk.CTkButton(
            top, text="← Dashboard", width=120, height=32,
            command=self.app.show_dashboard, fg_color=colors["card"],
            text_color=colors["text"], border_width=1, border_color=colors["border"],
        ).pack(side="left")
        ctk.CTkLabel(top, text="Statistics", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=colors["text"]).pack(side="left", padx=14)

        # Best / Worst
        best, worst = self.app.db.get_best_worst()
        if best:
            bw = ctk.CTkFrame(self, fg_color="transparent")
            bw.pack(fill="x", padx=24, pady=6)
            for i in range(2):
                bw.columnconfigure(i, weight=1)
            c1 = Card(bw, height=80)
            c1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(c1, text=f"Best: {best['efficiency']:.0f}%",
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=colors["success"]).pack(pady=(14, 0))
            ctk.CTkLabel(c1, text=f"{best['subject']} • {best['chapter']}",
                         text_color=colors["muted"], font=ctk.CTkFont(size=11)).pack()
            c2 = Card(bw, height=80)
            c2.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(c2, text=f"Worst: {worst['efficiency']:.0f}%",
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=colors["danger"]).pack(pady=(14, 0))
            ctk.CTkLabel(c2, text=f"{worst['subject']} • {worst['chapter']}",
                         text_color=colors["muted"], font=ctk.CTkFont(size=11)).pack()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=8)

        series = self.app.db.get_study_series()
        subj = self.app.db.get_subject_stats()

        self.add_chart(scroll, "Daily Study Time (min)",
                       self.line_chart([(k, round(v / 60, 1)) for k, v in series["daily"]]))
        self.add_chart(scroll, "Weekly Study Time (min)",
                       self.line_chart([(k, round(v / 60, 1)) for k, v in series["weekly"]]))
        self.add_chart(scroll, "Monthly Study Time (min)",
                       self.line_chart([(k, round(v / 60, 1)) for k, v in series["monthly"]]))
        self.add_chart(scroll, "Average Speed per Subject (sec/q)",
                       self.bar_chart(list(subj.keys()),
                                     [round(s["avg_speed"], 1) for s in subj.values()]))
        self.add_chart(scroll, "Average Efficiency per Subject (%)",
                       self.bar_chart(list(subj.keys()),
                                     [round(s["avg_efficiency"], 1) for s in subj.values()]))

    # ------------------------------------------------------------------ charts
    def add_chart(self, parent, title, fig):
        colors = self.colors
        card = Card(parent)
        card.pack(fill="x", pady=6)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=colors["text"]).pack(anchor="w", padx=14, pady=(10, 0))
        img = fig_to_image(fig, size=(820, 260))
        self._imgs.append(img)
        ctk.CTkLabel(card, text="", image=img).pack(padx=10, pady=10)

    def line_chart(self, data):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 3))
        if data:
            xs = [d[0] for d in data]
            ys = [d[1] for d in data]
            ax.plot(range(len(xs)), ys, marker="o", color="#3b82f6")
            ax.set_xticks(range(len(xs)))
            ax.set_xticklabels(xs, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel("Minutes")
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
        fig.tight_layout()
        return fig

    def bar_chart(self, labels, values):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 3))
        if labels:
            ax.bar(labels, values, color="#22c55e")
            ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
        fig.tight_layout()
        return fig
