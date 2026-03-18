"""
database.py — Restaurant Intelligence Platform
================================================
Dual-mode persistence layer: SQLite (local dev) or PostgreSQL (production).

Set DATABASE_URL=postgresql://user:pass@host:5432/db in .env to activate PostgreSQL.
Without DATABASE_URL, SQLite is used (file: app/output/restaurant_intelligence.db).

Tables:
  call_notes      — call/visit log per restaurant (replaces JSON flat-files)
  score_history   — weekly score snapshots per restaurant
  chat_sessions   — persisted chat messages per restaurant

On first run, existing JSON call notes are auto-migrated into the DB.
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent / "app" / "output" / "restaurant_intelligence.db"

CALL_NOTES_DIR = Path(__file__).resolve().parent / "scripts" / "data" / "call_notes"


# ─────────────────────────────────────────────
# BACKEND DETECTION + HELPERS
# ─────────────────────────────────────────────

def _is_postgres() -> bool:
    return os.environ.get("DATABASE_URL", "").startswith("postgresql://")


def _sql(query: str) -> str:
    if _is_postgres():
        return query.replace("?", "%s")
    return query


# ─────────────────────────────────────────────
# POSTGRESQL COMPATIBILITY WRAPPER
# ─────────────────────────────────────────────

class _PgConn:
    def __init__(self, con, cur):
        self._con = con
        self._cur = cur

    def execute(self, sql: str, params=None):
        self._cur.execute(sql, params or ())
        return self._cur

    def executemany(self, sql: str, params_list):
        self._cur.executemany(sql, params_list)
        return self._cur

    def commit(self):
        self._con.commit()

    def rollback(self):
        self._con.rollback()

    def close(self):
        self._con.close()


@contextmanager
def _conn():
    if _is_postgres():
        import psycopg2
        import psycopg2.extras
        raw = psycopg2.connect(os.environ["DATABASE_URL"])
        raw.autocommit = False
        cur = raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        con = _PgConn(raw, cur)
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        raw.row_factory = sqlite3.Row
        raw.execute("PRAGMA journal_mode=WAL")
        try:
            yield raw
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    return dict(zip(row.keys(), tuple(row)))


# ─────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS call_notes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id       TEXT NOT NULL,
    call_date           TEXT,
    rep_name            TEXT,
    contact_name        TEXT,
    interest_level      INTEGER,
    main_objection      TEXT,
    budget_range        TEXT,
    confidence          INTEGER,
    timeline            TEXT,
    products_discussed  TEXT,
    visit_outcome       TEXT,
    notes               TEXT,
    image_data          TEXT,
    saved_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS score_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id   TEXT NOT NULL,
    scored_at       TEXT NOT NULL,
    composite_score REAL,
    reputation      REAL,
    responsiveness  REAL,
    digital         REAL,
    visibility      REAL,
    intelligence    REAL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id   TEXT NOT NULL UNIQUE,
    city            TEXT,
    messages_json   TEXT NOT NULL DEFAULT '[]',
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_call_notes_rid ON call_notes (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_score_history_rid ON score_history (restaurant_id);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS call_notes (
    id                  SERIAL PRIMARY KEY,
    restaurant_id       TEXT NOT NULL,
    call_date           TEXT,
    rep_name            TEXT,
    contact_name        TEXT,
    interest_level      INTEGER,
    main_objection      TEXT,
    budget_range        TEXT,
    confidence          INTEGER,
    timeline            TEXT,
    products_discussed  TEXT,
    visit_outcome       TEXT,
    notes               TEXT,
    image_data          TEXT,
    saved_at            TEXT DEFAULT (NOW()::text)
);

CREATE TABLE IF NOT EXISTS score_history (
    id              SERIAL PRIMARY KEY,
    restaurant_id   TEXT NOT NULL,
    scored_at       TEXT NOT NULL,
    composite_score REAL,
    reputation      REAL,
    responsiveness  REAL,
    digital         REAL,
    visibility      REAL,
    intelligence    REAL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id              SERIAL PRIMARY KEY,
    restaurant_id   TEXT NOT NULL UNIQUE,
    city            TEXT,
    messages_json   TEXT NOT NULL DEFAULT '[]',
    updated_at      TEXT DEFAULT (NOW()::text)
);

CREATE INDEX IF NOT EXISTS idx_call_notes_rid ON call_notes (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_score_history_rid ON score_history (restaurant_id);
"""


