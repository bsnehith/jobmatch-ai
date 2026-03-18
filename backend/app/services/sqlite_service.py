import json
import sqlite3
from typing import Any, Dict, List, Optional


class SQLiteService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    score INTEGER NOT NULL,
                    strengths TEXT NOT NULL,
                    gaps TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    web_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    @staticmethod
    def _to_utc_iso(timestamp: Optional[str]) -> Optional[str]:
        if not timestamp:
            return timestamp
        # SQLite CURRENT_TIMESTAMP is usually "YYYY-MM-DD HH:MM:SS" in UTC.
        normalized = str(timestamp).strip().replace(" ", "T")
        if normalized.endswith("Z"):
            return normalized
        return f"{normalized}Z"

    @staticmethod
    def _deserialize_row(row: sqlite3.Row) -> Dict[str, Any]:
        payload = dict(row)
        payload["strengths"] = json.loads(payload.get("strengths", "[]"))
        payload["gaps"] = json.loads(payload.get("gaps", "[]"))
        payload["created_at"] = SQLiteService._to_utc_iso(payload.get("created_at"))
        payload["updated_at"] = SQLiteService._to_utc_iso(payload.get("updated_at"))
        return payload

    def upsert_candidate(
        self,
        *,
        name: str,
        score: int,
        strengths: List[str],
        gaps: List[str],
        recommendation: str,
        reason: str,
        web_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO candidates
                    (name, score, strengths, gaps, recommendation, reason, web_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    score=excluded.score,
                    strengths=excluded.strengths,
                    gaps=excluded.gaps,
                    recommendation=excluded.recommendation,
                    reason=excluded.reason,
                    web_url=excluded.web_url,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    name,
                    int(score),
                    json.dumps(strengths),
                    json.dumps(gaps),
                    recommendation,
                    reason,
                    web_url,
                ),
            )
            conn.commit()
        return self.get_candidate(name=name)

    def get_candidate(self, *, name: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE LOWER(name) = LOWER(?)",
                (name,),
            ).fetchone()
        return self._deserialize_row(row) if row else {}

    def list_candidates(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates ORDER BY updated_at DESC, created_at DESC"
            ).fetchall()
        return [self._deserialize_row(row) for row in rows]

    def top_candidates(self, *, limit: int = 3) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates ORDER BY score DESC, updated_at DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [self._deserialize_row(row) for row in rows]

    def delete_candidate(self, *, name: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM candidates WHERE LOWER(name) = LOWER(?)",
                (name,),
            )
            conn.commit()
        return cursor.rowcount > 0
