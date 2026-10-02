"""
database.py - simple SQLite storage for N3thunt3r enquiries.

SQLite is built into Python, so nothing extra needs to be installed.
To move to MySQL/PostgreSQL later, only this file needs to change.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

# By default the database file sits next to this script.
# You can override it with DB_PATH in the .env file.
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "n3thunt3r.db"
)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(os.getenv("DB_PATH") or DEFAULT_DB_PATH)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    """Create the table the first time the bot runs."""
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS enquiries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                username     TEXT,
                name         TEXT NOT NULL,
                need         TEXT NOT NULL,
                description  TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL,
                cancelled_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_enquiries_user ON enquiries(user_id)"
        )


def add_enquiry(
    user_id: int, username: str | None, name: str, need: str, description: str
) -> int:
    """Save a new enquiry and return its number."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO enquiries
                (user_id, username, name, need, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
            """,
            (user_id, username, name, need, description, _now()),
        )
        return cursor.lastrowid


def get_user_enquiries(user_id: int) -> list[dict]:
    """All enquiries (active and cancelled) for one user, newest first."""
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM enquiries WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_enquiry(user_id: int, enquiry_id: int) -> dict | None:
    """One enquiry, but only if it belongs to this user."""
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM enquiries WHERE id = ? AND user_id = ?",
            (enquiry_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def count_active(user_id: int) -> int:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM enquiries "
            "WHERE user_id = ? AND status = 'active'",
            (user_id,),
        ).fetchone()
    return row["total"]


def cancel_enquiry(user_id: int, enquiry_id: int) -> bool:
    """Cancel one active enquiry. Returns True if something was cancelled."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute(
            """
            UPDATE enquiries SET status = 'cancelled', cancelled_at = ?
            WHERE id = ? AND user_id = ? AND status = 'active'
            """,
            (_now(), enquiry_id, user_id),
        )
        return cursor.rowcount > 0


def cancel_all(user_id: int) -> list[int]:
    """Cancel every active enquiry for a user. Returns the cancelled numbers."""
    with closing(_connect()) as conn, conn:
        rows = conn.execute(
            "SELECT id FROM enquiries WHERE user_id = ? AND status = 'active' "
            "ORDER BY id",
            (user_id,),
        ).fetchall()
        ids = [row["id"] for row in rows]
        if ids:
            conn.execute(
                """
                UPDATE enquiries SET status = 'cancelled', cancelled_at = ?
                WHERE user_id = ? AND status = 'active'
                """,
                (_now(), user_id),
            )
    return ids