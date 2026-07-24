"""
settings.py
-----------
User settings: theme (Dark/Light), accent color, notification sound,
default target time, auto-save. Changes persist to JSON and apply live.
"""

import customtkinter as ctk

from ui import Card, accent_button, get_colors, Toast, ACCENT_PRESETS
from utils import save_settings


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.colors = get_colors()
        self.s = dict(app.settings)  # work on a copy
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
        ctk.CTkLabel(top, text="Settings", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=colors["text"]).pack(side="left", padx=14)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=8)

        card = Card(body)
        card.pack(fill="x", pady=6)
        ctk.CTkLabel(card, text="Appearance", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=colors["text"]).pack(anchor="w", padx=16, pady=(12, 2))

        self.theme_switch = ctk.CTkSwitch(
            card, text="Dark Mode", command=self.on_theme,
            onvalue="dark", offvalue="light")
        self.theme_switch.pack(anchor="w", padx=16, pady=(4, 8))
        if self.s["theme"] == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        ctk.CTkLabel(card, text="Accent Color", text_color=colors["muted"]).pack(
            anchor="w", padx=16, pady=(6, 2))
        self.accent_var = ctk.StringVar(value=self._accent_name())
        ctk.CTkOptionMenu(
            card, variable=self.accent_var, values=list(ACCENT_PRESETS.keys()),
            command=self.on_accent).pack(anchor="w", padx=16, pady=(2, 8))

        self.sound_switch = ctk.CTkSwitch(card, text="Notification Sound",
                                         command=self.on_sound)
        self.sound_switch.pack(anchor="w", padx=16, pady=(4, 8))
        if self.s["notification_sound"]:
            self.sound_switch.select()
        else:
            self.sound_switch.deselect()

        self.auto_switch = ctk.CTkSwitch(card, text="Auto Save Reports",
                                        command=self.on_auto)
        self.auto_switch.pack(anchor="w", padx=16, pady=(4, 8))
        if self.s.get("auto_save", True):
            self.auto_switch.select()
        else:
            self.auto_switch.deselect()

        ctk.CTkLabel(card, text="Default Target Time (minutes)",
                     text_color=colors["muted"]).pack(anchor="w", padx=16, pady=(6, 2))
        self.def_target = ctk.CTkEntry(card, height=36, width=160)
        self.def_target.insert(0, str(self.s.get("default_target_minutes", 60)))
        self.def_target.pack(anchor="w", padx=16, pady=(2, 12))

        # --- AI difficulty engine ---
        ai_card = Card(body)
        ai_card.pack(fill="x", pady=6)
        ctk.CTkLabel(ai_card, text="AI Difficulty Engine",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=colors["text"]).pack(anchor="w", padx=16, pady=(12, 2))
        self.ai_var = ctk.StringVar(value=self.s.get("ai_backend", "heuristic"))
        ctk.CTkSegmentedButton(
            ai_card, values=["heuristic", "ollama"], variable=self.ai_var,
            command=self.on_ai).pack(anchor="w", padx=16, pady=(4, 4))
        ctk.CTkLabel(
            ai_card,
            text="Heuristic = free offline rules (works now). Local AI (Ollama) = a free "
                 "open-source model on your PC for smarter analysis (advanced setup; "
                 "auto-falls back to Heuristic if not installed).",
            text_color=colors["muted"], font=ctk.CTkFont(size=11), justify="left").pack(
            anchor="w", padx=16, pady=(2, 12))

        accent_button(
            self, "Save Settings", command=self.save, height=44,
            font=ctk.CTkFont(size=15, weight="bold")).pack(fill="x", padx=24, pady=(6, 12))
        ctk.CTkLabel(self, text="Tip: Changes apply immediately after saving.",
                     text_color=colors["muted"], font=ctk.CTkFont(size=11)).pack(pady=(0, 10))

    # ------------------------------------------------------------------ helpers
    def _accent_name(self):
        for k, v in ACCENT_PRESETS.items():
            if v.lower() == self.s["accent"].lower():
                return k
        return "Blue"

    # ------------------------------------------------------------------ handlers
    def on_theme(self):
        self.s["theme"] = self.theme_switch.get()

    def on_accent(self, name):
        self.s["accent"] = ACCENT_PRESETS[name]

    def on_sound(self):
        self.s["notification_sound"] = self.sound_switch.get() == "on"

    def on_auto(self):
        self.s["auto_save"] = self.auto_switch.get() == "on"

    def on_ai(self, value):
        self.s["ai_backend"] = value

    def save(self):
        try:
            self.s["default_target_minutes"] = int(self.def_target.get() or 60)
        except ValueError:
            self.s["default_target_minutes"] = 60
        self.app.settings = self.s
        save_settings(self.s)
        self.app.apply_theme()
        Toast.show("Saved", "Settings applied.", "success")