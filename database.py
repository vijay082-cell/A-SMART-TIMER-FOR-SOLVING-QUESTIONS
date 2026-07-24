"""
database.py
-----------
SQLite backed persistence for DPP Timer AI.

Stores:
  * dpp      -> one row per completed (or saved) DPP session
  * question -> one row per question inside a DPP (time spent, skipped, ...)

Thread safety: a single connection with check_same_thread=False plus a lock
so the GUI thread and any worker threads can read/write safely.
"""

import sqlite3
import threading
from datetime import datetime


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    # ------------------------------------------------------------------ schema
    def create_tables(self):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dpp (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    date              TEXT,
                    subject           TEXT,
                    chapter           TEXT,
                    num_questions     INTEGER,
                    target_time       REAL,
                    actual_time       REAL,
                    avg_time          REAL,
                    efficiency        REAL,
                    completion        REAL,
                    skipped           INTEGER,
                    above_recommended INTEGER,
                    source            TEXT,
                    pdf_name          TEXT,
                    pages             INTEGER
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS question (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    dpp_id           INTEGER,
                    question_number  INTEGER,
                    time_spent       REAL,
                    skipped          INTEGER,
                    recommended_time REAL,
                    FOREIGN KEY(dpp_id) REFERENCES dpp(id)
                )
                """
            )
            self.conn.commit()

    # ------------------------------------------------------------------ writes
    def add_dpp(self, **kwargs):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO dpp
                (date, subject, chapter, num_questions, target_time,
                 actual_time, avg_time, efficiency, completion, skipped,
                 above_recommended, source, pdf_name, pages)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    kwargs.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    kwargs.get("subject", ""),
                    kwargs.get("chapter", ""),
                    kwargs.get("num_questions", 0),
                    kwargs.get("target_time", 0),
                    kwargs.get("actual_time", 0),
                    kwargs.get("avg_time", 0),
                    kwargs.get("efficiency", 0),
                    kwargs.get("completion", 0),
                    kwargs.get("skipped", 0),
                    kwargs.get("above_recommended", 0),
                    kwargs.get("source", "manual"),
                    kwargs.get("pdf_name", ""),
                    kwargs.get("pages", 0),
                ),
            )
            self.conn.commit()
            return cur.lastrowid

    def update_dpp(self, dpp_id, **kwargs):
        with self._lock:
            cur = self.conn.cursor()
            fields = []
            values = []
            for k, v in kwargs.items():
                fields.append(f"{k}=?")
                values.append(v)
            values.append(dpp_id)
            cur.execute(f"UPDATE dpp SET {','.join(fields)} WHERE id=?", values)
            self.conn.commit()

    def add_question(self, dpp_id, question_number, time_spent, skipped, recommended_time):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO question
                (dpp_id, question_number, time_spent, skipped, recommended_time)
                VALUES (?,?,?,?,?)
                """,
                (dpp_id, question_number, time_spent, int(skipped), recommended_time),
            )
            self.conn.commit()

    # ------------------------------------------------------------------- reads
    def get_all_dpps(self, limit=500):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM dpp ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    def get_dpp(self, dpp_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM dpp WHERE id=?", (dpp_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_questions(self, dpp_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT * FROM question WHERE dpp_id=? ORDER BY question_number",
                (dpp_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def delete_dpp(self, dpp_id):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM question WHERE dpp_id=?", (dpp_id,))
            cur.execute("DELETE FROM dpp WHERE id=?", (dpp_id,))
            self.conn.commit()

    def search_dpps(self, query):
        with self._lock:
            cur = self.conn.cursor()
            like = f"%{query}%"
            cur.execute(
                """
                SELECT * FROM dpp
                WHERE subject LIKE ? OR chapter LIKE ? OR date LIKE ?
                ORDER BY id DESC
                """,
                (like, like, like),
            )
            return [dict(row) for row in cur.fetchall()]

    # --------------------------------------------------------------- analytics
    def get_study_series(self):
        """
        Aggregate actual_time into daily / weekly / monthly totals.
        Returns dict with keys 'daily','weekly','monthly' -> list of (key, seconds).
        """
        dpps = self.get_all_dpps(limit=100000)
        daily, weekly, monthly = {}, {}, {}
        for d in dpps:
            try:
                dt = datetime.strptime(d["date"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            day_key = dt.strftime("%Y-%m-%d")
            week_key = dt.strftime("%Y-W%W")
            month_key = dt.strftime("%Y-%m")
            daily[day_key] = daily.get(day_key, 0) + d["actual_time"]
            weekly[week_key] = weekly.get(week_key, 0) + d["actual_time"]
            monthly[month_key] = monthly.get(month_key, 0) + d["actual_time"]

        daily_sorted = sorted(daily.items())
        weekly_sorted = sorted(weekly.items())
        monthly_sorted = sorted(monthly.items())
        return {
            "daily": daily_sorted[-14:],
            "weekly": weekly_sorted[-8:],
            "monthly": monthly_sorted[-12:],
        }

    def get_subject_stats(self):
        """
        Per-subject aggregates: sessions, avg seconds/question (speed),
        avg efficiency.
        """
        dpps = self.get_all_dpps(limit=100000)
        agg = {}
        for d in dpps:
            s = d["subject"] or "Unknown"
            a = agg.setdefault(s, {"count": 0, "questions": 0, "time": 0.0, "eff": 0.0})
            a["count"] += 1
            a["questions"] += d["num_questions"]
            a["time"] += d["actual_time"]
            a["eff"] += d["efficiency"]
        result = {}
        for s, a in agg.items():
            result[s] = {
                "sessions": a["count"],
                "avg_speed": (a["time"] / a["questions"]) if a["questions"] else 0.0,
                "avg_efficiency": (a["eff"] / a["count"]) if a["count"] else 0.0,
            }
        return result

    def get_best_worst(self):
        """Return (best_dpp, worst_dpp) by efficiency, or (None, None)."""
        dpps = self.get_all_dpps(limit=100000)
        if not dpps:
            return None, None
        best = max(dpps, key=lambda d: d["efficiency"])
        worst = min(dpps, key=lambda d: d["efficiency"])
        return best, worst

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
