import sqlite3
import re
from pathlib import Path

# Mock config
class Settings:
    DATABASE_URL = "sqlite:///./app.db"

settings = Settings()

DB_PATH = Path("app.db")
IS_POSTGRES = settings.DATABASE_URL.startswith("postgres")

_pg_pool = None

if IS_POSTGRES:
    import psycopg2
    from psycopg2.pool import ThreadedConnectionPool
    from psycopg2.extras import DictCursor

def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = ThreadedConnectionPool(1, 20, settings.DATABASE_URL)
    return _pg_pool

class PGCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
        
    def _translate_sql(self, sql):
        # SQLite's TIMESTAMP DEFAULT CURRENT_TIMESTAMP is fine
        # Translate INTEGER PRIMARY KEY AUTOINCREMENT
        if "INTEGER PRIMARY KEY AUTOINCREMENT" in sql:
            sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            
        if "INSERT OR IGNORE INTO" in sql:
            sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
            sql = sql.rstrip(";") + " ON CONFLICT DO NOTHING"
            
        sql = sql.replace("?", "%s")
        return sql
        
    def execute(self, sql, params=()):
        pg_sql = self._translate_sql(sql)
        print("Executing:", pg_sql)
        # Mock execute for testing
        return self
        
    def executemany(self, sql, params_seq):
        pg_sql = self._translate_sql(sql)
        print("Executing many:", pg_sql)
        return self
        
    def fetchone(self):
        return None
        
    def fetchall(self):
        return []
        
    def close(self):
        pass

class PGConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def cursor(self):
        return PGCursorWrapper(None)
        
    def commit(self):
        pass
        
    def rollback(self):
        pass
        
    def close(self):
        pass

def get_connection():
    if IS_POSTGRES:
        # Mock pool
        return PGConnectionWrapper(None)
    else:
        # We don't want to actually connect to sqlite in this test
        print("Would connect to SQLite")
        return None

# Test translations
c = PGCursorWrapper(None)
c.execute("SELECT * FROM users WHERE id = ?", (1,))
c.execute("INSERT OR IGNORE INTO community_likes (post_id, user_id) VALUES (?, ?)", (1, 2))
c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
