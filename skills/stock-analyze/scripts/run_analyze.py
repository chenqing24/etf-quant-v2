"""
stock-analyze/scripts/run_analyze.py — 个股深度分析入口

按 v2 设计（US-022）。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent


def get_db_path() -> str:
    """获取数据库路径。"""
    return os.environ.get("ETF_QUANT_DB_PATH", str(_REPO_ROOT / "data" / "etf.db"))


def run_info(code: str) -> dict:
    """查询单只股票基本信息。"""
    db_path = get_db_path()
    if not Path(db_path).exists():
        return {"error": "DB 不存在", "code": code}
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT code, name, exchange, full_code, list_date, updated_at FROM stock_info WHERE code = ?",
            (code,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"error": "未找到", "code": code}
    return {
        "code": row[0], "name": row[1], "exchange": row[2],
        "full_code": row[3], "list_date": row[4], "updated_at": row[5],
    }


def run_compare(code: str) -> dict:
    """vs 板块/大盘对比（v2 占位）。"""
    info = run_info(code)
    return {
        "stock": info,
        "sector_avg": "v2_占位",  # 待 US-022 完善
        "market_avg": "v2_占位",
    }


def run_sector(code: str) -> dict:
    """板块成分股（v2 占位）。"""
    return {"code": code, "sector_members": "v2_占位"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Stock Analyze Skill")
    parser.add_argument("action", nargs="?", default="info", choices=["info", "compare", "sector"])
    parser.add_argument("code", nargs="?", default="600519", help="股票代码")
    args = parser.parse_args()

    if args.action == "info":
        result = run_info(args.code)
    elif args.action == "compare":
        result = run_compare(args.code)
    elif args.action == "sector":
        result = run_sector(args.code)
    else:
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())