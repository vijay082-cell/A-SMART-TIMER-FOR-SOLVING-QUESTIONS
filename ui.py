"""
ui.py
-----
Reusable UI primitives and theming helpers for DPP Timer AI (luxury edition).
"""

import os
import time
import random
import tkinter as tk
import customtkinter as ctk

from utils import load_settings, ASSETS_DIR, BASE_DIR


ACCENT_PRESETS = {
    "Gold": "#d4af37",
    "Blue": "#3b82f6",
    "Purple": "#8b5cf6",
    "Green": "#22c55e",
    "Orange": "#f97316",
    "Red": "#ef4444",
    "Teal": "#14b8a6",
}

LUX_GOLD = "#d4af37"
LUX_GOLD_SOFT = "#e8c87a"

_FRAME_MS = 16


def get_colors():
    dark = ctk.get_appearance_mode() == "Dark"
    if dark:
        return {
            "bg": "#06090f", "surface": "#0d1320", "card": "#121a2b",
            "card_hover": "#18233a", "text": "#eef2f8", "muted": "#8b97a8",
            "border": "#263149", "success": "#3fb950", "warning": "#d29922",
            "danger": "#f85149", "accent": load_settings()["accent"],
        }
    return {
        "bg": "#eef1f6", "surface": "#ffffff", "card": "#ffffff",
        "card_hover": "#eef2f7", "text": "#14181f", "muted": "#5b6675",
        "border": "#d4dae3", "success": "#1a7f37", "warning": "#9a6700",
        "danger": "#cf222e", "accent": load_settings()["accent"],
    }


def shade(hex_color, percent):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16); g = int(hex_color[2:4], 16); b = int(hex_color[4:6], 16)
    def adj(c):
        c = int(c * (1 + percent / 100.0)); return max(0, min(255, c))
    r, g, b = adj(r), adj(g), adj(b)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_to_hex(r, g, b):
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _mix(c1, c2, p):
    a = _hex_to_rgb(c1); b = _hex_to_rgb(c2)
    return _rgb_to_hex(
        round(a[0] + (b[0] - a[0]) * p),
        round(a[1] + (b[1] - a[1]) * p),
        round(a[2] + (b[2] - a[2]) * p),
    )


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def tween(master, duration_ms, on_step, on_done=None, easing=None):
    easing = easing or _ease_out_cubic
    t0 = time.time()
    def tick():
        elapsed = (time.time() - t0) * 1000.0
        p = min(1.0, elapsed / duration_ms)
        try:
            on_step(easing(p))
        except Exception:
            pass
        if p < 1:
            master.after(_FRAME_MS, tick)
        elif on_done:
            try:
                on_done()
            except Exception:
                pass
    master.after(_FRAME_MS, tick)


def count_up_label(master, label, to_value, duration_ms=700, fmt=None, start_value=0):
    fmt = fmt or (lambda v: str(int(round(v))))
    def step(p):
        v = start_value + (to_value - start_value) * p
        label.configure(text=fmt(v))
    tween(master, duration_ms, step)


def fade_transition(app, build_fn, duration_ms=170):
    """Crossfade the whole window: fade out, swap content, fade back in.

    Hardened: if the screen build raises, we NEVER leave the window invisible
    (alpha stuck at 0) and we surface + log the error so it can be diagnosed.
    """
    if not app.winfo_viewable():
        _safe_build(app, build_fn)
        return

    def out(p):
        app.attributes("-alpha", max(0.0, 1.0 - p))

    def swap():
        _safe_build(app, build_fn)

    tween(app, duration_ms, out, on_done=swap)


def _safe_build(app, build_fn):
    try:
        build_fn()
    except Exception as e:
        # Keep the window usable and record what went wrong.
        try:
            app.attributes("-alpha", 1.0)
        except Exception:
            pass
        _log_error(e)
        try:
            Toast.show("Screen error", str(e)[:220], "danger")
        except Exception:
            pass
    else:
        try:
            app.attributes("-alpha", 1.0)
        except Exception:
            pass


