import hashlib
import os
import sqlite3
from pathlib import Path


DEFAULT_USERS = {
    "admin": "admin123",
    "alice": "redes2026",
    "bruno": "segredo",
}


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return salt.hex(), digest.hex()


def init_database(db_path: Path, reset: bool = False) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if reset and db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                from_user TEXT NOT NULL,
                to_user TEXT,
                message TEXT NOT NULL,
                is_private INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        for username, password in DEFAULT_USERS.items():
            salt, password_hash = hash_password(password)
            conn.execute(
                """
                INSERT OR IGNORE INTO users (username, salt, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, salt, password_hash),
            )
        conn.commit()


def verify_login(db_path: Path, username: str, password: str) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None:
        return False

    salt_hex, expected_hash = row
    salt = bytes.fromhex(salt_hex)
    _, candidate_hash = hash_password(password, salt)
    return candidate_hash == expected_hash


def list_users(db_path: Path) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
    return [row[0] for row in rows]


def save_message(db_path: Path, from_user: str, message: str, to_user: str | None = None) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO messages (from_user, to_user, message, is_private)
            VALUES (?, ?, ?, ?)
            """,
            (from_user, to_user, message, 1 if to_user else 0),
        )
        conn.commit()


def last_messages(db_path: Path, limit: int = 10) -> list[tuple[str, str, str | None, str, int]]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT timestamp, from_user, to_user, message, is_private
            FROM messages
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return list(reversed(rows))
