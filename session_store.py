from contextlib import closing, contextmanager
from pathlib import Path
import sqlite3
from threading import RLock

from models import GameSession


class SessionStore:
    """Server-owned case records, addressed by an opaque browser resume token."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._locks = tuple(RLock() for _ in range(64))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, state TEXT NOT NULL)")

    def load(self, case_id: str) -> GameSession | None:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT state FROM cases WHERE id = ?", (case_id,)).fetchone()
        return GameSession.model_validate_json(row[0]) if row else None

    def save(self, session: GameSession) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "INSERT INTO cases (id, state) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET state = excluded.state",
                (session.id, session.model_dump_json()),
            )

    @contextmanager
    def edit(self, case_id: str, create_case):
        # Serialize actions for the same case across browser tabs on this server.
        with self._locks[hash(case_id) % len(self._locks)]:
            session = self.load(case_id) if case_id else None
            if session is None:
                session = create_case()
                self.save(session)
            before = session.model_dump_json()
            try:
                yield session
            finally:
                if session.model_dump_json() != before:
                    self.save(session)
