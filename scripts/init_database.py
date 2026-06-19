"""
init_database.py — 一键初始化 v2 数据库

按 v1 scripts/init_database.py 模式（v1 6/17 升级版）。
执行 schema/migrations/ 下所有 SQL 迁移，按编号顺序。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# 项目根
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_DIR = _REPO_ROOT / "schema" / "migrations"
sys.path.insert(0, str(_REPO_ROOT / "src"))

from etf_quant.config import constants  # noqa: E402


def apply_migration(conn: sqlite3.Connection, sql_path: Path) -> bool:
    """应用单个 SQL 迁移文件。

    容错策略：
    - CREATE TABLE 失败（如已存在）= 视为成功
    - ALTER TABLE ADD COLUMN 失败（重复列）= 视为成功（v1 增量迁移设计假设）
    - 其他失败 = 真正失败
    """
    print(f"  应用: {sql_path.name}")
    try:
        sql = sql_path.read_text(encoding="utf-8")
        # 分割每个语句独立执行（executescript 不容错）
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in statements:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as e:
                err_msg = str(e).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    # CREATE TABLE IF NOT EXISTS / ALTER TABLE ADD COLUMN 已存在
                    continue
                raise
        conn.commit()
        return True
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False


def main() -> int:
    # 支持环境变量覆盖（用于测试）
    import os
    db_path = os.environ.get("ETF_QUANT_DB_PATH", constants.DB_PATH)
    print(f"📦 初始化 v2 数据库: {db_path}")
    print(f"📁 Schema 目录: {_SCHEMA_DIR}")
    print(f"📐 WAL 模式: {constants.WAL_MODE_ENABLED}")

    # 创建目录
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # 列出所有 SQL 迁移（按文件名排序）
    sql_files = sorted(_SCHEMA_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    if not sql_files:
        print(f"❌ 未找到 SQL 迁移文件: {_SCHEMA_DIR}")
        return 1

    print(f"\n🔄 共 {len(sql_files)} 个迁移:")
    for f in sql_files:
        print(f"  - {f.name}")

    # 连接 DB + 启用 WAL
    conn = sqlite3.connect(db_path)
    if constants.WAL_MODE_ENABLED:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        print(f"\n✅ WAL 模式已启用")

    # 应用所有迁移
    print(f"\n🔧 开始应用迁移:")
    success_count = 0
    for sql_path in sql_files:
        if apply_migration(conn, sql_path):
            success_count += 1

    # 验证表创建
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 数据库表 ({len(tables)} 个):")
    for t in tables:
        print(f"  - {t}")

    # 验证 schema_version
    try:
        cursor = conn.execute("SELECT version, description, applied_at FROM schema_version")
        rows = cursor.fetchall()
        print(f"\n📋 schema_version 记录 ({len(rows)} 条):")
        for v, desc, ts in rows:
            print(f"  - {v}: {desc[:50]} ({ts})")
    except Exception as e:
        print(f"\n⚠️ schema_version 表未创建: {e}")

    conn.close()
    print(f"\n{'✅' if success_count == len(sql_files) else '⚠️'} "
          f"成功 {success_count}/{len(sql_files)} 个迁移")
    return 0 if success_count == len(sql_files) else 1


if __name__ == "__main__":
    sys.exit(main())
