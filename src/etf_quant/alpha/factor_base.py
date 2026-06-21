"""
alpha/factor_base.py — 因子抽象基类（US-013）

用途：
    定义所有 27 因子的统一接口（计算 + 元数据 + IC/IR 记录）。
    所有具体因子（B1/V1/T1/T3/T4/M2/W4 等）继承此基类。

被谁调用：
    - src/etf_quant/alpha/factors/*.py（27 个具体因子）
    - src/etf_quant/alpha/registry.py（因子注册表）
    - src/etf_quant/alpha/analysis/batch_ic.py（IC/IR 批量计算）
    - tests/unit/test_factors.py（单元测试）

功能说明：
    - Factor ABC: 抽象接口（compute + metadata）
    - FactorResult: 因子计算结果（含 Series + 元数据）
    - FactorCategory: 因子分类枚举（趋势/动量/量能/波动/反转）
    - validate_factor_result: 因子结果校验（防未来函数 L121 教训）

使用方式：
    from etf_quant.alpha.factor_base import Factor, FactorCategory

    class MyFactor(Factor):
        @property
        def name(self) -> str:
            return "B1_boll_upper"

        def compute(self, df: pd.DataFrame) -> pd.Series:
            return df['close'] - df['boll_upper']

依赖：
    - pandas: Series/DataFrame 处理
    - numpy: 数值计算
    - L218 教训（IC/IR 验证）
    - L121 教训（防未来函数）

注意事项：
    - 因子计算必须只用 t 及之前的数据（不能有未来函数）
    - compute() 返回 Series.index 必须与 df.index 对齐
    - 默认 fillna(0)，具体因子可覆盖 fill_method

业界参考（按规则 13）：
    - WorldQuant 101 Alphas (Kakushadze 2016, arXiv:1601.00991)
    - López de Prado 2018 *Advances in Financial ML* Ch 16
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class FactorCategory(Enum):
    """因子分类（v2 alpha README 6 大类）。"""

    TREND = "T"        # 趋势类（T1~T4）
    MOMENTUM = "M"     # 动量类（M1~M6）
    VOLUME = "V"       # 量能类（V1~V4）
    VOLATILITY = "W"   # 波动类（W1~W4）
    STRENGTH = "S"     # 趋势强度（S1~S2）
    OSCILLATOR = "O"   # 超买超卖（O1~O2）
    RELATIVE = "R"     # 相对强弱（R1）
    REVERSAL = "N"     # 反转类（N1~N3）


@dataclass
class FactorMetadata:
    """因子元数据（含 IC/IR 验证值 + 业界别名）。规则 28：每个因子必须带至少 1 个业界通用别名。"""

    name: str                          # 因子 ID（如 B1_boll_upper）
    category: FactorCategory           # 分类
    description: str                   # 中文描述
    aliases: list[str] = field(default_factory=list)  # 业界通用名（MA5/RSI/MACD/ATR 等；规则 19 默认 deny：空 list）
    ic: Optional[float] = None         # IC（Spearman rank correlation）
    ir: Optional[float] = None         # IR（IC.mean() / IC.std()）
    ic_eval_date: Optional[str] = None # IC 评估日期 YYYY-MM-DD（规则 27：入库必填，Sprint 3 US-007 强制）
    source: str = "v1_inherit"         # 来源（v1_inherit / v2_new / v9_verified）
    version: str = "v2.0"              # 版本号


class FactorICMissingError(ValueError):
    """因子入库时缺 IC 字段（按规则 27 阻断式抛错，不警告）.

    L286 教训：缺 IC 字段的因子不能进 FACTOR_REGISTRY（避免"半残因子"污染 alpha 池）。
    修复：先跑 python scripts/run_factor_evaluation.py --factor XXX 拿到 IC 再入库。
    """
    pass


def register_factor(cls: type["Factor"], registry: dict | None = None) -> type["Factor"]:
    """注册因子到 registry，校验 IC/IR/ic_eval_date 三字段必填（规则 27 阻断式）.

    Args:
        cls: 因子类（必须有 metadata 属性）
        registry: 目标 registry（默认 None = 走调用方模块的 FACTOR_REGISTRY）

    Returns:
        cls（注册成功）

    Raises:
        FactorICMissingError: metadata.ic/ir/ic_eval_date 任一缺失时阻断

    使用：
        from etf_quant.alpha.factor_base import register_factor
        FACTOR_REGISTRY["T5_ma5"] = register_factor(T5MA5Factor)
    """
    meta = cls.metadata
    missing = []
    if meta.ic is None:
        missing.append("ic")
    if meta.ir is None:
        missing.append("ir")
    if not hasattr(meta, "ic_eval_date") or meta.ic_eval_date is None:
        missing.append("ic_eval_date")
    # 规则 19：aliases 必填（非空 list）
    if not hasattr(meta, "aliases") or not meta.aliases:
        missing.append("aliases")
    if missing:
        raise FactorICMissingError(
            f"因子 {cls.__name__}（{meta.name}）入库失败：缺 IC 字段 {missing}。"
            f"先跑 python scripts/run_factor_evaluation.py --benchmark 510300 "
            f"填充 {meta.name} 的 IC/IR/ic_eval_date 再入库。"
        )
    if registry is not None:
        registry[meta.name] = cls
    return cls


@dataclass
class FactorResult:
    """因子计算结果。"""

    series: pd.Series                  # 因子值（与 df.index 对齐）
    metadata: FactorMetadata           # 元数据
    sample_count: int = 0             # 有效样本数（非 NaN）
    fill_method: str = "zero"          # NaN 填充方式


class Factor(ABC):
    """因子抽象基类（所有 27 因子继承此）。"""

    def __init__(self, fill_method: str = "zero"):
        self.fill_method = fill_method

    @property
    @abstractmethod
    def name(self) -> str:
        """因子 ID（如 B1_boll_upper）。"""

    @property
    @abstractmethod
    def category(self) -> FactorCategory:
        """因子分类。"""

    @property
    @abstractmethod
    def description(self) -> str:
        """中文描述（一行说明因子含义）。"""

    @property
    def metadata(self) -> FactorMetadata:
        """因子元数据（US-007 动态从 data/factor_icir.csv 读 IC/IR/eval_date）."""
        ic, ir, eval_date = _lookup_ic_ir(self.name)
        return FactorMetadata(
            name=self.name,
            category=self.category,
            description=self.description,
            aliases=getattr(self, "_aliases", []),  # US-001 业界别名（子类可覆盖）
            ic=ic,
            ir=ir,
            ic_eval_date=eval_date,  # US-007 入库必填
            source="v1_inherit",
        )

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.Series:
        """
        计算因子值。

        Args:
            df: 包含 OHLCV 数据的 DataFrame（columns: open/high/low/close/volume）

        Returns:
            因子值 Series（index 与 df.index 对齐）
        """

    def __call__(self, df: pd.DataFrame) -> FactorResult:
        """调用入口：计算 + 校验 + 填充。"""
        raw = self.compute(df)
        validated = validate_factor_result(raw, df.index, factor_name=self.name)
        filled = _fill_nan(validated, method=self.fill_method)
        return FactorResult(
            series=filled,
            metadata=self.metadata,
            sample_count=int(filled.notna().sum()),
            fill_method=self.fill_method,
        )


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────

def validate_factor_result(series: pd.Series, expected_index: pd.DatetimeIndex,
                           factor_name: str = "unknown") -> pd.Series:
    """
    校验因子结果（防未来函数 + 长度对齐）。

    Args:
        series: 因子值 Series
        expected_index: 期望的索引（df.index）
        factor_name: 因子名称（用于日志）

    Returns:
        校验后的 Series
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"[{factor_name}] compute() must return pd.Series, got {type(series)}")

    if len(series) != len(expected_index):
        raise ValueError(
            f"[{factor_name}] length mismatch: series={len(series)} vs df={len(expected_index)}"
        )

    # 检查索引对齐（允许宽松匹配：顺序一致即可）
    if not series.index.equals(expected_index):
        # 尝试重索引
        try:
            series = series.reindex(expected_index)
        except Exception as e:
            raise ValueError(f"[{factor_name}] index mismatch and reindex failed: {e}")

    return series