def init_db() -> None:
    """Create tables (idempotent). Migrates existing JSON call notes on first run."""
    schema = _SCHEMA_PG if _is_postgres() else _SCHEMA_SQLITE
    with _conn() as con:
        if _is_postgres():
            for stmt in [s.strip() for s in schema.split(";") if s.strip()]:
                con.execute(stmt)
        else:
            con.executescript(schema)  # type: ignore[attr-defined]
    _migrate_json_notes_once()


# ─────────────────────────────────────────────
# JSON → DB MIGRATION (one-time, idempotent)
# ─────────────────────────────────────────────

def _migrate_json_notes_once() -> None:
    """
    On first startup, copy any existing JSON call notes into the DB.
    Skips restaurants that already have DB records.
    """
    if not CALL_NOTES_DIR.exists():
        return
    for json_path in CALL_NOTES_DIR.glob("*.json"):
        restaurant_id = json_path.stem
        try:
            # Skip if already migrated
            with _conn() as con:
                existing = con.execute(
                    _sql("SELECT COUNT(*) as cnt FROM call_notes WHERE restaurant_id = ?"),
                    (restaurant_id,),
                ).fetchone()
                cnt = _row_to_dict(existing).get("cnt", 0)
                if cnt and int(cnt) > 0:
                    continue
            # Load JSON and insert each call
            data = json.loads(json_path.read_text(encoding="utf-8"))
            calls = data.get("calls", [])
            for call in calls:
                _save_call_note_raw(restaurant_id, call)
            if calls:
                logger.info("Migrated %d call notes from JSON for %s", len(calls), restaurant_id)
        except Exception as e:
            logger.warning("JSON migration failed for %s: %s", restaurant_id, e)


# ─────────────────────────────────────────────
# CALL NOTES
# ─────────────────────────────────────────────

def _products_to_str(products) -> str:
    if isinstance(products, list):
        return json.dumps(products, ensure_ascii=False)
    return str(products or "")


def _products_from_str(s) -> list:
    if not s:
        return []
    try:
        val = json.loads(s)
        return val if isinstance(val, list) else [str(val)]
    except Exception:
        return [s] if s else []


