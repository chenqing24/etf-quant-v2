"""
quant-knowledge/scripts/run_knowledge.py — 量化知识库入口

按 v2 设计（US-024）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent


def get_workspace_root() -> Path:
    """获取 workspace 仓根（含 memory/lessons）。"""
    return _REPO_ROOT.parent


def run_strategy() -> dict:
    """策略列表（从 configs/ 读）。"""
    configs = list((_REPO_ROOT / "configs").glob("*.json"))
    strategies = []
    for cfg_path in configs:
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            strategies.append({
                "strategy_id": data.get("strategy_id"),
                "strategy_name": data.get("strategy_name"),
                "version": data.get("version"),
            })
        except Exception:
            continue
    return {"strategies": strategies, "total": len(strategies)}


def run_lesson(lesson_id: int = None) -> dict:
    """教训列表（从 memory/lessons/ 读）。"""
    lessons_dir = get_workspace_root() / "memory" / "lessons"
    if not lessons_dir.exists():
        return {"lessons": [], "total": 0}
    if lesson_id is not None:
        # 查询单个教训
        lesson_path = lessons_dir / f"L{lesson_id}_*.md"
        matches = list(lessons_dir.glob(f"L{lesson_id}_*.md"))
        if matches:
            return {
                "lesson_id": lesson_id,
                "title": matches[0].stem,
                "content": matches[0].read_text(encoding="utf-8")[:500],
            }
        return {"error": f"L{lesson_id} 不存在"}
    # 全部列表
    lessons = sorted([
        int(re.match(r"L(\d+)", p.name).group(1))
        for p in lessons_dir.glob("L[0-9]*.md")
        if re.match(r"L(\d+)", p.name)
    ])
    return {"lessons": lessons, "total": len(lessons)}


def run_reference() -> dict:
    """业界参考（从 v2-roadmap/ 读）。"""
    v2_root = get_workspace_root() / "v2-roadmap"
    if not v2_root.exists():
        return {"references": [], "total": 0}
    notes = sorted(v2_root.glob("notes/[0-9][0-9]_*.md"))
    return {
        "references": [n.stem for n in notes],
        "total": len(notes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quant Knowledge Skill")
    parser.add_argument("action", nargs="?", default="strategy", choices=["strategy", "lesson", "reference"])
    parser.add_argument("lesson_id", nargs="?", type=int, help="教训 ID（仅 lesson action）")
    args = parser.parse_args()

    if args.action == "strategy":
        result = run_strategy()
    elif args.action == "lesson":
        result = run_lesson(args.lesson_id)
    elif args.action == "reference":
        result = run_reference()
    else:
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())