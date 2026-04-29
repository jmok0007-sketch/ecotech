"""PostgreSQL connection pool.

A single global pool is created at startup and shared by all requests."""
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

from config import Config

_pool: pg_pool.SimpleConnectionPool | None = None


def init_pool() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = pg_pool.SimpleConnectionPool(
        minconn=Config.POOL_MIN,
        maxconn=Config.POOL_MAX,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_cursor(dict_rows: bool = True):
    """Yield (conn, cursor) and ensure proper cleanup.

    Usage:
        with get_cursor() as (conn, cur):
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        cursor_factory = psycopg2.extras.RealDictCursor if dict_rows else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        _pool.putconn(conn)
