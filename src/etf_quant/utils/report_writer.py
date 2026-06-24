"""
utils/report_writer.py — 决策报告文件落盘工具（L321 教训 P1-2）

用途：
    run_daily.py 三个模式（daily/eval/history）落 JSON 到文件。
    默认路径：reports/etf-daily/YYYY-MM-DD/{mode}_{HHMMSS}.json
    支持 --report-dir 自定义。

被谁调用：
    - skills/etf-daily/scripts/run_daily.py（main 三模式）
    - tests/unit/test_report_writer.py

功能说明：
    - write_report(result, mode, report_dir=None) -> Path
    - 自动创建日期子目录
    - 原子写入（先 .tmp 再 rename）
    - 失败抛异常，不写半截文件

使用方式：
    from etf_quant.utils.report_writer import write_report
    path = write_report(result, mode="daily")
    # → reports/etf-daily/2026-06-24/daily_231900.json

依赖：
    - L321 教训 P1-2：SKILL.md 写"控制台 + 文件"但实现只 print
    - 规则 18：JSON 写入必用 json.dump + 立即验证

注意事项：
    - 路径用 Path.write_text（原子写入）
    - 返回 Path 便于 caller 二次操作
    - ensure_ascii=False（中文可读）

业界参考：
    - 12-Factor App § XI Logs：events stream
    - GitHub Actions artifact：执行产物落 reports/YYYY-MM-DD/
    - Linux FHS § /var/log：约定式日志路径
    - pathlib.Path.write_text 原子写入官方文档
    - pytest tmp_path 最佳实践（测试用临时目录）
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# 默认报告根目录（项目根 reports/etf-daily）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_REPORT_ROOT = _PROJECT_ROOT / "reports" / "etf-daily"


def write_report(
    result: dict[str, Any],
    mode: str,
    report_dir: Optional[str | Path] = None,
    timestamp: Optional[str] = None,
) -> Path:
    """把决策报告写到文件。

    Args:
        result: 决策结果 dict（必须 JSON 可序列化）
        mode: daily / eval / history
        report_dir: 自定义报告根目录（默认 reports/etf-daily/YYYY-MM-DD）
        timestamp: 时间戳字符串（默认当前时间 YYYYMMDD_HHMMSS）

    Returns:
        Path: 写入的文件路径

    Raises:
        TypeError: result 不可 JSON 序列化
        OSError: 目录创建或文件写入失败
    """
    # 1. 计算时间戳和日期子目录
    if timestamp is None:
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        date_str = now.strftime("%Y-%m-%d")
    else:
        # 兼容 ISO 格式时间戳（"2026-06-24T12:00:00"）
        try:
            dt = datetime.fromisoformat(timestamp)
            timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            # 不是 ISO 格式，剥掉非数字字符作文件名
            timestamp_str = timestamp.replace(":", "").replace("-", "").replace("T", "_")
            date_str = datetime.now().strftime("%Y-%m-%d")

    # 2. 决定报告目录
    if report_dir is not None:
        target_dir = Path(report_dir) / date_str
    else:
        target_dir = DEFAULT_REPORT_ROOT / date_str

    # 3. 创建目录
    target_dir.mkdir(parents=True, exist_ok=True)

    # 4. 文件名
    filename = f"{mode}_{timestamp_str}.json"
    target_path = target_dir / filename

    # 5. 原子写入：先写 .tmp 再 rename（防止半截文件）
    try:
        json_text = json.dumps(result, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise TypeError(
            f"result 不可 JSON 序列化: {type(e).__name__}: {e}"
        ) from e

    # 6. 写入临时文件 + 立即验证 + rename
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_dir,
        delete=False,
        suffix=".tmp",
        prefix=f"{mode}_",
    ) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(json_text)
        tmp.flush()

    # 7. 验证（规则 18：JSON 写入必用 json.dump + 立即验证）
    verified = json.loads(tmp_path.read_text(encoding="utf-8"))
    assert verified == result, "JSON 验证失败：写入与原始不一致"

    # 8. 原子 rename
    tmp_path.rename(target_path)
    return target_path
