"""
dashboard.py
------------
Home screen (luxury edition): live animated background shows through, a large
centered daily quote (the "title of the day"), quick stats that count up, and
navigation cards with gold hover-glow.
"""

import customtkinter as ctk

from ui import Card, accent_button, get_colors, Toast, count_up_label, LUX_GOLD
from utils import format_time, save_settings
from quotes import get_daily_quote


class Dashboard(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.colors = get_colors()
        self.build()

    def build(self):
        colors = self.colors

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(22, 4))
        ctk.CTkLabel(top, text="DPP Timer AI", font=ctk.CTkFont(family="Georgia", size=26, weight="bold"), text_color=LUX_GOLD).pack(side="left")
        ctk.CTkLabel(top, text="Smart time tracking for JEE aspirants", font=ctk.CTkFont(size=13), text_color=colors["muted"]).pack(side="left", padx=(12, 0))
        self.theme_switch = ctk.CTkSwitch(top, text="Dark Mode", command=self.toggle_theme, onvalue="dark", offvalue="light")
        self.theme_switch.pack(side="right")
        if self.app.settings["theme"] == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        quote_frame = ctk.CTkFrame(self, fg_color="transparent")
        quote_frame.pack(fill="x", padx=40, pady=(6, 10))
        q_text, q_author = get_daily_quote()
        ctk.CTkLabel(quote_frame, text=f"\u201C{q_text}\u201D", font=ctk.CTkFont(family="Georgia", size=22, slant="italic", weight="bold"), text_color=LUX_GOLD, wraplength=900, justify="center").pack(pady=(4, 0))
        ctk.CTkLabel(quote_frame, text=f"— {q_author}", font=ctk.CTkFont(family="Georgia", size=13, slant="italic"), text_color=colors["muted"]).pack(pady=(4, 0))

        statbar = ctk.CTkFrame(self, fg_color="transparent")
        statbar.pack(fill="x", padx=30, pady=8)
        for label, value, fmt in self.get_quick_stats():
            c = Card(statbar, height=92)
            c.pack(side="left", padx=6, pady=6, expand=True, fill="x")
            val_lbl = ctk.CTkLabel(c, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color=colors["text"])
            val_lbl.pack(pady=(14, 0))
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=12), text_color=colors["muted"]).pack()
            count_up_label(c, val_lbl, value, duration_ms=800, fmt=fmt, start_value=0)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=30, pady=10)
        grid.columnconfigure((0, 1), weight=1)
        grid.rowconfigure((0, 1), weight=1)

        self.make_nav_card(grid, 0, 0, "Start New DPP", "Begin a fresh practice session", self.app.show_new_dpp, LUX_GOLD)
        self.make_nav_card(grid, 0, 1, "History", "Review and manage past DPPs", self.app.show_history, "#8b5cf6")
        self.make_nav_card(grid, 1, 0, "Statistics", "Track progress & solving speed", self.app.show_statistics, "#22c55e")
        self.make_nav_card(grid, 1, 1, "Settings", "Customize theme, accent & more", self.app.show_settings, "#f59e0b")

    def make_nav_card(self, parent, r, c, title, desc, command, color):
        colors = self.colors
        card = Card(parent, height=150)
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(card, text="●", text_color=color, font=ctk.CTkFont(size=28)).pack(anchor="w", padx=20, pady=(18, 0))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=20, pady=(6, 0))
        ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color=colors["muted"]).pack(anchor="w", padx=20, pady=(4, 0))
        accent_button(card, "Open", command=command, width=110, height=32, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(14, 0))

    def toggle_theme(self):
        self.app.settings["theme"] = self.theme_switch.get()
        save_settings(self.app.settings)
        self.app.apply_theme()

    def get_quick_stats(self):
        dpps = self.app.db.get_all_dpps(limit=10000)
        total = len(dpps)
        total_time = sum(d["actual_time"] for d in dpps)
        avg_eff = (sum(d["efficiency"] for d in dpps) / total) if total else 0
        return [
            ("Total DPPs", total, lambda v: str(int(v))),
            ("Study Time", total_time, lambda v: format_time(v)),
            ("Avg Efficiency", avg_eff, lambda v: f"{int(v)}%"),
            ("Sessions", total, lambda v: str(int(v))),
        ]