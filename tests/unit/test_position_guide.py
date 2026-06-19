"""
test_position_guide.py — PositionGuide 22 字段 + 9 步决策树测试

按用户原话'完整测试'+ 业务层零 SQL 验证。
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def temp_db_with_position(tmp_path):
    """临时 DB + 建表 + 插入持仓。"""
    db_path = tmp_path / "etf.db"
    schema_dir = _SRC.parent / "schema" / "migrations"
    sql_files = sorted(schema_dir.glob("00[0-9]_*.sql"))
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    for sql_path in sql_files:
        sql = sql_path.read_text(encoding="utf-8")
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass
    conn.commit()
    conn.close()
    # 插入 etf_names（外键）
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO etf_names (code, name, tradable) VALUES (?, ?, 1)",
        ("510300", "沪深300ETF"),
    )
    conn.execute(
        "INSERT INTO etf_names (code, name, tradable) VALUES (?, ?, 1)",
        ("512170", "医疗ETF"),
    )
    conn.commit()
    conn.close()
    # 插入持仓（10 天前建仓 + 5% 浮盈）
    entry_date = (date.today() - timedelta(days=10)).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO positions (code, name, entry_date, entry_price, quantity, current_price, pnl_pct, hold_days, status, score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("510300", "沪深300ETF", entry_date, 4.0, 1000, 4.2, 0.05, 10, "HOLDING", 85),
    )
    conn.execute(
        "INSERT INTO positions (code, name, entry_date, entry_price, quantity, current_price, pnl_pct, hold_days, status, score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("512170", "医疗ETF", entry_date, 0.5, 1000, 0.48, -0.04, 10, "HOLDING", 60),
    )
    conn.commit()
    conn.close()
    return str(db_path)


class TestPositionGuideAnalyzer:
    """PositionGuide 22 字段 + 9 步决策树测试。"""

    def test_22_fields_present(self, temp_db_with_position):
        """22 字段全部存在。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up", current_score=85,
        )
        assert guide is not None
        # 现状 (5)
        assert hasattr(guide, "code")
        assert hasattr(guide, "name")
        assert hasattr(guide, "quantity")
        assert hasattr(guide, "entry_price")
        assert hasattr(guide, "current_price")
        # 衍生 (5)
        assert hasattr(guide, "pnl_pct")
        assert hasattr(guide, "hold_days")
        assert hasattr(guide, "stop_loss_price")
        assert hasattr(guide, "take_profit_price")
        assert hasattr(guide, "expire_in_days")
        # 阈值 (2)
        assert hasattr(guide, "min_hold_remaining")
        assert hasattr(guide, "stop_loss_pct")
        # 信号 (3)
        assert hasattr(guide, "market_regime")
        assert hasattr(guide, "current_score")
        assert hasattr(guide, "emotion_flag")
        # 触发 (3)
        assert hasattr(guide, "should_stop_loss")
        assert hasattr(guide, "should_take_profit")
        assert hasattr(guide, "should_expire")
        # 多持仓 (3)
        assert hasattr(guide, "should_add_position")
        assert hasattr(guide, "should_reduce_position")
        assert hasattr(guide, "should_go_cash")
        # 建议 (1)
        assert hasattr(guide, "action")
        assert hasattr(guide, "reason")
        # 22 个字段
        attrs = [a for a in dir(guide) if not a.startswith("_")]
        assert len(attrs) >= 22

    def test_zero_sqlite3_in_business(self, temp_db_with_position):
        """v2 规则 15：业务层零 sqlite3。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        import inspect, re
        src = inspect.getsource(PositionGuideAnalyzer)
        sqlite_uses = re.findall(r"sqlite3\.\w+|import sqlite3", src)
        assert len(sqlite_uses) == 0, f"业务层禁止 sqlite3: {sqlite_uses}"

    def test_step1_legacy_holding_clear(self, temp_db_with_position):
        """Step 1: legacy_holding=1 → CLEAR_LEGACY。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        # 改 legacy_holding=1
        conn = sqlite3.connect(temp_db_with_position)
        conn.execute("UPDATE positions SET legacy_holding=1 WHERE code='510300'")
        conn.commit()
        conn.close()
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up",
        )
        assert guide.action == "CLEAR_LEGACY"

    def test_step2_stop_loss_trigger(self, temp_db_with_position):
        """Step 2: 价格 <= stop_loss → STOP_LOSS。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        # entry 4.0, stop_loss -10% = 3.6, current 3.5 → 触发
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=3.5, market_regime="trend_up",
        )
        assert guide.should_stop_loss is True
        assert guide.action == "STOP_LOSS"

    def test_step3_hold_short(self, temp_db_with_position):
        """Step 3: hold_days < min_hold → HOLD_SHORT。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        # 改 entry_date 为 1 天前
        entry_date = (date.today() - timedelta(days=1)).isoformat()
        conn = sqlite3.connect(temp_db_with_position)
        conn.execute(
            "UPDATE positions SET entry_date = ?, hold_days = ? WHERE code = '510300'",
            (entry_date, 1),
        )
        conn.commit()
        conn.close()
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up",
        )
        assert guide.action == "HOLD_SHORT"

    def test_step4_take_profit_trigger(self, temp_db_with_position):
        """Step 4: hold >= min_hold + price >= take_profit → TAKE_PROFIT。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        # hold 10 天, take_profit +15% = 4.6, current 4.7 → 触发
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.7, market_regime="trend_up",
        )
        assert guide.should_take_profit is True
        assert guide.action == "TAKE_PROFIT"

    def test_step5_expire(self, temp_db_with_position):
        """Step 5: hold >= max_hold → EXPIRE_REVIEW。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        # 改 entry_date 为 20 天前（> max_hold 15）
        entry_date = (date.today() - timedelta(days=20)).isoformat()
        conn = sqlite3.connect(temp_db_with_position)
        conn.execute(
            "UPDATE positions SET entry_date = ?, hold_days = ? WHERE code = '510300'",
            (entry_date, 20),
        )
        conn.commit()
        conn.close()
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up",
        )
        assert guide.should_expire is True
        assert guide.action == "EXPIRE_REVIEW"

    def test_step6_market_go_cash(self, temp_db_with_position):
        """Step 6: market_regime = trend_down → GO_CASH。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_down",
        )
        assert guide.action == "GO_CASH"

    def test_step7_default_hold_with_high_score(self, temp_db_with_position):
        """Step 9 默认：hold + score>=80 → should_add_position=True。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up",
            current_score=85,
        )
        assert guide.action == "HOLD"
        assert guide.should_add_position is True

    def test_step8_default_hold_with_low_score(self, temp_db_with_position):
        """Step 9 默认：hold + score<50 → should_reduce_position=True。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(
            code="510300", current_price=4.2, market_regime="trend_up",
            current_score=40,
        )
        assert guide.should_reduce_position is True

    def test_default_parameters_align_v8(self):
        """默认参数对齐 v8 POSITION_MANAGEMENT.md。"""
        from etf_quant.risk.position_guide import (
            DEFAULT_STOP_LOSS_PCT, DEFAULT_TAKE_PROFIT_PCT,
            DEFAULT_MIN_HOLD_DAYS, DEFAULT_MAX_HOLD_DAYS, DEFAULT_MAX_HOLDINGS,
        )
        assert DEFAULT_STOP_LOSS_PCT == -0.10
        assert DEFAULT_TAKE_PROFIT_PCT == 0.15
        assert DEFAULT_MIN_HOLD_DAYS == 3
        assert DEFAULT_MAX_HOLD_DAYS == 15
        assert DEFAULT_MAX_HOLDINGS == 2  # v8 + 用户 B 决策

    def test_analyze_all_holdings(self, temp_db_with_position):
        """analyze_all 返回所有 HOLDING 持仓的 guide。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        # 2 只 HOLDING（510300 + 512170）
        guides = analyzer.analyze_all(current_prices={}, market_regime="range_bound")
        assert len(guides) == 2
        codes = {g.code for g in guides}
        assert "510300" in codes
        assert "512170" in codes

    def test_no_position_returns_none(self, temp_db_with_position):
        """无持仓时返回 None。"""
        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=temp_db_with_position)
        guide = analyzer.analyze_position(code="999999", current_price=1.0)
        assert guide is None
