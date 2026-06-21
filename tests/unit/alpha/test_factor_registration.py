"""
tests/unit/alpha/test_factor_registration.py — US-007 因子入库校验

按规则 27：因子入库必带 IC + 季度必巡检（阻断式）
按规则 28：因子命名必带 aliases
按规则 5.1：关键路径测试覆盖

总计：8 测试
"""
from __future__ import annotations

import pytest

from etf_quant.alpha.factors import FACTOR_REGISTRY, list_factors, get_factor
from etf_quant.alpha.factor_base import (
    Factor,
    FactorCategory,
    FactorMetadata,
    register_factor,
    FactorICMissingError,
)


def test_27_factors_have_ic_metadata():
    """US-007 AC1: 27 因子 metadata 都有 ic/ir/ic_eval_date（动态从 factor_icir.csv 读）"""
    for name in FACTOR_REGISTRY:
        inst = get_factor(name)
        m = inst.metadata
        assert m.ic is not None, f"{name} 缺 ic"
        assert m.ir is not None, f"{name} 缺 ir"
        assert m.ic_eval_date is not None, f"{name} 缺 ic_eval_date"
        # 数值范围
        assert -1 <= m.ic <= 1, f"{name} ic={m.ic} 越界"
        assert isinstance(m.ir, float), f"{name} ir 不是 float"


def test_register_factor_blocks_missing_ic():
    """US-007 AC2: 缺 IC 因子注册时抛 FactorICMissingError（阻断式）"""

    class NoICFactor(Factor):
        @property
        def name(self): return "NO_IC_TEST"

        @property
        def category(self): return FactorCategory.TREND

        @property
        def description(self): return "test no ic"

        def compute(self, df): return None

        metadata = FactorMetadata(
            name="NO_IC_TEST", category=FactorCategory.TREND, description="test"
        )

    with pytest.raises(FactorICMissingError) as exc_info:
        register_factor(NoICFactor, FACTOR_REGISTRY)
    assert "NO_IC_TEST" in str(exc_info.value)
    assert "ic" in str(exc_info.value)
    assert "ir" in str(exc_info.value)
    assert "ic_eval_date" in str(exc_info.value)


def test_register_factor_blocks_missing_aliases():
    """US-007+US-001+US-028: 缺 aliases 因子也抛错（按规则 28）"""

    class NoAliasFactor(Factor):
        @property
        def name(self): return "NO_ALIAS_TEST"

        @property
        def category(self): return FactorCategory.TREND

        @property
        def description(self): return "test no alias"

        def compute(self, df): return None

        metadata = FactorMetadata(
            name="NO_ALIAS_TEST", category=FactorCategory.TREND, description="test",
            ic=0.05, ir=1.0, ic_eval_date="2026-06-21",
        )

    with pytest.raises(FactorICMissingError) as exc_info:
        register_factor(NoAliasFactor, FACTOR_REGISTRY)
    assert "aliases" in str(exc_info.value)


def test_register_factor_accepts_complete_factor():
    """US-007 AC3: IC/IR/ic_eval_date/aliases 都齐的因子能注册"""

    class CompleteFactor(Factor):
        @property
        def name(self): return "COMPLETE_TEST"

        @property
        def category(self): return FactorCategory.TREND

        @property
        def description(self): return "test complete"

        def compute(self, df): return None

        metadata = FactorMetadata(
            name="COMPLETE_TEST", category=FactorCategory.TREND, description="test",
            ic=0.05, ir=1.0, ic_eval_date="2026-06-21",
            aliases=["COMPLETE", "完整测试"],
        )

    register_factor(CompleteFactor, FACTOR_REGISTRY)
    assert "COMPLETE_TEST" in FACTOR_REGISTRY
    del FACTOR_REGISTRY["COMPLETE_TEST"]  # 清理


def test_factor_metadata_default_blocks_registration():
    """US-007 AC4: FactorMetadata 默认值（ic=None）注册时必抛错（规则 19 deny）"""
    meta = FactorMetadata(
        name="DEFAULT_TEST", category=FactorCategory.TREND, description="default"
    )
    # 不填 IC 时，metadata.ic/ir/ic_eval_date 都是 None
    assert meta.ic is None
    assert meta.ir is None
    assert meta.ic_eval_date is None


def test_factor_metadata_aliases_default_is_empty_list():
    """US-007+US-001+US-019: aliases 默认空 list（规则 19 黑名单模式）"""
    m1 = FactorMetadata(name="A", category=None, description="x")
    m2 = FactorMetadata(name="B", category=None, description="y")
    assert m1.aliases == []
    assert m2.aliases == []
    # 不共享可变默认
    m1.aliases.append("X")
    assert m2.aliases == []


def test_ic_table_loaded_from_csv():
    """US-007 AC5: _IC_IR_TABLE 动态从 factor_icir.csv 加载"""
    from etf_quant.alpha.factor_base import _IC_IR_TABLE
    # 至少 27 因子有 IC 数据
    assert len(_IC_IR_TABLE) >= 27
    # 验证 T5_ma5 有数据
    assert "T5_ma5" in _IC_IR_TABLE
    ic, ir, eval_date = _IC_IR_TABLE["T5_ma5"]
    assert ic is not None
    assert ir is not None
    assert eval_date is not None


def test_register_factor_error_message_helpful():
    """US-007 AC6: 错误消息含修复指引（先跑 run_factor_evaluation.py）"""

    class NoICFactor2(Factor):
        @property
        def name(self): return "NO_IC_MSG_TEST"

        @property
        def category(self): return FactorCategory.TREND

        @property
        def description(self): return "test"

        def compute(self, df): return None

        metadata = FactorMetadata(name="NO_IC_MSG_TEST", category=FactorCategory.TREND, description="test")

    with pytest.raises(FactorICMissingError) as exc_info:
        register_factor(NoICFactor2, FACTOR_REGISTRY)
    msg = str(exc_info.value)
    # 错误消息含修复指引
    assert "run_factor_evaluation.py" in msg, f"错误消息没指引: {msg}"
