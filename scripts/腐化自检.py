#!/usr/bin/env python3
"""
8 维度腐化自检脚本（按 v1 教训 L209 + L228 模板）

目的：每完成 3 个 US 跑一次，检测 LLM 智能腐化征兆。

用法：
    python scripts/腐化自检.py --sprint=0
    python scripts/腐化自检.py --sprint=0 --output=json

8 维度（来自 v1 教训）：
    1. Hallucination（幻觉/编造）：方案有没有提已存在的功能？
    2. Context Loss（上下文丢失）：是否引用了 N 跳前的文件但已遗忘？
    3. Task Drift（任务漂移）：是否还在做本 Sprint 的事？
    4. Capability Drift（能力漂移）：是否假设了不存在的工具/API？
    5. 因果倒置：是否把"输出"反推"输入"？
    6. 过度概括：是否用"全部/总是/绝不"等绝对化词？
    7. 重复犯错：是否违反已记录的 v1 教训？
    8. 文档脱节：是否代码改了但文档没更新？

证据要求：
    每个维度必须输出"证据"，不能只打勾 ✅。
    没证据 = 视同 ❌ 严重。

输出：
    - 8 维度分数（0-100）
    - 加权平均
    - 风险点列表
    - 必读教训列表（基于分数触发）
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 8 维度定义（来自 v1 教训 L209 + L228）
DIMENSIONS = [
    {
        "id": 1,
        "name": "Hallucination",
        "description": "幻觉/编造：方案有没有提已存在的功能？",
        "check": "检查：提议的功能是否已存在于代码库？（grep 检查）",
        "weight": 0.15,
    },
    {
        "id": 2,
        "name": "Context Loss",
        "description": "上下文丢失：是否引用了 N 跳前的文件但已遗忘？",
        "check": "检查：本次 commit 引用的所有文件路径是否仍存在？",
        "weight": 0.10,
    },
    {
        "id": 3,
        "name": "Task Drift",
        "description": "任务漂移：是否还在做本 Sprint 的事？",
        "check": "检查：本次 commit 的改动是否在 CHECKPOINT.md 当前 Sprint 清单中？",
        "weight": 0.15,
    },
    {
        "id": 4,
        "name": "Capability Drift",
        "description": "能力漂移：是否假设了不存在的工具/API？",
        "check": "检查：使用的所有 import / 工具是否真实存在？",
        "weight": 0.10,
    },
    {
        "id": 5,
        "name": "因果倒置",
        "description": "因果倒置：是否把'输出'反推'输入'？",
        "check": "检查：归因是否基于外部数据（git log / 测试 / 用户原话），而非'看起来合理'？",
        "weight": 0.10,
    },
    {
        "id": 6,
        "name": "过度概括",
        "description": "过度概括：是否用'全部/总是/绝不'等绝对化词？",
        "check": "检查：本次 commit 消息和文档中是否有绝对化词？",
        "weight": 0.10,
    },
    {
        "id": 7,
        "name": "重复犯错",
        "description": "重复犯错：是否违反已记录的 v1 教训？",
        "check": "检查：本次 commit 是否涉及 L1/L101/L117/L228/L229 等已记录教训？",
        "weight": 0.20,
    },
    {
        "id": 8,
        "name": "文档脱节",
        "description": "文档脱节：是否代码改了但文档没更新？",
        "check": "检查：本次 commit 改的 .py 文件对应的 .md 文档是否同步更新？",
        "weight": 0.10,
    },
]


def check_dimension(dim: dict[str, Any]) -> dict[str, Any]:
    """单个维度自检（人工填写证据 + 分数）"""
    print(f"\n=== 维度 {dim['id']}: {dim['name']} ===")
    print(f"描述: {dim['description']}")
    print(f"检查项: {dim['check']}")

    # 交互式输入证据
    print("\n请提供:")
    evidence = input("  证据（不能为空）：").strip()
    if not evidence:
        return {
            "id": dim["id"],
            "name": dim["name"],
            "score": 0,
            "evidence": "(无证据，按 ❌ 严重处理)",
            "status": "❌ 严重",
            "weight": dim["weight"],
        }

    try:
        score_str = input("  分数（0-100）：").strip()
        score = int(score_str)
        if score < 0 or score > 100:
            raise ValueError
    except ValueError:
        return {
            "id": dim["id"],
            "name": dim["name"],
            "score": 0,
            "evidence": f"分数输入无效: {score_str}",
            "status": "❌ 严重",
            "weight": dim["weight"],
        }

    if score >= 80:
        status = "✅ 通过"
    elif score >= 60:
        status = "⚠️ 中等"
    else:
        status = "❌ 严重"

    return {
        "id": dim["id"],
        "name": dim["name"],
        "score": score,
        "evidence": evidence,
        "status": status,
        "weight": dim["weight"],
    }


def load_lessons() -> dict[str, str]:
    """加载 v1 教训库（从 memory/lessons/INDEX.md）"""
    index_path = Path("/home/qwenpaw/.qwenpaw/workspaces/default/memory/lessons/INDEX.md")
    if not index_path.exists():
        return {"警告": f"教训库 INDEX.md 不存在: {index_path}"}
    return {"info": f"教训库已加载: {index_path}（{len(list(index_path.parent.glob('L*.md')))} 个文件）"}


def main() -> int:
    parser = argparse.ArgumentParser(description="8 维度腐化自检（按 L209 模板）")
    parser.add_argument("--sprint", type=int, required=True, help="当前 Sprint 编号")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--non-interactive", action="store_true", help="非交互模式（默认分数）")
    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print(f"  8 维度腐化自检 — Sprint-{args.sprint}")
    print(f"  时间: {datetime.now().isoformat()}")
    print(f"  教训库: {load_lessons().get('info', 'N/A')}")
    print(f"{'=' * 70}")

    if args.non_interactive:
        # 非交互模式：所有维度默认 100 分（不推荐，仅用于测试）
        results = [
            {
                "id": dim["id"],
                "name": dim["name"],
                "score": 100,
                "evidence": "(non-interactive 默认)",
                "status": "✅ 通过",
                "weight": dim["weight"],
            }
            for dim in DIMENSIONS
        ]
    else:
        results = []
        for dim in DIMENSIONS:
            result = check_dimension(dim)
            results.append(result)
            if result["score"] < 60:
                print(f"\n⚠️ 维度 {dim['id']} 严重问题，建议修复后再继续")

    # 计算加权平均
    weighted_score = sum(r["score"] * r["weight"] for r in results)
    weighted_score = round(weighted_score, 1)

    # 必读教训（基于低分维度）
    triggered_lessons = []
    for r in results:
        if r["score"] < 80:
            if r["id"] == 7:
                triggered_lessons.extend(["L101", "L117", "L228", "L229"])
            elif r["id"] == 1:
                triggered_lessons.extend(["L228", "L229"])
            elif r["id"] == 3:
                triggered_lessons.extend(["L228"])
            elif r["id"] == 8:
                triggered_lessons.extend(["L118", "L119"])
    triggered_lessons = sorted(set(triggered_lessons))

    output = {
        "sprint": args.sprint,
        "timestamp": datetime.now().isoformat(),
        "weighted_score": weighted_score,
        "dimensions": results,
        "triggered_lessons": triggered_lessons,
        "verdict": (
            "✅ 优秀" if weighted_score >= 90
            else "✅ 合格" if weighted_score >= 70
            else "⚠️ 需改进" if weighted_score >= 50
            else "❌ 不合格 — 立即反思"
        ),
    }

    if args.output == "json":
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'=' * 70}")
        print(f"  自评结果 — Sprint-{args.sprint}")
        print(f"{'=' * 70}")
        for r in results:
            print(f"  维度 {r['id']} ({r['name']}): {r['score']}/100  {r['status']}")
            print(f"    证据: {r['evidence']}")
        print(f"\n  加权平均: {weighted_score}/100")
        print(f"  判定: {output['verdict']}")
        if triggered_lessons:
            print(f"  必读教训: {', '.join(triggered_lessons)}")

    # 输出报告
    report_path = Path(f"/tmp/腐化自检_sprint-{args.sprint}.json")
    report_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  报告保存: {report_path}")

    # 退出码：< 70 警告，< 50 失败
    return 0 if weighted_score >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())