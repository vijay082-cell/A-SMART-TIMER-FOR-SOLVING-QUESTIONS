"""
history.py
----------
Browse, search, view and delete past DPP reports.
"""

import customtkinter as ctk
from tkinter import messagebox

from ui import Card, get_colors, Toast
from utils import format_time


class HistoryScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.colors = get_colors()
        self.build()
        self.refresh()

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
        ctk.CTkLabel(top, text="History", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=colors["text"]).pack(side="left", padx=14)

        self.search = ctk.CTkEntry(
            top, placeholder_text="Search subject / chapter / date…",
            height=34, width=260)
        self.search.pack(side="right")
        self.search.bind("<KeyRelease>", lambda _e: self.refresh())

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=8)

    # ------------------------------------------------------------------- data
    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        q = self.search.get().strip()
        dpps = self.app.db.search_dpps(q) if q else self.app.db.get_all_dpps(limit=500)
        if not dpps:
            ctk.CTkLabel(self.scroll, text="No DPPs found.", text_color=self.colors["muted"]
                         ).pack(pady=20)
            return
        for d in dpps:
            self.make_row(d)

    def make_row(self, d):
        colors = self.colors
        row = ctk.CTkFrame(
            self.scroll, fg_color=colors["card"], corner_radius=12,
            border_width=1, border_color=colors["border"])
        row.pack(fill="x", pady=5)

        ctk.CTkLabel(row, text=f"{d['subject']} • {d['chapter']}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=colors["text"]).pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(row, text=d["date"], font=ctk.CTkFont(size=11),
                     text_color=colors["muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(row, text=f"Eff {d['efficiency']:.0f}%  •  {format_time(d['actual_time'])}",
                     text_color=colors["muted"]).pack(side="left", padx=10)

        ctk.CTkButton(
            row, text="View", width=80, height=30,
            command=lambda _id=d["id"]: self.app.show_report(_id),
            fg_color=colors["card"], text_color=colors["text"],
            border_width=1, border_color=colors["border"]).pack(side="right", padx=6)
        ctk.CTkButton(
            row, text="Delete", width=80, height=30,
            command=lambda _id=d["id"]: self.confirm_delete(_id),
            fg_color=colors["danger"], text_color="#ffffff").pack(side="right", padx=6)

    # ------------------------------------------------------------------ delete
    def confirm_delete(self, dpp_id):
        win = ctk.CTkToplevel(self.app)
        win.title("Confirm Delete")
        win.geometry("320x150")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text="Delete this DPP report?",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=18)
        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(pady=8)
        ctk.CTkButton(
            btns, text="Cancel", width=100, command=win.destroy,
            fg_color=self.colors["card"], text_color=self.colors["text"],
            border_width=1, border_color=self.colors["border"]).pack(side="left", padx=6)
        ctk.CTkButton(
            btns, text="Delete", width=100, fg_color=self.colors["danger"],
            text_color="#ffffff", command=lambda: self.do_delete(dpp_id, win)).pack(
            side="left", padx=6)

    def do_delete(self, dpp_id, win):
        self.app.db.delete_dpp(dpp_id)
        win.destroy()
        self.refresh()
        Toast.show("Deleted", "Report removed.", "info")