def _log_error(e):
    try:
        import traceback, os
        from utils import DATA_DIR
        path = os.path.join(DATA_DIR, "dpp_error.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n--- " + time.strftime("%Y-%m-%d %H:%M:%S") + " ---\n")
            f.write("".join(traceback.format_exception(type(e), e, e.__traceback__)))
    except Exception:
        pass

class AnimatedBackground(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#06090f", highlightthickness=0, borderwidth=0)
        self.particles = []
        self.blobs = []
        self._running = True
        self._init_entities()
        self.bind("<Configure>", self._resize)
        self._animate()

    def _init_entities(self):
        w = self.winfo_width() or 1100
        h = self.winfo_height() or 720
        palette = ["#d4af37", "#3b82f6", "#8b5cf6", "#22d3ee", "#ffffff", "#f472b6"]
        self.particles = [{
            "x": random.uniform(0, w), "y": random.uniform(0, h),
            "vx": random.uniform(-0.22, 0.22), "vy": random.uniform(-0.22, 0.22),
            "r": random.uniform(1.0, 3.2), "c": random.choice(palette),
        } for _ in range(60)]
        self.blobs = [{
            "x": random.uniform(0, w), "y": random.uniform(0, h),
            "vx": random.uniform(-0.15, 0.15), "vy": random.uniform(-0.15, 0.15),
            "r": random.uniform(170, 330),
            "c": random.choice(["#0e1830", "#161033", "#0c2230", "#102a2e"]),
        } for _ in range(3)]

    def _resize(self, e):
        w, h = e.width, e.height
        for p in self.particles:
            if p["x"] > w: p["x"] = random.uniform(0, w)
            if p["y"] > h: p["y"] = random.uniform(0, h)
        for b in self.blobs:
            if b["x"] > w: b["x"] = random.uniform(0, w)
            if b["y"] > h: b["y"] = random.uniform(0, h)

    def _animate(self):
        if not self._running:
            return
        self.delete("all")
        w = self.winfo_width(); h = self.winfo_height()
        for b in self.blobs:
            b["x"] += b["vx"]; b["y"] += b["vy"]
            if b["x"] < -b["r"]: b["x"] = w + b["r"]
            if b["x"] > w + b["r"]: b["x"] = -b["r"]
            if b["y"] < -b["r"]: b["y"] = h + b["r"]
            if b["y"] > h + b["r"]: b["y"] = -b["r"]
            self.create_oval(b["x"]-b["r"], b["y"]-b["r"], b["x"]+b["r"], b["y"]+b["r"], fill=b["c"], outline="")
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["x"] < -5: p["x"] = w + 5
            if p["x"] > w + 5: p["x"] = -5
            if p["y"] < -5: p["y"] = h + 5
            if p["y"] > h + 5: p["y"] = -5
            self.create_oval(p["x"]-p["r"], p["y"]-p["r"], p["x"]+p["r"], p["y"]+p["r"], fill=p["c"], outline="")
        self.after(33, self._animate)

    def stop(self):
        self._running = False


class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        colors = get_colors()
        kwargs.setdefault("fg_color", colors["card"])
        kwargs.setdefault("corner_radius", 18)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", colors["border"])
        super().__init__(master, **kwargs)
        self._base_border = colors["border"]
        self._accent = LUX_GOLD
        self._anim_id = None
        self._target = self._base_border
        self.bind("<Enter>", lambda e: self._animate_border(self._accent))
        self.bind("<Leave>", lambda e: self._animate_border(self._base_border))

    def _animate_border(self, target):
        if self._target == target and self._anim_id is None:
            return
        self._target = target
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
        try:
            start = _hex_to_rgb(self.cget("border_color"))
        except Exception:
            start = _hex_to_rgb(self._base_border)
        end = _hex_to_rgb(target)
        t0 = time.time(); dur = 200.0
        def tick():
            e = (time.time() - t0) * 1000.0
            p = min(1.0, e / dur); ep = _ease_out_cubic(p)
            r = round(start[0] + (end[0] - start[0]) * ep)
            g = round(start[1] + (end[1] - start[1]) * ep)
            b = round(start[2] + (end[2] - start[2]) * ep)
            self.configure(border_color=_rgb_to_hex(r, g, b))
            if p < 1:
                self._anim_id = self.after(_FRAME_MS, tick)
            else:
                self._anim_id = None
        self._anim_id = self.after(_FRAME_MS, tick)


def accent_button(master, text, command=None, primary=True, **kwargs):
    settings = load_settings()
    colors = get_colors()
    if primary:
        base = settings["accent"]; hover = shade(base, 16); press = shade(base, -26); text_color = "#ffffff"
    else:
        base = colors["card"]; hover = colors["card_hover"]; press = shade(colors["card"], -14); text_color = colors["text"]
    kwargs.setdefault("fg_color", base)
    kwargs.setdefault("hover_color", hover)
    kwargs.setdefault("text_color", text_color)
    kwargs.setdefault("corner_radius", 14)
    kwargs.setdefault("height", 42)
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", colors["border"])
    kwargs.setdefault("font", ctk.CTkFont(size=14, weight="bold"))
    btn = ctk.CTkButton(master, text=text, command=command, **kwargs)
    def enter(_e):
        tween(btn, 130, lambda p: btn.configure(border_color=_mix(colors["border"], LUX_GOLD, p)))
    def leave(_e):
        tween(btn, 130, lambda p: btn.configure(border_color=_mix(LUX_GOLD, colors["border"], p)))
    def press(_e):
        btn.configure(fg_color=press)
    def release(_e):
        btn.configure(fg_color=base)
    btn.bind("<Enter>", enter)
    btn.bind("<Leave>", leave)
    btn.bind("<ButtonPress-1>", press)
    btn.bind("<ButtonRelease-1>", release)
    return btn


class Toast:
    _root = None
    _stack = []

    @classmethod
    def set_root(cls, root):
        cls._root = root

    @classmethod
    def show(cls, title, message, kind="info", duration=3000):
        if cls._root is None:
            return
        colors = get_colors()
        win = ctk.CTkToplevel(cls._root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        frame = ctk.CTkFrame(win, corner_radius=12, fg_color=colors["card"], border_width=1, border_color=LUX_GOLD)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(frame, text=message, font=ctk.CTkFont(size=12), text_color=colors["muted"], wraplength=280).pack(anchor="w", padx=14, pady=(2, 10))
        cls._root.update_idletasks()
        rw = cls._root.winfo_width(); rx = cls._root.winfo_rootx(); ry = cls._root.winfo_rooty(); rh = cls._root.winfo_height()
        x = rx + rw - 340; y = ry + rh - 110 - len(cls._stack) * 95
        win.geometry(f"320x84+{x + 60}+{y}")
        cls._stack.append(win)
        def slide(p):
            cx = int((x + 60) + (x - (x + 60)) * p)
            win.geometry(f"320x84+{cx}+{y}")
        tween(win, 260, slide)
        win.after(duration, lambda: cls._dismiss(win))

    @classmethod
    def _dismiss(cls, win):
        try:
            cls._stack.remove(win)
        except ValueError:
            pass
        try:
            win.destroy()
        except Exception:
            pass


def fig_to_image(fig, size=(820, 260)):
    import io
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    img = Image.open(buf)
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


def ensure_logo():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    path = os.path.join(ASSETS_DIR, "logo.png")
    if not os.path.exists(path):
        try:
            from PIL import Image, ImageDraw
            size = 256
            img = Image.new("RGBA", (size, size), (212, 175, 55, 255))
            d = ImageDraw.Draw(img)
            d.ellipse([40, 40, 216, 216], fill=(255, 255, 255, 255))
            d.ellipse([58, 58, 198, 198], fill=(212, 175, 55, 255))
            d.line([128, 128, 128, 78], fill=(255, 255, 255, 255), width=12)
            d.line([128, 128, 172, 128], fill=(255, 255, 255, 255), width=12)
            img.save(path)
        except Exception:
            pass
    return path


def load_logo_image(size=(64, 64)):
    from PIL import Image
    path = ensure_logo()
    pil = Image.open(path)
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=size)


def load_logo_tk():
    from PIL import Image, ImageTk
    path = ensure_logo()
    return ImageTk.PhotoImage(Image.open(path))