"""
quantor-onboard/scripts/run_onboard.py — quantor-onboard 整合入口（US-010）

按 Mission quantor-onboard（mission-20260620-235022）US-010 设计。
按 3 块顺序引导：择股 → 择时 → 仓位管理。
支持中断 / 跳过 / 回头（state 持久化到 state.json）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent

STATE_FILE = _SKILL_ROOT / "state.json"


# 3 块顺序
BLOCKS = ["universe", "alpha", "risk"]


def load_state() -> dict:
    """加载 state.json（如不存在返回初始 state）。"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "current_block": "universe",
        "completed_blocks": [],
        "skipped_blocks": [],
        "user_choices": {},
        "checkpoint_acks": {},
    }


def save_state(state: dict) -> None:
    """保存 state.json。"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    # 规则 18：立即验证
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        json.load(f)


def run_block(block_name: str, state: dict) -> dict:
    """调用对应 block 的入口脚本。"""
    script_name = f"run_{block_name}.py"
    script_path = _SKILL_ROOT / "scripts" / script_name

    if not script_path.exists():
        return {"error": f"找不到脚本 {script_name}"}

    # 通过 import 调用（避免 subprocess 开销）
    try:
        sys.path.insert(0, str(script_path.parent))
        module_name = f"run_{block_name}"
        # 重新加载（每次都新鲜）
        if module_name in sys.modules:
            del sys.modules[module_name]
        module = __import__(module_name)
        return module.run_interactive()
    except Exception as e:
        return {"error": f"执行 {block_name} 失败: {e}"}


def run_full_onboard() -> dict:
    """完整 3 块引导。"""
    state = load_state()
    results = {}

    for block in BLOCKS:
        # checkpoint
        if block in state["completed_blocks"]:
            results[block] = {"status": "skipped", "reason": "已完成"}
            continue

        results[block] = run_block(block, state)

        # 更新 state
        state["current_block"] = block
        state["completed_blocks"].append(block)
        save_state(state)

    return {
        "state": state,
        "blocks": results,
        "summary": (
            f"完成 3 块引导：{' → '.join(state['completed_blocks'])}\n"
            f"你的量化模型初稿：\n"
            f"• 择股：14 核心 + 40 参考（可调）\n"
            f"• 择时：C21-1 + 你的因子（可加）\n"
            f"• 仓位：6 个关键纪律（可调）"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quantor Onboard（散户从 0 到 1）")
    parser.add_argument(
        "action", nargs="?", default="onboard",
        choices=["onboard", "status", "reset", "skip", "back"],
    )
    parser.add_argument("--block", choices=BLOCKS, help="指定 block（skip/back 用）")
    args = parser.parse_args()

    state = load_state()

    if args.action == "onboard":
        result = run_full_onboard()
    elif args.action == "status":
        result = {"state": state}
    elif args.action == "reset":
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        result = {"status": "reset", "message": "state.json 已删除"}
    elif args.action == "skip":
        if args.block and args.block not in state["skipped_blocks"]:
            state["skipped_blocks"].append(args.block)
            save_state(state)
        result = {"state": state, "skipped": args.block}
    elif args.action == "back":
        if args.block and args.block in state["completed_blocks"]:
            state["completed_blocks"].remove(args.block)
            state["current_block"] = args.block
            save_state(state)
        result = {"state": state, "back_to": args.block}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())