def _save_call_note_raw(restaurant_id: str, call: dict) -> int:
    with _conn() as con:
        cur = con.execute(
            _sql("""INSERT INTO call_notes
                   (restaurant_id, call_date, rep_name, contact_name, interest_level,
                    main_objection, budget_range, confidence, timeline,
                    products_discussed, visit_outcome, notes, image_data, saved_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""),
            (
                restaurant_id,
                call.get("call_date", ""),
                call.get("rep_name", ""),
                call.get("contact_name", ""),
                call.get("interest_level"),
                call.get("main_objection", ""),
                call.get("budget_range", ""),
                call.get("confidence"),
                call.get("timeline", ""),
                _products_to_str(call.get("products_discussed", [])),
                call.get("visit_outcome", ""),
                call.get("notes", ""),
                call.get("image_data", ""),
                call.get("saved_at", datetime.now().isoformat(timespec="seconds")),
            ),
        )
        return cur.lastrowid


def get_call_notes(restaurant_id: str) -> list[dict]:
    """Return all call notes for a restaurant, oldest first."""
    try:
        with _conn() as con:
            rows = con.execute(
                _sql("SELECT * FROM call_notes WHERE restaurant_id = ? ORDER BY saved_at ASC"),
                (restaurant_id,),
            ).fetchall()
        result = []
        for row in rows:
            d = _row_to_dict(row)
            d["products_discussed"] = _products_from_str(d.get("products_discussed", ""))
            result.append(d)
        return result
    except Exception as e:
        logger.warning("get_call_notes failed for %s: %s", restaurant_id, e)
        return []


def save_call_note(restaurant_id: str, call: dict) -> int:
    """Save a single call note; returns the new row id."""
    return _save_call_note_raw(restaurant_id, call)


def delete_call_note_by_index(restaurant_id: str, index: int) -> bool:
    """Delete a call note by its position in the ordered list."""
    notes = get_call_notes(restaurant_id)
    if index < 0 or index >= len(notes):
        return False
    row_id = notes[index].get("id")
    if not row_id:
        return False
    try:
        with _conn() as con:
            con.execute(_sql("DELETE FROM call_notes WHERE id = ?"), (row_id,))
        return True
    except Exception as e:
        logger.error("delete_call_note failed: %s", e)
        return False


# ─────────────────────────────────────────────
# SCORE HISTORY
# ─────────────────────────────────────────────

def save_score_history(restaurant_id: str, scores: dict) -> None:
    """Record a score snapshot. scores = {composite, reputation, responsiveness, digital, visibility, intelligence}."""
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as con:
        con.execute(
            _sql("""INSERT INTO score_history
                   (restaurant_id, scored_at, composite_score, reputation, responsiveness,
                    digital, visibility, intelligence)
                   VALUES (?,?,?,?,?,?,?,?)"""),
            (
                restaurant_id,
                now,
                scores.get("composite", 0),
                scores.get("reputation", 0),
                scores.get("responsiveness", 0),
                scores.get("digital", 0),
                scores.get("visibility", 0),
                scores.get("intelligence", 0),
            ),
        )


def get_score_history(restaurant_id: str, limit: int = 8) -> list[dict]:
    """Return recent score snapshots, oldest first."""
    try:
        with _conn() as con:
            rows = con.execute(
                _sql("""SELECT scored_at, composite_score, reputation, responsiveness,
                               digital, visibility, intelligence
                        FROM score_history
                        WHERE restaurant_id = ?
                        ORDER BY scored_at DESC
                        LIMIT ?"""),
                (restaurant_id, limit),
            ).fetchall()
        return list(reversed([_row_to_dict(r) for r in rows]))
    except Exception as e:
        logger.warning("get_score_history failed: %s", e)
        return []


# ─────────────────────────────────────────────
# CHAT SESSION PERSISTENCE
# ─────────────────────────────────────────────

def save_chat_session(restaurant_id: str, city: str, messages: list) -> None:
    """Persist the full chat message list for a restaurant."""
    now = datetime.now().isoformat(timespec="seconds")
    messages_json = json.dumps(messages, ensure_ascii=False)
    with _conn() as con:
        con.execute(
            _sql("""INSERT INTO chat_sessions (restaurant_id, city, messages_json, updated_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(restaurant_id) DO UPDATE SET
                       messages_json = excluded.messages_json,
                       city = excluded.city,
                       updated_at = excluded.updated_at"""),
            (restaurant_id, city or "", messages_json, now),
        )


def load_chat_session(restaurant_id: str) -> list:
    """Load persisted chat messages; returns [] if none."""
    try:
        with _conn() as con:
            row = con.execute(
                _sql("SELECT messages_json FROM chat_sessions WHERE restaurant_id = ?"),
                (restaurant_id,),
            ).fetchone()
        if row:
            d = _row_to_dict(row)
            return json.loads(d.get("messages_json", "[]"))
    except Exception as e:
        logger.warning("load_chat_session failed: %s", e)
    return []


def clear_chat_session(restaurant_id: str) -> None:
    """Clear persisted chat for a restaurant."""
    try:
        with _conn() as con:
            con.execute(
                _sql("DELETE FROM chat_sessions WHERE restaurant_id = ?"),
                (restaurant_id,),
            )
    except Exception as e:
        logger.warning("clear_chat_session failed: %s", e)
