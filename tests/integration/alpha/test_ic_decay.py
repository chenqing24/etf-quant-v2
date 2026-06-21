"""
tests/integration/alpha/test_ic_decay.py — US-010 季度 IC 巡检测试

按规则 5.1：关键路径测试覆盖
按规则 18：CSV/JSON 必验证
按规则 27：IC 入库必带 + 季度必巡检

总计：7 测试
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


PROJECT_ROOT = Path("/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2")
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
SCRIPT = PROJECT_ROOT / "scripts" / "check_ic_decay.py"
HISTORY_CSV = PROJECT_ROOT / "data" / "factor_icir_history.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"


def test_load_history_returns_list():
    """US-010 AC1: load_history 返回 list[dict]"""
    from check_ic_decay import load_history
    rows = load_history()
    assert isinstance(rows, list)
    if rows:
        assert "factor_name" in rows[0]
        assert "ic" in rows[0]
        assert "ir" in rows[0]
        assert "eval_date" in rows[0]


def test_group_by_run_groups_by_eval_date():
    """US-010 AC2: group_by_run 按 eval_date 分组"""
    from check_ic_decay import load_history, group_by_run
    rows = load_history()
    runs = group_by_run(rows)
    assert len(runs) >= 1
    # 每次跑至少 27 因子
    for run in runs:
        assert len(run) >= 27


def test_detect_decay_with_no_change():
    """US-010 AC3: detect_decay 在 IC 无变化时不报警"""
    from check_ic_decay import detect_decay
    current = [{"factor_name": "F1", "ic": 0.05, "ir": 1.0, "eval_date": "2026-06-21", "benchmark": "510300"}]
    previous = [{"factor_name": "F1", "ic": 0.05, "ir": 1.0, "eval_date": "2026-03-21", "benchmark": "510300"}]
    decayed = detect_decay(current, previous, delta_threshold=0.03, ir_threshold=0.5)
    assert decayed == []


def test_detect_decay_with_large_delta():
    """US-010 AC4: detect_decay 在 |ΔIC| > 0.03 时报警"""
    from check_ic_decay import detect_decay
    current = [{"factor_name": "F1", "ic": 0.10, "ir": 1.0, "eval_date": "2026-06-21", "benchmark": "510300"}]
    previous = [{"factor_name": "F1", "ic": 0.05, "ir": 1.0, "eval_date": "2026-03-21", "benchmark": "510300"}]
    decayed = detect_decay(current, previous, delta_threshold=0.03, ir_threshold=0.5)
    assert len(decayed) == 1
    assert decayed[0]["factor_name"] == "F1"
    assert decayed[0]["ic_decay_alert"] is True
    assert "|ΔIC|" in decayed[0]["alert_reasons"][0]


def test_detect_decay_with_low_ir():
    """US-010 AC5: detect_decay 在 |IR| < 0.5 时报警"""
    from check_ic_decay import detect_decay
    current = [{"factor_name": "F1", "ic": 0.05, "ir": 0.3, "eval_date": "2026-06-21", "benchmark": "510300"}]
    previous = [{"factor_name": "F1", "ic": 0.05, "ir": 1.0, "eval_date": "2026-03-21", "benchmark": "510300"}]
    decayed = detect_decay(current, previous, delta_threshold=0.03, ir_threshold=0.5)
    assert len(decayed) == 1
    assert "|IR|" in decayed[0]["alert_reasons"][0]


def test_generate_report_with_decay():
    """US-010 AC6: generate_report 输出 Markdown 报告"""
    from check_ic_decay import generate_report
    decayed = [{
        "factor_name": "F1", "old_ic": 0.10, "new_ic": 0.05, "delta_ic": -0.05,
        "old_ir": 1.0, "new_ir": 0.3, "ic_decay_alert": True,
        "alert_reasons": ["|ΔIC|=0.0500 > 0.03", "|IR|=0.3000 < 0.5"],
    }]
    current = [{"factor_name": "F1", "ic": 0.05, "ir": 0.3, "eval_date": "2026-06-21", "benchmark": "510300"}]
    previous = [{"factor_name": "F1", "ic": 0.10, "ir": 1.0, "eval_date": "2026-03-21", "benchmark": "510300"}]
    report = generate_report(decayed, current, previous)
    assert "# 季度 IC 巡检报告" in report
    assert "F1" in report
    assert "|ΔIC|=0.0500" in report
    assert "## ⚠️ 衰减因子" in report


def test_check_ic_decay_script_runs():
    """US-010 AC7: check_ic_decay.py 实际可跑（端到端）"""
    if not HISTORY_CSV.exists():
        pytest.skip("history CSV 不存在")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--report-only"],
        capture_output=True, text=True, timeout=30,
        cwd=str(PROJECT_ROOT),
    )
    assert r.returncode in (0, 1, 2), f"check_ic_decay.py exit={r.returncode}, stderr={r.stderr[:200]}"
    # 报告生成
    reports = list(REPORTS_DIR.glob("ic_decay_*.md"))
    assert len(reports) >= 1, f"reports/ic_decay_*.md 不存在"
    # 最近一份报告含概况
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    content = latest.read_text()
    assert "# 季度 IC 巡检报告" in content
