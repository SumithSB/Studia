"""PostgreSQL backend for Studia DB. Used when DATABASE_URL starts with postgresql://."""

import json
import uuid
from contextlib import contextmanager
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from config import DATABASE_URL

_conn = None


def _get_conn():
    global _conn
    if _conn is not None:
        return _conn
    if not DATABASE_URL or not DATABASE_URL.startswith("postgresql"):
        raise RuntimeError("PostgreSQL backend requires DATABASE_URL to start with postgresql://")
    _conn = psycopg2.connect(DATABASE_URL)
    _init_schema(_conn)
    return _conn


@contextmanager
def _cursor():
    conn = _get_conn()
    conn.rollback()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _init_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL DEFAULT '',
                data JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                profile_id TEXT PRIMARY KEY,
                data JSONB NOT NULL DEFAULT '{}',
                updated_at TIMESTAMPTZ NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                target_role TEXT,
                history JSONB NOT NULL DEFAULT '[]',
                research_context TEXT,
                company TEXT,
                summary TEXT,
                updated_at TIMESTAMPTZ NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles(id)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS curriculum (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                keywords JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );
        """)
    conn.commit()


def list_curriculum() -> list[dict]:
    with _cursor() as cur:
        cur.execute("SELECT id, label, category, keywords FROM curriculum ORDER BY id")
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "label": r["label"] or r["id"],
            "category": r["category"] or "",
            "keywords": r["keywords"] if isinstance(r["keywords"], list) else (json.loads(r["keywords"]) if r["keywords"] else []),
        }
        for r in rows
    ]


def get_topic(topic_id: str) -> dict | None:
    with _cursor() as cur:
        cur.execute("SELECT id, label, category, keywords FROM curriculum WHERE id = %s", (topic_id,))
        row = cur.fetchone()
    if not row:
        return None
    kw = row["keywords"]
    return {
        "id": row["id"],
        "label": row["label"] or row["id"],
        "category": row["category"] or "",
        "keywords": kw if isinstance(kw, list) else (json.loads(kw) if kw else []),
    }


def upsert_topic(topic_id: str, label: str, category: str = "", keywords: list | None = None) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    kw = keywords if keywords is not None else []
    with _cursor() as cur:
        cur.execute(
            """INSERT INTO curriculum (id, label, category, keywords, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT(id) DO UPDATE SET label = %s, category = %s, keywords = %s, updated_at = %s""",
            (topic_id, label, category, json.dumps(kw), now, now, label, category, json.dumps(kw), now),
        )


def get_profile(profile_id: str) -> dict | None:
    with _cursor() as cur:
        cur.execute(
            "SELECT id, label, data, created_at, updated_at FROM profiles WHERE id = %s",
            (profile_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    data = row["data"]
    return {
        "id": row["id"],
        "label": row["label"] or "",
        "data": data if isinstance(data, dict) else (json.loads(data) if data else {}),
        "created_at": row["created_at"].isoformat() + "Z" if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        "updated_at": row["updated_at"].isoformat() + "Z" if hasattr(row["updated_at"], "isoformat") else str(row["updated_at"]),
    }


def list_profiles() -> list[dict]:
    with _cursor() as cur:
        cur.execute("SELECT id, label, created_at FROM profiles ORDER BY updated_at DESC")
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "label": r["label"] or r["id"],
            "created_at": r["created_at"].isoformat() + "Z" if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
        }
        for r in rows
    ]


def save_profile(profile_id: str | None, label: str, data: dict) -> str:
    if not profile_id:
        profile_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    with _cursor() as cur:
        cur.execute(
            """INSERT INTO profiles (id, label, data, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT(id) DO UPDATE SET label = %s, data = %s, updated_at = %s""",
            (profile_id, label or profile_id, json.dumps(data), now, now, label or profile_id, json.dumps(data), now),
        )
    return profile_id


def get_default_profile_id() -> str | None:
    with _cursor() as cur:
        cur.execute("SELECT value FROM meta WHERE key = %s", ("default_profile_id",))
        row = cur.fetchone()
    return row["value"] if row and row["value"] else None


def set_default_profile_id(profile_id: str) -> None:
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO meta (key, value) VALUES (%s, %s) ON CONFLICT(key) DO UPDATE SET value = %s",
            ("default_profile_id", profile_id, profile_id),
        )


def profile_exists() -> bool:
    with _cursor() as cur:
        cur.execute("SELECT 1 FROM profiles LIMIT 1")
        return cur.fetchone() is not None


def get_progress(profile_id: str) -> dict:
    with _cursor() as cur:
        cur.execute("SELECT data FROM progress WHERE profile_id = %s", (profile_id,))
        row = cur.fetchone()
    if not row or not row["data"]:
        return {"topics": {}}
    data = row["data"]
    return data if isinstance(data, dict) else json.loads(data)


def save_progress(profile_id: str, data: dict) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    with _cursor() as cur:
        cur.execute(
            """INSERT INTO progress (profile_id, data, updated_at) VALUES (%s, %s, %s)
               ON CONFLICT(profile_id) DO UPDATE SET data = %s, updated_at = %s""",
            (profile_id, json.dumps(data), now, json.dumps(data), now),
        )


def get_session(session_id: str) -> dict | None:
    with _cursor() as cur:
        cur.execute(
            "SELECT id, profile_id, target_role, history, research_context, company, summary, updated_at FROM sessions WHERE id = %s",
            (session_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    history = row["history"]
    if not isinstance(history, list):
        history = json.loads(history) if history else []
    return {
        "id": row["id"],
        "profile_id": row["profile_id"],
        "target_role": row["target_role"],
        "history": history,
        "research_context": row["research_context"] or "",
        "company": row["company"] or "",
        "summary": row["summary"] or "",
        "updated_at": row["updated_at"].isoformat() + "Z" if hasattr(row["updated_at"], "isoformat") else str(row["updated_at"]),
    }


def save_session(
    session_id: str,
    profile_id: str,
    history: list[dict],
    *,
    target_role: str | None = None,
    research_context: str | None = None,
    company: str | None = None,
    summary: str | None = None,
) -> None:
    now = datetime.utcnow().isoformat() + "Z"
    with _cursor() as cur:
        cur.execute(
            """INSERT INTO sessions (id, profile_id, target_role, history, research_context, company, summary, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT(id) DO UPDATE SET
                 profile_id = %s, target_role = %s, history = %s, research_context = %s, company = %s, summary = %s, updated_at = %s""",
            (
                session_id, profile_id, target_role or "", json.dumps(history), research_context or "", company or "", summary or "", now,
                profile_id, target_role or "", json.dumps(history), research_context or "", company or "", summary or "", now,
            ),
        )


def health_check() -> bool:
    try:
        with _cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False
