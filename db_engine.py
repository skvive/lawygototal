"""SQLite (local) or Neon Postgres (Vercel production) with SQL adaptation for LAWYGO CMS."""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any

DATABASE_URL = (
    os.getenv("DATABASE_URL", "").strip()
    or os.getenv("NEON_DATABASE_URL", "").strip()
)
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _adapt_sql(sql: str) -> str:
    if not USE_POSTGRES:
        return sql
    s = sql
    s = re.sub(r"\bINSERT OR IGNORE\b", "INSERT", s, flags=re.I)
    s = s.replace("?", "%s")
    s = re.sub(r"\bBEGIN IMMEDIATE\b", "BEGIN", s, flags=re.I)
    s = re.sub(r"DATE\s*\(\s*'now'\s*\)", "CURRENT_DATE", s, flags=re.I)
    if re.search(r"^INSERT\b", s.strip(), re.I) and "ON CONFLICT" not in s.upper():
        compact = s.replace(" ", "")
        if "boards(id,tenant,product,slug" in compact:
            s = s.rstrip().rstrip(";") + " ON CONFLICT (tenant, product, slug) DO NOTHING"
        elif "users(id,tenant,email" in compact:
            s = s.rstrip().rstrip(";") + " ON CONFLICT (tenant, email) DO NOTHING"
    return s


class _Row(dict):
    def __getitem__(self, key: Any):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class CompatCursor:
    def __init__(self, raw, is_pg: bool):
        self._raw = raw
        self._is_pg = is_pg
        self._lastrowid: int | None = None

    def execute(self, sql: str, params: tuple | list = ()):
        adapted = _adapt_sql(sql)
        self._raw.execute(adapted, params)
        self._lastrowid = None
        return self

    def executemany(self, sql: str, seq):
        self._raw.executemany(_adapt_sql(sql), seq)
        return self

    def executescript(self, script: str):
        if not USE_POSTGRES:
            self._raw.executescript(script)
            return self
        stmts: list[str] = []
        buf: list[str] = []
        for line in script.splitlines():
            stripped = line.strip()
            if stripped.startswith("PRAGMA"):
                continue
            buf.append(line)
            if ";" in line:
                chunk = "\n".join(buf)
                buf = []
                for part in chunk.split(";"):
                    part = part.strip()
                    if not part:
                        continue
                    stmts.append(_adapt_pg_ddl(part))
        for stmt in stmts:
            self._raw.execute(stmt)
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        if row is None:
            return None
        if self._is_pg:
            cols = [d.name if hasattr(d, "name") else d[0] for d in self._raw.description]
            return _Row(zip(cols, row))
        return row

    def fetchall(self):
        rows = self._raw.fetchall()
        if not self._is_pg:
            return rows
        cols = [d.name if hasattr(d, "name") else d[0] for d in self._raw.description]
        return [_Row(zip(cols, r)) for r in rows]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def lastrowid(self) -> int | None:
        return self._lastrowid


def _adapt_pg_ddl(stmt: str) -> str:
    s = _adapt_sql(stmt)
    s = re.sub(
        r"id INTEGER PRIMARY KEY AUTOINCREMENT",
        "id BIGSERIAL PRIMARY KEY",
        s,
        flags=re.I,
    )
    return s


class CompatConnection:
    def __init__(self, raw, is_pg: bool):
        self._raw = raw
        self._is_pg = is_pg

    def execute(self, sql: str, params: tuple | list = ()):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executescript(self, script: str):
        return self.cursor().executescript(script)

    def executemany(self, sql: str, seq):
        return self.cursor().executemany(sql, seq)

    def cursor(self) -> CompatCursor:
        return CompatCursor(self._raw.cursor(), self._is_pg)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()


@contextmanager
def open_db(db_path: str | None = None):
    if USE_POSTGRES:
        import psycopg

        conn = psycopg.connect(DATABASE_URL, autocommit=False)
        try:
            yield CompatConnection(conn, True)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        from pathlib import Path

        path = Path(db_path or os.getenv("LAWYGO_DB_PATH", "data/lawygo.db"))
        path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(path), timeout=15, isolation_level=None, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=15000")
        con.execute("PRAGMA journal_mode=WAL")
        try:
            yield CompatConnection(con, False)
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def storage_label() -> str:
    return "neon-postgres" if USE_POSTGRES else "sqlite"
