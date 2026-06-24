"""
test_report_writer.py — 报告落盘工具单元测试（L321 教训 P1-2）

修复前：run_daily.py 只 print JSON 不写文件
修复后：调 write_report() 落 reports/etf-daily/YYYY-MM-DD/{mode}_{HHMMSS}.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestWriteReport:
    """L321 教训 P1-2 核心：写文件 + 原子性 + 中文支持"""

    def test_write_creates_file(self, tmp_path):
        from etf_quant.utils.report_writer import write_report
        result = {"decision": "HOLD", "code": "512170"}
        path = write_report(result, mode="daily", report_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".json"
        assert "daily_" in path.name

    def test_write_atomic_no_partial_file(self, tmp_path):
        """原子写入：失败时不留 .tmp 半截文件"""
        from etf_quant.utils.report_writer import write_report
        result = {"decision": "BUY", "count": 5}
        path = write_report(result, mode="eval", report_dir=tmp_path)
        # 不应有 .tmp 后缀的临时文件
        tmp_files = list(tmp_path.rglob("*.tmp"))
        assert tmp_files == [], f"残留 .tmp 文件: {tmp_files}"
        # 应只有 .json 文件
        json_files = list(tmp_path.rglob("*.json"))
        assert len(json_files) == 1
        assert json_files[0] == path

    def test_write_creates_date_subdir(self, tmp_path):
        """自动创建 YYYY-MM-DD 子目录"""
        from etf_quant.utils.report_writer import write_report
        result = {"x": 1}
        path = write_report(result, mode="daily", report_dir=tmp_path)
        # 父目录应是日期格式
        date_part = path.parent.name
        # 验证 YYYY-MM-DD 格式
        try:
            datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"日期子目录格式错: {date_part}")

    def test_write_chinese_preserved(self, tmp_path):
        """中文不转义（ensure_ascii=False）"""
        from etf_quant.utils.report_writer import write_report
        result = {"reason": "崩盘市，清仓避险", "code": "512170"}
        path = write_report(result, mode="daily", report_dir=tmp_path)
        text = path.read_text(encoding="utf-8")
        assert "崩盘市" in text
        assert "\\u" not in text  # ensure_ascii=False

    def test_write_json_validation(self, tmp_path):
        """规则 18：JSON 写入必立即验证（写入与原始一致）"""
        from etf_quant.utils.report_writer import write_report
        result = {"a": [1, 2, 3], "b": {"nested": True}}
        path = write_report(result, mode="history", report_dir=tmp_path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded == result

    def test_write_rejects_non_serializable(self, tmp_path):
        """不可序列化数据应抛 TypeError，不写半截 .json 文件"""
        from etf_quant.utils.report_writer import write_report
        # set 不可 JSON 序列化
        bad = {"x": {1, 2, 3}}
        with pytest.raises(TypeError) as exc_info:
            write_report(bad, mode="daily", report_dir=tmp_path)
        assert "JSON" in str(exc_info.value) or "serialize" in str(exc_info.value).lower()
        # 不应留任何 .json 文件（空日期目录可接受）
        json_files = list(tmp_path.rglob("*.json"))
        assert json_files == [], f"残留 .json 文件: {json_files}"
        # 不应留 .tmp 文件
        tmp_files = list(tmp_path.rglob("*.tmp"))
        assert tmp_files == [], f"残留 .tmp 文件: {tmp_files}"

    def test_write_uses_provided_timestamp(self, tmp_path):
        """传 ISO timestamp 时文件名同步"""
        from etf_quant.utils.report_writer import write_report
        result = {"x": 1}
        path = write_report(
            result, mode="daily",
            report_dir=tmp_path,
            timestamp="2026-06-24T12:00:00",
        )
        # 文件名应含 20260624_120000
        assert "20260624_120000" in path.name

    def test_write_filename_includes_mode(self, tmp_path):
        """文件名必须含 mode"""
        from etf_quant.utils.report_writer import write_report
        for mode in ("daily", "eval", "history"):
            p = write_report({"x": mode}, mode=mode, report_dir=tmp_path)
            assert p.name.startswith(f"{mode}_")

    def test_default_report_root_is_project_relative(self):
        """默认 report root 是项目根 reports/etf-daily"""
        from etf_quant.utils.report_writer import DEFAULT_REPORT_ROOT
        # 应含 etf-daily 路径段
        assert "etf-daily" in str(DEFAULT_REPORT_ROOT)
        # 必须是绝对路径（锚定项目根，不依赖 cwd）
        assert DEFAULT_REPORT_ROOT.is_absolute()
