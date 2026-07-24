"""
main.py
-------
Entry point for DPP Timer AI (luxury edition).
"""

import customtkinter as ctk

from database import Database
from utils import load_settings, DB_PATH
import ui

from dashboard import Dashboard
from new_dpp import NewDPPScreen
from solving import SolvingScreen
from report import ReportScreen
from history import HistoryScreen
from stats import StatisticsScreen
from settings import SettingsScreen


class DPPTimerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DPP Timer AI")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self.settings = load_settings()
        ctk.set_appearance_mode(self.settings["theme"])
        ctk.set_default_color_theme("blue")

        self.bg = ui.AnimatedBackground(self)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        ui.Toast.set_root(self)
        try:
            self.iconphoto(True, ui.load_logo_tk())
        except Exception:
            pass

        self.db = Database(DB_PATH)
        self.current = "dashboard"
        self._current_dpp_id = None
        self._booting = True

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_dashboard()
        self._booting = False

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _navigate(self, builder):
        if self._booting or not self.winfo_viewable():
            builder()
            return
        ui.fade_transition(self, builder, duration_ms=160)

    def show_dashboard(self):
        self.current = "dashboard"
        self._navigate(lambda: (self._clear(), Dashboard(self.content, self).pack(fill="both", expand=True)))

    def show_new_dpp(self):
        self.current = "new_dpp"
        self._navigate(lambda: (self._clear(), NewDPPScreen(self.content, self).pack(fill="both", expand=True)))

    def show_solving(self, config):
        self.current = "solving"
        self._navigate(lambda: (self._clear(), SolvingScreen(self.content, self, config).pack(fill="both", expand=True)))

    def show_report(self, dpp_id):
        self.current = "report"
        self._current_dpp_id = dpp_id
        self._navigate(lambda: (self._clear(), ReportScreen(self.content, self, dpp_id).pack(fill="both", expand=True)))

    def show_history(self):
        self.current = "history"
        self._navigate(lambda: (self._clear(), HistoryScreen(self.content, self).pack(fill="both", expand=True)))

    def show_statistics(self):
        self.current = "statistics"
        self._navigate(lambda: (self._clear(), StatisticsScreen(self.content, self).pack(fill="both", expand=True)))

    def show_settings(self):
        self.current = "settings"
        self._navigate(lambda: (self._clear(), SettingsScreen(self.content, self).pack(fill="both", expand=True)))

    def apply_theme(self):
        ctk.set_appearance_mode(self.settings["theme"])
        if self.current == "report":
            self.show_report(self._current_dpp_id)
        else:
            getattr(self, f"show_{self.current}")()

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = DPPTimerApp()
    app.run()