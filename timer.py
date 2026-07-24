"""
timer.py
--------
A small, self-contained Timer built on a background thread.

Two modes:
  * "stopwatch"  -> counts elapsed time upward (used for per-question timing)
  * "countdown"  -> counts down from `duration`; auto-stops at zero
                    (used for the overall DPP target time)

The optional on_tick(elapsed_seconds) callback fires roughly every `interval`
seconds. To stay Tkinter-thread-safe (especially on Windows), the callback is
marshalled onto the main thread via `master.after` when a `master` is given.
"""

import threading
import time


class Timer:
    def __init__(self, duration=0.0, mode="stopwatch", on_tick=None, interval=0.1, master=None):
        self.duration = float(duration)
        self.mode = mode                # "stopwatch" | "countdown"
        self.on_tick = on_tick
        self.interval = interval
        self.master = master            # a Tk widget; used to marshal on_tick
                                        # onto the MAIN thread (Tk is not
                                        # thread-safe, especially on Windows)

        self._elapsed = 0.0
        self._running = False
        self._paused = False
        self._stop = False
        self._thread = None
        self._lock = threading.Lock()

    # ----------------------------------------------------------------- control
    def _emit(self, elapsed):
        """Call on_tick on the main thread if a master widget was given.

        Touching Tkinter from a background thread corrupts the GUI on Windows,
        so we schedule the callback via the main thread's event loop instead.
        """
        if self.master is not None:
            try:
                self.master.after(0, self._call, elapsed)
                return
            except Exception:
                pass
        # Fallback: call directly (may run off the main thread).
        self._call(elapsed)

    def _call(self, elapsed):
        if self.on_tick:
            self.on_tick(elapsed)

    def start(self):
        """Begin ticking (no-op if already running)."""
        if self._running:
            return
        self._running = True
        self._stop = False
        self._paused = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        last = time.time()
        while self._running and not self._stop:
            if not self._paused:
                now = time.time()
                dt = now - last
                last = now
                with self._lock:
                    self._elapsed += dt
                if self.on_tick:
                    try:
                        self._emit(self._elapsed)
                    except Exception:
                        pass
                # countdown auto-stop
                if self.mode == "countdown" and self._elapsed >= self.duration:
                    with self._lock:
                        self._elapsed = self.duration
                    if self.on_tick:
                        try:
                            self._emit(self._elapsed)
                        except Exception:
                            pass
                    self._running = False
                    break
            else:
                # keep 'last' fresh while paused so resume doesn't jump
                last = time.time()
            time.sleep(self.interval)

    def pause(self):
        with self._lock:
            self._paused = True

    def resume(self):
        with self._lock:
            self._paused = False

    def stop(self):
        """Stop ticking; elapsed value is preserved."""
        self._running = False
        self._stop = True

    def reset(self):
        with self._lock:
            self._elapsed = 0.0

    # ------------------------------------------------------------------ queries
    def is_running(self):
        return self._running

    def is_paused(self):
        return self._paused

    def get_elapsed(self):
        with self._lock:
            return self._elapsed

    def get_remaining(self):
        with self._lock:
            return max(0.0, self.duration - self._elapsed)