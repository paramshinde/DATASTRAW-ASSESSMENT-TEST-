from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Iterator


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(DATA_DIR / "support_crm.db")))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ticket_code(ticket_id: int) -> str:
    return f"TKT-{ticket_id:04d}"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE
            );
            """
        )


def seed_demo_data() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()["count"]
        if count:
            return

        examples = [
            (
                "Aanya Patel",
                "aanya@example.com",
                "Unable to reset password",
                "Customer gets a reset link, but the temporary password expires before login completes.",
                "Open",
            ),
            (
                "Jordan Lee",
                "jordan@example.com",
                "Invoice shows duplicate charge",
                "The June invoice includes a duplicate payment line for the same order.",
                "In Progress",
            ),
            (
                "Maya Singh",
                "maya@example.com",
                "Shipping address needs correction",
                "The shipping address was entered incorrectly after checkout and needs urgent review.",
                "Closed",
            ),
        ]

        for customer_name, customer_email, subject, description, status in examples:
            now = utc_now()
            cursor = conn.execute(
                """
                INSERT INTO tickets (
                    ticket_id, customer_name, customer_email, subject, description, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("", customer_name, customer_email, subject, description, status, now, now),
            )
            generated_id = cursor.lastrowid
            generated_ticket_id = ticket_code(generated_id)
            conn.execute(
                "UPDATE tickets SET ticket_id = ? WHERE id = ?",
                (generated_ticket_id, generated_id),
            )

        conn.execute(
            "INSERT INTO notes (ticket_id, note_text, created_at) VALUES (?, ?, ?)",
            ("TKT-0002", "Asked billing to verify the second payment capture.", utc_now()),
        )
        conn.execute(
            "INSERT INTO notes (ticket_id, note_text, created_at) VALUES (?, ?, ?)",
            ("TKT-0003", "Customer confirmed the address is now correct in the CRM.", utc_now()),
        )


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
