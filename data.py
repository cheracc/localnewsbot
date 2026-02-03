from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "database.sqlite"

class DatabaseManager:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        """Create the SQLite database and posts table if they don't exist."""
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_url TEXT NOT NULL UNIQUE,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new sqlite3 connection to the database."""
        return sqlite3.connect(self.path)
    def has_posted_article(self, article_url: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM posts WHERE article_url = ?",
                (article_url,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def record_posted_article(self, article_url: str) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO posts (article_url) VALUES (?)",
                (article_url,)
            )
            conn.commit()
        finally:
            conn.close()
