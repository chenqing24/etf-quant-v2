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


def run_full_onboard(confirm: bool = False) -> dict:
    """US-005: 强制走 3 块对话。

    不带 --confirm: 只跑 current_block 的第 1 步，不标 completed
    带 --confirm: 标记当前块完成，推进到下一块
    """
    state = load_state()

    # 防御：如果已完成 3 块，提示并返回
    if len(state["completed_blocks"]) >= len(BLOCKS):
        return {
            "state": state,
            "status": "all_done",
            "summary": (
                f"已完成 3 块：{' → '.join(state['completed_blocks'])}\n"
                f"如果想重来：python run_onboard.py reset"
            ),
        }

    current = state["current_block"]
    block_result = run_block(current, state)

    if confirm:
        # 用户确认完成当前块
        if current not in state["completed_blocks"]:
            state["completed_blocks"].append(current)
        # 推进到下一块
        idx = BLOCKS.index(current)
        if idx + 1 < len(BLOCKS):
            state["current_block"] = BLOCKS[idx + 1]
        save_state(state)

    return {
        "state": state,
        "current_block": current,
        "block_result_summary": {
            "block": current,
            "keys": list(block_result.keys())[:5] if isinstance(block_result, dict) else "non-dict",
            "hint": (
                f"【对话完成提示】\n\n"
                f"你刚跑了 {current} 块的引导（见 block_result_summary）。\n"
                f"如果你看明白了，告诉我'确认'，我会把这一块标 completed 并推进到下一块。\n"
                f"如果还不明白，继续问我。\n\n"
                f"下一步：\n"
                f"python run_onboard.py onboard --confirm  # 确认本块并推进\n"
                f"python run_onboard.py status  # 看当前状态"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quantor Onboard（散户从 0 到 1）")
    parser.add_argument(
        "action", nargs="?", default="onboard",
        choices=["onboard", "status", "reset", "skip", "back"],
    )
    parser.add_argument("--block", choices=BLOCKS, help="指定 block（skip/back 用）")
    parser.add_argument("--confirm", action="store_true", help="确认完成当前块并推进（US-005）")
    args = parser.parse_args()

    state = load_state()

    if args.action == "onboard":
        result = run_full_onboard(confirm=args.confirm)
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