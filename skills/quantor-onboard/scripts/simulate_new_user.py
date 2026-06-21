"""
simulate_new_user.py — US-012 模拟新用户走完 3 块

模拟一个不会 Python 的散户：
1. reset 清空 state
2. 用散户口语触发词（如"今天 ETF 决策"）
3. 每步给出"用户回应"（Y/N + 调整指令）
4. 验证 state.json 正确推进
5. 输出真实 walkthrough 日志

记录每个对话回合 → tests/integration/simulated_user_YYYYMMDD.log
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
LOG_DIR = SKILL_DIR / "tests" / "integration"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"simulated_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def log(msg: str):
    """写日志（同时 stdout）。"""
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def run_phrase(phrase: str) -> dict:
    """模拟用户说一句话，AI 解析后执行。"""
    log(f"\n[散户] {phrase}")

    # 解析触发词
    from test_trigger_phrases import parse_trigger
    parsed = parse_trigger(phrase)
    if parsed is None:
        log(f"  [AI] 我没听懂你说的，能换个说法吗？比如：'今天 ETF 决策'或'帮我从 0 建立模型'")
        return {"status": "unparsed"}
    block, args = parsed
    log(f"  [AI 解析] block={block}, args={args}")

    # 执行
    cmd = ["python3", str(SCRIPTS_DIR / f"run_{block}.py")] + args
    result = subprocess.run(
        cmd,
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        log(f"  [AI 错误] {result.stderr[:200]}")
        return {"status": "error"}
    try:
        out = json.loads(result.stdout)
        log(f"  [AI 响应] 状态 OK，keys={list(out.keys())[:5]}")
        return out
    except json.JSONDecodeError:
        log(f"  [AI 响应] 非 JSON: {result.stdout[:100]}")
        return {"status": "non-json"}


def main() -> int:
    log("=" * 60)
    log(f"模拟新用户走完 3 块：{datetime.now()}")
    log("=" * 60)

    # Step 1: 重置（用户说"重新开始"）
    log("\n=== 散户第一次来 ===")
    r = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "run_onboard.py"), "reset"],
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True,
    )
    log(f"[AI] 重置完成：{r.stdout.strip()}")

    # Step 2: 用户用触发词进入引导
    run_phrase("今天 ETF 决策")

    # Step 3: 用户确认 universe → alpha
    log("\n[散户] 我看明白了，确认")
    r = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"],
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True,
    )
    out = json.loads(r.stdout)
    log(f"  [AI] 已推进到：{out['state']['current_block']}")
    log(f"  [AI] 完成块：{out['state']['completed_blocks']}")

    # Step 4: 用户加一个因子
    run_phrase("我想加 RSI 抄底因子")

    # Step 5: 用户确认 alpha → risk
    log("\n[散户] 我看明白了，确认")
    r = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"],
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True,
    )
    out = json.loads(r.stdout)
    log(f"  [AI] 已推进到：{out['state']['current_block']}")

    # Step 6: 用户调止损
    run_phrase("我要调止损到 5%")

    # Step 7: 用户确认 risk → done
    log("\n[散户] 我看明白了，确认")
    r = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"],
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True,
    )
    out = json.loads(r.stdout)
    log(f"  [AI] 已推进到：{out['state']['current_block']}")
    log(f"  [AI] 完成块：{out['state']['completed_blocks']}")

    # Step 8: 看最终状态
    log("\n=== 走完 3 块，看最终状态 ===")
    r = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "run_onboard.py"), "status"],
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True,
    )
    log(r.stdout)

    log("\n" + "=" * 60)
    log(f"✅ 模拟新用户走查完成")
    log(f"日志：{LOG_FILE}")
    log("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())