"""
---
role: 数据存储
depends: []
exports:
  - Storage
status: IMPLEMENTED
functions:
  - Storage.save_alert(symbol: str, message: str, level: str = "INFO", created_at: str | None = None) -> int
  - Storage.save_symbol_state(symbol: str, state: str, bought_at: str | None = None, extra: str | None = None) -> None
  - Storage.load_symbol_state(symbol: str) -> dict | None
---
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Lock


class Storage:
    def close(self) -> None:
        """Compatibility API for explicit cleanup; no-op for per-operation connections."""
        return

    def __init__(self, db_path: str = ".data/monitor.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path), check_same_thread=False)

    def _init_db(self) -> None:
        with self._lock:
            with closing(self._connect()) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS symbol_state (
                        symbol TEXT PRIMARY KEY,
                        state TEXT NOT NULL,
                        bought_at TEXT,
                        extra TEXT,
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.commit()

    def save_alert(
        self,
        symbol: str,
        message: str,
        level: str = "INFO",
        created_at: str | None = None,
    ) -> int:
        with self._lock:
            with closing(self._connect()) as conn:
                if created_at is None:
                    cur = conn.execute(
                        "INSERT INTO alerts(symbol, level, message) VALUES(?, ?, ?)",
                        (symbol, level, message),
                    )
                else:
                    cur = conn.execute(
                        "INSERT INTO alerts(symbol, level, message, created_at) VALUES(?, ?, ?, ?)",
                        (symbol, level, message, created_at),
                    )
                conn.commit()
                return int(cur.lastrowid)

    def save_symbol_state(
        self,
        symbol: str,
        state: str,
        bought_at: str | None = None,
        extra: str | None = None,
    ) -> None:
        with self._lock:
            with closing(self._connect()) as conn:
                conn.execute(
                    """
                    INSERT INTO symbol_state(symbol, state, bought_at, extra, updated_at)
                    VALUES(?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(symbol) DO UPDATE SET
                        state = excluded.state,
                        bought_at = excluded.bought_at,
                        extra = excluded.extra,
                        updated_at = datetime('now')
                    """,
                    (symbol, state, bought_at, extra),
                )
                conn.commit()

    def load_symbol_state(self, symbol: str) -> dict | None:
        with self._lock:
            with closing(self._connect()) as conn:
                cur = conn.execute(
                    """
                    SELECT symbol, state, bought_at, extra, updated_at
                    FROM symbol_state
                    WHERE symbol = ?
                    """,
                    (symbol,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return {
            "symbol": row[0],
            "state": row[1],
            "bought_at": row[2],
            "extra": row[3],
            "updated_at": row[4],
        }
