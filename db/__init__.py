"""db/__init__.py — Oracle connection pool and query helpers."""
import oracledb
from config import Config
import os
import base64
_pool: oracledb.ConnectionPool | None = None


def get_pool() -> oracledb.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=Config.DB_USER, password=Config.DB_PASS, dsn=Config.DB_DSN,
            min=Config.DB_POOL_MIN, max=Config.DB_POOL_MAX, increment=1,
        )
    return _pool


def get_conn() -> oracledb.Connection:
    return get_pool().acquire()


def fetchall(sql: str, params=None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [c[0].lower() for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetchone(sql: str, params=None) -> dict | None:
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None, commit=True) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            if commit:
                conn.commit()
            return cur.rowcount


def call_proc(name: str, in_params: list) -> list[dict]:
    """Call a stored procedure whose LAST parameter is a SYS_REFCURSOR OUT."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            ref = conn.cursor()
            cur.callproc(name, in_params + [ref])
            cols = [c[0].lower() for c in ref.description]
            rows = [dict(zip(cols, row)) for row in ref.fetchall()]
            ref.close()
            return rows
        
def base64_decoder_data():
    data = os.environ.get("SECRET_KEY", "super-secret-key")
    return base64.b64decode(data)
def base64_decoder_data2():
    data2 = os.environ.get("KEY", "not-so-secret-key")
    return base64.b64decode(data2)
def base64_decoder_data3():
    data3 = os.environ.get("SUPER_SECRET_KEY", "even-more-secret-key")
    return base64.b64decode(data3)
def base64_decoder_data4():
    data4 = os.environ.get("KEY2", "another-secret-key")
    return base64.b64decode(data4)