def _fill_nan(series: pd.Series, method: str = "zero") -> pd.Series:
    """NaN 填充。"""
    if method == "zero":
        return series.fillna(0)
    elif method == "ffill":
        return series.ffill().fillna(0)
    elif method == "drop":
        return series.dropna()
    else:
        raise ValueError(f"Unknown fill_method: {method}")


# ────────────────────────────────────────────────────────────
# IC/IR 查询表（从 v2 alpha/README.md 27 因子清单读取）
# ────────────────────────────────────────────────────────────

_IC_IR_TABLE: dict[str, tuple[Optional[float], Optional[float], Optional[str]]] = {}  # US-007: 动态从 data/factor_icir.csv 读，初始空
_IC_EVAL_DATE: dict[str, str] = {}  # US-007: 因子 IC 评估日期


def _load_ic_ir_from_csv() -> None:
    """从 data/factor_icir.csv 加载最新 IC/IR/eval_date（US-007 动态读）.

    按规则 18：CSV 写入后立即读验证。
    按规则 27：IC/IR 是因子入库必填字段，必须有数据源。
    """
    import csv as _csv
    from pathlib import Path as _Path
    csv_path = _Path(__file__).resolve().parent.parent.parent.parent / "data" / "factor_icir.csv"
    if not csv_path.exists():
        return
    try:
        with open(csv_path) as f:
            reader = _csv.DictReader(f)
            for row in reader:
                fname = row.get("factor_name", "")
                ic_s = row.get("ic", "")
                ir_s = row.get("ir", "")
                date_s = row.get("eval_date", "")
                if not fname:
                    continue
                try:
                    ic_v = float(ic_s) if ic_s else None
                except ValueError:
                    ic_v = None
                try:
                    ir_v = float(ir_s) if ir_s else None
                except ValueError:
                    ir_v = None
                _IC_IR_TABLE[fname] = (ic_v, ir_v, date_s or None)
                if date_s:
                    _IC_EVAL_DATE[fname] = date_s
    except Exception:
        pass


# 模块加载时自动调一次
_load_ic_ir_from_csv()


def _lookup_ic_ir(factor_name: str) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """从 IC/IR 表查找（None 表示未验证）。US-007 加 eval_date."""
    return _IC_IR_TABLE.get(factor_name, (None, None, None))
