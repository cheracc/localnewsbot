from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "database.sqlite"

# DatabaseManager handles SQLite operations for tracking posted articles. It's a very simple sqlite database that just 
# records article URLs that have been posted already and the time posted.
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS excluded (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_url TEXT NOT NULL UNIQUE,
                    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def is_excluded(self, article_url: str) -> bool:
        """Check if an article URL exists in the excluded table."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM excluded WHERE article_url = ?",
                (article_url,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def record_excluded_article(self, article_url: str) -> None:
        """Add an article URL to the excluded table."""
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO excluded (article_url) VALUES (?)",
                (article_url,)
            )
            conn.commit()
        finally:
            conn.close()
