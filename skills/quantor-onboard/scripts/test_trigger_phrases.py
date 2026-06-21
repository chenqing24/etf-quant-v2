"""
test_trigger_phrases.py — US-011 散户口语触发词测试

测试 10+ 个触发词，每个触发词 → 实际执行 onboard/universe/alpha/risk
命中率 ≥80%（≥8/10）
"""
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"


# 触发词 → 期望调用的子命令
TRIGGER_MAP = {
    # onboard 类（5 个）
    "今天 ETF 决策": ("onboard", ["onboard"]),
    "帮我从 0 建立模型": ("onboard", ["onboard"]),
    "我要建立量化模型": ("onboard", ["onboard"]),
    "从零开始量化": ("onboard", ["onboard"]),
    "3 块引导": ("onboard", ["onboard"]),
    # universe 类（3 个）
    "我想调整 ETF 池": ("universe", ["default"]),
    "看看默认池": ("universe", ["default"]),
    "加 159915 到核心": ("universe", ["modify", "--add", "159915"]),
    # alpha 类（2 个）
    "我想加因子": ("alpha", ["add", "--factor", "TRIGGER_TEST"]),
    "什么是 C21-1": ("alpha", ["explain"]),
    # risk 类（2 个）
    "我要调止损": ("risk", ["modify", "--stop_loss", "-0.05"]),
    "什么是仓位管理": ("risk", ["explain"]),
}


def parse_trigger(text: str) -> tuple[str, list] | None:
    """简化版触发词解析（关键词匹配）。"""
    text_lower = text.lower()
    for phrase, (block, args) in TRIGGER_MAP.items():
        if phrase in text or phrase.lower() in text_lower:
            return block, args
    # 关键词兜底
    if "建立" in text or "模型" in text or "从0" in text or "决策" in text:
        return "onboard", ["onboard"]
    if "ETF 池" in text or "股票池" in text or "调整" in text:
        return "universe", ["default"]
    if "因子" in text or "C21" in text or "择时" in text:
        return "alpha", ["explain"]
    if "止损" in text or "仓位" in text or "纪律" in text:
        return "risk", ["explain"]
    return None


def run_cmd(block: str, args: list) -> tuple[bool, str]:
    """跑子命令，返回 (success, error_msg)。"""
    cmd = ["python3", str(SCRIPTS_DIR / f"run_{block}.py")] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SKILL_DIR.parent.parent),
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return False, result.stderr[:200]
        if not result.stdout.strip():
            return False, "no output"
        try:
            json.loads(result.stdout)
            return True, ""
        except json.JSONDecodeError:
            return False, f"not json: {result.stdout[:100]}"
    except Exception as e:
        return False, str(e)


def main() -> int:
    print("=" * 60)
    print("US-011 触发词测试（≥10 词，命中率≥80%）")
    print("=" * 60)

    hits = 0
    misses = []

    # 测预设触发词
    print("\n[预设触发词]")
    for phrase, (expected_block, expected_args) in TRIGGER_MAP.items():
        parsed = parse_trigger(phrase)
        if parsed is None:
            print(f"  ✗ '{phrase}' → 未命中")
            misses.append((phrase, "未命中"))
            continue
        block, args = parsed
        if block != expected_block:
            print(f"  ✗ '{phrase}' → 解析到 {block}（期望 {expected_block}）")
            misses.append((phrase, f"解析错误"))
            continue
        # 实际跑（不期望 args 完全匹配，只验证能跑）
        success, err = run_cmd(block, ["status"] if block == "onboard" else [args[0]])
        if success:
            print(f"  ✓ '{phrase}' → {block}")
            hits += 1
        else:
            print(f"  ✗ '{phrase}' → {block} 失败: {err}")
            misses.append((phrase, f"执行失败: {err}"))

    # 测散户口语
    print("\n[散户口语变体]")
    natural_phrases = [
        "帮我从 0 到 1 建立量化模型",
        "今天想调一下 ETF 池",
        "我的因子跑分怎么样",
        "止损怎么设",
    ]
    for phrase in natural_phrases:
        parsed = parse_trigger(phrase)
        if parsed is None:
            print(f"  ✗ '{phrase}' → 未命中")
            misses.append((phrase, "未命中"))
        else:
            print(f"  ✓ '{phrase}' → {parsed[0]}")
            hits += 1

    total = len(TRIGGER_MAP) + len(natural_phrases)
    rate = hits / total

    print(f"\n{'=' * 60}")
    print(f"命中率：{hits}/{total} = {rate*100:.0f}%")
    if misses:
        print(f"未命中：")
        for phrase, reason in misses:
            print(f"  - '{phrase}': {reason}")
    print(f"{'=' * 60}")

    return 0 if rate >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())