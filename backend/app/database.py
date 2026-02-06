"""SQLite 数据库：图谱元数据、每日查询统计、用户、查询记录"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from app.config import PROJECT_ROOT, DATA_DIR, GRAPHS_DIR

DB_PATH = DATA_DIR / "rag_web.db"


def _get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def init_db():
    """初始化表"""
    conn = _get_conn()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS graphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            working_dir TEXT UNIQUE,
            daily_limit INTEGER DEFAULT 100,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS query_stats (
            graph_id INTEGER NOT NULL,
            stat_date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (graph_id, stat_date),
            FOREIGN KEY (graph_id) REFERENCES graphs(id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            graph_id INTEGER NOT NULL,
            query_text TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (graph_id) REFERENCES graphs(id)
        );
        CREATE INDEX IF NOT EXISTS idx_query_history_user_graph ON query_history(user_id, graph_id);
        CREATE INDEX IF NOT EXISTS idx_query_history_created ON query_history(created_at);
        """)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_db():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- 图谱 CRUD ---

def graph_create(name: str, description: str, working_dir: Optional[str] = None, daily_limit: int = 100) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO graphs (name, description, working_dir, daily_limit, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, description, working_dir, daily_limit, datetime.now(timezone.utc).isoformat())
        )
        return cur.lastrowid


def graph_list(include_private: bool = False) -> List[dict]:
    """列表。include_private=False 时只返回 name, description（前端展示）；True 时返回全部（管理端）"""
    with get_db() as conn:
        rows = conn.execute("SELECT id, name, description, working_dir, daily_limit, created_at FROM graphs ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if not include_private:
            d = {"id": d["id"], "name": d["name"], "description": d["description"]}
        out.append(d)
    return out


def graph_get(graph_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT id, name, description, working_dir, daily_limit, created_at FROM graphs WHERE id = ?", (graph_id,)).fetchone()
    return dict(row) if row else None


def graph_update_meta(graph_id: int, name: Optional[str] = None, description: Optional[str] = None):
    if name is None and description is None:
        return
    with get_db() as conn:
        if name is not None:
            conn.execute("UPDATE graphs SET name = ? WHERE id = ?", (name, graph_id))
        if description is not None:
            conn.execute("UPDATE graphs SET description = ? WHERE id = ?", (description, graph_id))


def graph_set_daily_limit(graph_id: int, daily_limit: int):
    with get_db() as conn:
        conn.execute("UPDATE graphs SET daily_limit = ? WHERE id = ?", (daily_limit, graph_id))


def graph_delete(graph_id: int) -> Optional[str]:
    """删除记录并返回 working_dir 以便删除目录。若不存在返回 None"""
    g = graph_get(graph_id)
    if not g:
        return None
    with get_db() as conn:
        conn.execute("DELETE FROM query_stats WHERE graph_id = ?", (graph_id,))
        conn.execute("DELETE FROM graphs WHERE id = ?", (graph_id,))
    return g["working_dir"]


# --- 查询统计 ---

def query_stat_inc(graph_id: int) -> bool:
    """今日该图谱查询次数 +1。若未超限返回 True，超限返回 False（调用方需先检查）"""
    today = date.today().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO query_stats (graph_id, stat_date, count) VALUES (?, ?, 1) ON CONFLICT(graph_id, stat_date) DO UPDATE SET count = count + 1",
            (graph_id, today)
        )
    return True


def query_stat_get_today(graph_id: int) -> int:
    today = date.today().isoformat()
    with get_db() as conn:
        row = conn.execute("SELECT count FROM query_stats WHERE graph_id = ? AND stat_date = ?", (graph_id, today)).fetchone()
    return row[0] if row else 0


def query_stat_get_today_all() -> List[dict]:
    """所有图谱今日查询次数"""
    today = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT g.id, g.name, g.daily_limit, COALESCE(s.count, 0) AS today_count
            FROM graphs g
            LEFT JOIN query_stats s ON g.id = s.graph_id AND s.stat_date = ?
            ORDER BY g.id
        """, (today,)).fetchall()
    return [dict(r) for r in rows]


def can_query_today(graph_id: int) -> tuple[bool, int, int]:
    """(是否可查询, 今日已用次数, 每日限额)"""
    g = graph_get(graph_id)
    if not g:
        return False, 0, 0
    limit = g["daily_limit"]
    used = query_stat_get_today(graph_id)
    return used < limit, used, limit


# --- 用户 ---

def user_create(username: str, password_hash: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now(timezone.utc).isoformat())
        )
        return cur.lastrowid


def user_get_by_username(username: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    return dict(row) if row else None


def user_list(search: Optional[str] = None) -> List[dict]:
    """管理端：用户列表，可选按用户名搜索。"""
    with get_db() as conn:
        if search and search.strip():
            q = "SELECT id, username, created_at FROM users WHERE username LIKE ? ORDER BY id"
            rows = conn.execute(q, (f"%{search.strip()}%",)).fetchall()
        else:
            rows = conn.execute("SELECT id, username, created_at FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def user_update_password(user_id: int, password_hash: str):
    with get_db() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def user_get(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def user_delete(user_id: int) -> bool:
    """删除用户并级联删除其查询记录。存在则返回 True，不存在返回 False。"""
    u = user_get(user_id)
    if not u:
        return False
    with get_db() as conn:
        conn.execute("DELETE FROM query_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return True


# --- 查询记录（仅保留 7 天内）---

HISTORY_DAYS = 7


def _history_cutoff() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)).isoformat()


def query_history_add(user_id: int, graph_id: int, query_text: str, answer: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO query_history (user_id, graph_id, query_text, answer, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, graph_id, query_text, answer, datetime.now(timezone.utc).isoformat())
        )
        # 删除 7 天前的记录
        conn.execute("DELETE FROM query_history WHERE created_at < ?", (_history_cutoff(),))


def query_history_list(user_id: int, graph_id: int) -> List[dict]:
    """某用户在某图谱下、7 天内的查询记录，按时间倒序。"""
    cutoff = _history_cutoff()
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, user_id, graph_id, query_text, answer, created_at
               FROM query_history
               WHERE user_id = ? AND graph_id = ? AND created_at >= ?
               ORDER BY created_at DESC""",
            (user_id, graph_id, cutoff)
        ).fetchall()
    return [dict(r) for r in rows]


def query_history_list_by_user(user_id: int) -> List[dict]:
    """某用户全部 7 天内记录，按时间倒序（管理端用）。"""
    cutoff = _history_cutoff()
    with get_db() as conn:
        rows = conn.execute(
            """SELECT h.id, h.user_id, h.graph_id, h.query_text, h.answer, h.created_at, g.name AS graph_name
               FROM query_history h
               LEFT JOIN graphs g ON g.id = h.graph_id
               WHERE h.user_id = ? AND h.created_at >= ?
               ORDER BY h.created_at DESC""",
            (user_id, cutoff)
        ).fetchall()
    return [dict(r) for r in rows]


def query_history_delete(user_id: int, history_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM query_history WHERE id = ? AND user_id = ?",
            (history_id, user_id)
        )
    return cur.rowcount > 0
