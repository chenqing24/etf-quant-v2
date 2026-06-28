"""
tests/unit/alpha/test_factor_set.py — FactorSet 单测

覆盖：
    - 池存在性校验（未知因子报错）
    - 非空校验
    - 去重（保持顺序）
    - 8 因子 v2 子集
    - 全 27 因子子集
"""
import pytest

from etf_quant.alpha.factor_set import FactorSet
from etf_quant.alpha.factors import FACTOR_REGISTRY


def test_eight_factor_v2_basic():
    """D-004 + D-013.1 精选 8 因子 v2 子集：8 因子全在 registry + 名称正确"""
    fs = FactorSet.eight_factor_v2()
    assert fs.name == "eight_factor_v2"
    assert len(fs) == 8  # D-013.1: 27+T6/T7 → 8 因子都在 registry
    assert "W2_boll_width" in fs
    assert "M2_momentum_5d" in fs
    assert "T6_dma" in fs  # D-013.1 新增
    assert "T7_ma_arrangement" in fs  # D-013.1 新增


def test_all_registered_count():
    """全 29 因子子集：覆盖 FACTOR_REGISTRY 全部（D-013.1：27+T6/T7）"""
    fs = FactorSet.all_registered()
    assert len(fs) == 29
    assert set(fs.factor_names) == set(FACTOR_REGISTRY.keys())


def test_unknown_factor_raises():
    """未知因子必须报错（不允许静默）"""
    with pytest.raises(ValueError, match="包含未知因子"):
        FactorSet(name="bad", factor_names=("W2_boll_width", "FAKE_FACTOR"))


def test_empty_set_raises():
    """空集必须报错"""
    with pytest.raises(ValueError, match="不能为空集"):
        FactorSet(name="empty", factor_names=())


def test_dedup_preserves_order():
    """重复因子自动去重（保持首次出现顺序）"""
    fs = FactorSet(
        name="dup",
        factor_names=("W2_boll_width", "M4_rsi", "W2_boll_width", "V2_obv"),
    )
    assert len(fs) == 3
    assert list(fs.factor_names) == ["W2_boll_width", "M4_rsi", "V2_obv"]


def test_iter():
    """支持迭代"""
    fs = FactorSet.eight_factor_v2()
    names = list(fs)
    assert names == list(fs.factor_names)


def test_contains():
    """支持 in 操作"""
    fs = FactorSet.eight_factor_v2()
    assert "W2_boll_width" in fs
    assert "FAKE_FACTOR" not in fs


def test_get_factor_classes():
    """get_factor_classes 返回 Factor class"""
    fs = FactorSet.eight_factor_v2()
    classes = fs.get_factor_classes()
    assert len(classes) == len(fs)
    assert classes["W2_boll_width"] is FACTOR_REGISTRY["W2_boll_width"]


def test_to_from_dict_roundtrip():
    """to_dict / from_dict 往返一致"""
    fs = FactorSet.eight_factor_v2()
    data = fs.to_dict()
    fs2 = FactorSet.from_dict(data)
    assert fs.name == fs2.name
    assert list(fs.factor_names) == list(fs2.factor_names)


def test_frozen():
    """frozen=True 不允许直接赋值"""
    fs = FactorSet.eight_factor_v2()
    with pytest.raises(Exception):  # FrozenInstanceError 或 AttributeError
        fs.name = "new_name"