"""
tests/unit/alpha/test_factor_legacy_migration.py — US-002 M6/S2 迁移测试

按规则 21：业务数据删除前确认"数据 vs 角色"（标记角色，保留迁移路径）
按规则 20：行为变化类重构必须同步更新测试
按规则 23：分析数据时先看 is_real 字段（state 可能被 onboard 跑污染）

总计：6 测试（不依赖 alpha_state.json 实际内容）
"""
from __future__ import annotations

import pytest

from etf_quant.alpha.factors import (
    FACTOR_REGISTRY,
    LEGACY_FACTOR_MAP,
    migrate_legacy_factor_name,
)


def test_m6_macd_diff_removed_from_registry():
    """US-002 AC: M6_macd_diff 已删除（公式与 T1_macd_bar 完全重复）"""
    assert "M6_macd_diff" not in FACTOR_REGISTRY
    assert "M6_macd_diff" in LEGACY_FACTOR_MAP  # 但在 legacy 映射里
    assert LEGACY_FACTOR_MAP["M6_macd_diff"] == "T1_macd_bar"


def test_s2_adx_renamed_to_s2_adx_strength():
    """US-002 AC: S2_adx 改名 S2_adx_strength（区别于 T4_adx_trend）"""
    assert "S2_adx" not in FACTOR_REGISTRY
    assert "S2_adx_strength" in FACTOR_REGISTRY
    assert "S2_adx" in LEGACY_FACTOR_MAP
    assert LEGACY_FACTOR_MAP["S2_adx"] == "S2_adx_strength"


def test_migrate_legacy_factor_name_function():
    """US-002 AC: migrate_legacy_factor_name 正确转换"""
    assert migrate_legacy_factor_name("M6_macd_diff") == "T1_macd_bar"
    assert migrate_legacy_factor_name("S2_adx") == "S2_adx_strength"
    # 未在 legacy 表里的因子名原样返回
    assert migrate_legacy_factor_name("T5_ma5") == "T5_ma5"
    assert migrate_legacy_factor_name("M4_rsi") == "M4_rsi"
    # 未知名也原样返回（不抛错）
    assert migrate_legacy_factor_name("UNKNOWN_FACTOR") == "UNKNOWN_FACTOR"


def test_27_factors_after_us002():
    """US-002 AC: 27 因子 (US-001 加 T5 → 28，US-002 删 M6 → 27)"""
    assert len(FACTOR_REGISTRY) == 27
    # 验证 S2 是 strength 版
    from etf_quant.alpha.factors import get_factor
    s2 = get_factor("S2_adx_strength")
    assert s2.name == "S2_adx_strength"


def test_legacy_map_migrates_8_user_factors():
    """US-002 AC: 散户 8 因子（T5/B1/W2/M4/V2/V3/W1/R1）迁移后等价（不触发 legacy）"""
    user_8 = ["T5_ma5", "B1_boll_upper", "W2_boll_width", "M4_rsi",
              "V2_obv", "V3_maobv", "W1_atr", "R1_relative"]
    for old_name in user_8:
        new_name = migrate_legacy_factor_name(old_name)
        # 散户 8 因子都不在 legacy 列表里，应该原样返回
        assert new_name == old_name, f"散户因子 {old_name} 不应被迁移"
        # 且仍必须在 FACTOR_REGISTRY
        assert new_name in FACTOR_REGISTRY, f"散户因子 {new_name} 不在 registry"


def test_legacy_map_contains_only_documented_changes():
    """US-002 防御性: LEGACY_FACTOR_MAP 只能含 US-002 改动的两项"""
    expected_keys = {"M6_macd_diff", "S2_adx"}
    actual_keys = set(LEGACY_FACTOR_MAP.keys())
    assert actual_keys == expected_keys, f"legacy 映射有意外 key: {actual_keys}"
