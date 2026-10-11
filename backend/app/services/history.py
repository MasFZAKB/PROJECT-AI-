"""Riwayat analisis disimpan di SQLite (tanpa dependensi tambahan)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .. import config


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                width INTEGER, height INTEGER,
                total INTEGER NOT NULL,
                counts TEXT NOT NULL,
                detections TEXT NOT NULL,
                original_file TEXT,
                annotated_file TEXT,
                model_mode TEXT,
                inference_ms REAL
            )
            """
        )


def add(**row) -> int:
    row["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row["counts"] = json.dumps(row["counts"])
    row["detections"] = json.dumps(row["detections"])
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    with _conn() as con:
        cur = con.execute(f"INSERT INTO analyses ({cols}) VALUES ({marks})", list(row.values()))
        return cur.lastrowid


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["counts"] = json.loads(d["counts"])
    d["detections"] = json.loads(d["detections"])
    return d


def list_(limit: int, offset: int) -> tuple[list[dict], int]:
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        rows = con.execute(
            "SELECT * FROM analyses ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
    return [_row(r) for r in rows], total


def get(analysis_id: int) -> dict | None:
    with _conn() as con:
        r = con.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    return _row(r) if r else None


def delete(analysis_id: int) -> dict | None:
    item = get(analysis_id)
    if item:
        with _conn() as con:
            con.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    return item


def stats() -> dict:
    with _conn() as con:
        r = con.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(total),0) objs FROM analyses"
        ).fetchone()
    return {"photos": r["n"], "objects": r["objs"]}
