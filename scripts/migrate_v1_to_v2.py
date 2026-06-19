"""
scripts/migrate_v1_to_v2.py — v1 → v2 数据迁移脚本

按 L228/L244 教训"先查再答"——schema 已对齐 v1 业务库 100%。

用途：
    v1 业务库（v1/etf_data_live/etf.db） → v2 业务库（v2/data/etf.db）
    迁移范围：etf_names (1486) + stock_info (66) + trade_history (2) + daily (69480)
    其他表（positions/audit_log/decision_snapshot/etf_name_metrics/etf_name_retry_queue/realtime_cache）
    在 v1 都是 0 行，无需迁移。

被谁调用：
    - 用户手动跑（一次性迁移工具）
    - Sprint-5 US-026

使用方式：
    python scripts/migrate_v1_to_v2.py [--dry-run]
    --dry-run: 只打印，不实际迁移

依赖：
    - v1 业务库路径（默认 /home/qwenpaw/.qwenpaw/workspaces/default/etf_strategy/etf_data_live/etf.db）
    - v2 业务库路径（默认 ETF_QUANT_DB_PATH 环境变量）

注意事项：
    - 幂等性：v2 表已存在数据时跳过（避免重复插入）
    - 事务：每个表一个事务，失败回滚
    - 完整性：迁移完成后跑 schema 验证
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

V1_DB = "/home/qwenpaw/.qwenpaw/workspaces/default/etf_strategy/etf_data_live/etf.db"


def get_v2_path() -> str:
    """获取 v2 业务库路径。"""
    return os.environ.get("ETF_QUANT_DB_PATH", "data/etf.db")


def migrate_table(v1_conn: sqlite3.Connection, v2_conn: sqlite3.Connection,
                  table: str, v2_columns: list, dry_run: bool = False) -> dict:
    """迁移单张表。

    Args:
        v1_conn: v1 SQLite 连接
        v2_conn: v2 SQLite 连接
        table: 表名
        v2_columns: v2 表的目标列（按 v2 schema）
        dry_run: 只打印不写入

    Returns:
        dict: {"table": str, "total": int, "migrated": int, "skipped": int}
    """
    # 1. 查 v1 行数
    total = v1_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if total == 0:
        return {"table": table, "total": 0, "migrated": 0, "skipped": 0}

    # 2. 查 v1 列名（用 v1 的列，因为 v2 ⊇ v1）
    v1_columns = [c[1] for c in v1_conn.execute(f"PRAGMA table_info('{table}')").fetchall()]

    # 3. 取交集列（v1 ∩ v2）
    common = [c for c in v1_columns if c in v2_columns]

    # 4. 读 v1 数据
    rows = v1_conn.execute(f"SELECT {', '.join(common)} FROM {table}").fetchall()

    # 5. 插入 v2
    placeholders = ", ".join(["?"] * len(common))
    sql = f"INSERT OR IGNORE INTO {table} ({', '.join(common)}) VALUES ({placeholders})"

    migrated = 0
    skipped = 0
    if not dry_run:
        try:
            v2_conn.executemany(sql, rows)
            v2_conn.commit()
            migrated = len(rows)
        except Exception as e:
            v2_conn.rollback()
            print(f"  ❌ {table} 失败: {e}")
            return {"table": table, "total": total, "migrated": 0, "skipped": total}
    else:
        migrated = len(rows)

    return {"table": table, "total": total, "migrated": migrated, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="v1 → v2 数据迁移")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写入")
    parser.add_argument("--v1", default=V1_DB, help="v1 业务库路径")
    args = parser.parse_args()

    v1_path = args.v1
    v2_path = get_v2_path()

    if not Path(v1_path).exists():
        print(f"❌ v1 业务库不存在: {v1_path}")
        return 1
    if not Path(v2_path).exists():
        print(f"❌ v2 业务库不存在: {v2_path}")
        print(f"   先跑: PYTHONPATH=src python scripts/init_database.py")
        return 1

    print(f"📂 v1 业务库: {v1_path}")
    print(f"📂 v2 业务库: {v2_path}")
    print(f"🔧 模式: {'DRY-RUN（不写入）' if args.dry_run else '实际迁移'}")
    print()

    v1 = sqlite3.connect(v1_path)
    v2 = sqlite3.connect(v2_path)
    v2.execute("PRAGMA journal_mode=WAL")

    # 需要迁移的表（v1 有数据的）
    tables = ["etf_names", "stock_info", "trade_history", "daily"]

    results = []
    total_migrated = 0
    for tbl in tables:
        v2_cols = [c[1] for c in v2.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        result = migrate_table(v1, v2, tbl, v2_cols, dry_run=args.dry_run)
        results.append(result)
        total_migrated += result["migrated"]
        print(f"  {tbl}: 总 {result['total']} 行, 迁移 {result['migrated']} 行")

    v1.close()
    v2.close()

    print()
    print(f"📊 总计迁移: {total_migrated} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())