"""
test_e2e_onboard.py — US-009 端到端集成测试

模拟新用户从 reset 开始，按 3 块顺序跑完整 onboarding。
每块都有断言：核心池改了 / 因子加了 / 纪律改了。
"""
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"


def run(cmd: list, check: bool = True) -> dict:
    """跑子命令，解析 JSON 返回。"""
    result = subprocess.run(
        ["python3"] + cmd,
        cwd=str(SKILL_DIR.parent.parent),
        capture_output=True, text=True, timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"命令失败: {cmd}\n{result.stderr}")
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def assert_eq(actual, expected, msg: str):
    if actual != expected:
        raise AssertionError(f"{msg}: 期望 {expected!r}，实际 {actual!r}")


def main() -> int:
    print("=" * 60)
    print("US-009 端到端：reset → 3 块 → state.json")
    print("=" * 60)

    # 0. reset（清空所有 state，包括 universe/alpha/risk 子 state）
    print("\n[0] reset")
    r = run([str(SCRIPTS_DIR / "run_onboard.py"), "reset"])
    assert_eq(r["status"], "reset", "reset status")
    # 清理子 state 文件（onboard reset 只删 state.json）
    state_dir = SKILL_DIR / "state"
    for f in ["universe_state.json", "alpha_state.json", "risk_config.json", "audit_log.jsonl"]:
        p = state_dir / f
        if p.exists():
            p.unlink()
    print("    ✓ 子 state 已清理")

    # 1. onboard 第 1 块（不 confirm，应该不推进）
    print("\n[1] onboard (no confirm)")
    r = run([str(SCRIPTS_DIR / "run_onboard.py"), "onboard"])
    assert_eq(r["current_block"], "universe", "current_block 应该=universe")
    assert_eq(r["state"]["completed_blocks"], [], "completed_blocks 应该=[]")
    print("    ✓ 不 confirm 不推进")

    # 2. universe modify 改池（US-002）
    print("\n[2] universe modify --add 159915 --remove 512170")
    r = run([
        str(SCRIPTS_DIR / "run_universe.py"), "modify",
        "--add", "159915", "--remove", "512170",
    ])
    assert_eq(r["changes_applied"]["added"], ["159915"], "added")
    assert_eq(r["changes_applied"]["removed"], ["512170"], "removed")
    print("    ✓ 池改动已应用")

    # 3. onboard --confirm 推进到 alpha
    print("\n[3] onboard --confirm (push to alpha)")
    r = run([str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"])
    assert_eq(r["state"]["completed_blocks"], ["universe"], "completed 应该含 universe")
    assert_eq(r["state"]["current_block"], "alpha", "current 应该=alpha")
    print("    ✓ universe 完成，推进到 alpha")

    # 4. alpha add 因子（US-003）
    print("\n[4] alpha add --factor E2E_TEST_FACTOR")
    r = run([str(SCRIPTS_DIR / "run_alpha.py"), "add", "--factor", "E2E_TEST_FACTOR"])
    assert r["added_to_registry"], "E2E_TEST_FACTOR 应该被新增"
    assert r["registry_count_after"] >= 28, f"registry 应该≥28，实际{r['registry_count_after']}"
    print(f"    ✓ 因子已注册（registry 计数={r['registry_count_after']}）")

    # 5. onboard --confirm 推进到 risk
    print("\n[5] onboard --confirm (push to risk)")
    r = run([str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"])
    assert_eq(r["state"]["completed_blocks"], ["universe", "alpha"], "completed 应该含 universe+alpha")
    assert_eq(r["state"]["current_block"], "risk", "current 应该=risk")
    print("    ✓ alpha 完成，推进到 risk")

    # 6. risk modify 改纪律（US-004）
    print("\n[6] risk modify --stop_loss -0.05 --max_position_pct 0.30")
    r = run([
        str(SCRIPTS_DIR / "run_risk.py"), "modify",
        "--stop_loss", "-0.05", "--max_position_pct", "0.30",
    ])
    assert_eq(r["changes_applied"]["stop_loss_pct"], -0.05, "stop_loss")
    assert_eq(r["changes_applied"]["max_position_pct"], 0.30, "max_position_pct")
    print("    ✓ 纪律已修改")

    # 7. onboard --confirm 推进完成
    print("\n[7] onboard --confirm (final)")
    r = run([str(SCRIPTS_DIR / "run_onboard.py"), "onboard", "--confirm"])
    assert_eq(r["state"]["completed_blocks"], ["universe", "alpha", "risk"], "3 块全完成")
    print("    ✓ 3 块全完成")

    # 8. 验证 verify 真读到 state
    print("\n[8] universe verify 不带参数（应该看到 14+40 from db）")
    r = run([str(SCRIPTS_DIR / "run_universe.py"), "verify"])
    assert_eq(r["before"]["core_count"], 14, "core count from db")
    print(f"    ✓ DB 池={r['before']['core_count']}+{r['before']['reference_count']}")

    # 9. 验证 risk verify 不带参数（应该从 state.json 读）
    print("\n[9] risk verify 不带参数（应该读到 state.json 的 -0.05）")
    r = run([str(SCRIPTS_DIR / "run_risk.py"), "verify"])
    assert_eq(r["before"]["stop_loss_pct"], -0.05, "stop_loss 应该从 state.json 读")
    assert_eq(r["before"]["max_position_pct"], 0.30, "max_position_pct 应该从 state.json 读")
    print(f"    ✓ state.json 纪律 stop_loss={r['before']['stop_loss_pct']}, max_pos={r['before']['max_position_pct']}")

    # 10. 验证 alpha factors 数（应该 27 + 1 E2E = 28）
    print("\n[10] alpha factors（应该含 E2E_TEST_FACTOR）")
    r = run([str(SCRIPTS_DIR / "run_alpha.py"), "factors"])
    assert r["factor_count"] >= 28, f"factor_count 应该≥28，实际{r['factor_count']}"
    print(f"    ✓ factor_count={r['factor_count']}")

    print("\n" + "=" * 60)
    print("✅ US-009 端到端测试全部通过（10 步）")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())