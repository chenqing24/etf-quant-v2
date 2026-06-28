"""
alpha/scoring.py — 横截面打分器（Layer 3 算法层，D-013 设计）

用途：
    跨多只 ETF 的横截面打分（横截面排名 + 加权综合）。
    取代 daily 占位 0.5 和 backtesting 等权硬编码。

被谁调用：
    - skills/etf-daily/scripts/run_daily.py（修复 P0 占位符）
    - src/etf_quant/backtest/backtesting_adapter.py（替换等权）
    - tests/unit/alpha/test_scoring.py（单测）

设计原则（按规则 13 业界参考）：
    - Qlib Alpha158 + handler：横截面打分 pipeline
    - WorldQuant 101 Alphas (Kakushadze 2016)：rank + composite 模式
    - scipy.stats.rankdata 官方文档：横截面排名（ascending vs descending）

Pipeline (3 Layer)：
    Layer 1: compute（按 FactorSet，不浪费算力）
    Layer 2: rank normalize（横截面排名 → [0, 1]）
    Layer 3: weighted composite（D-004 权重）

重要约束：
    - DMA / FIB 当前不在 FACTOR_REGISTRY（D-013 后续补），暂不在 Scorer 处理
    - 数据缺失（NaN）→ composite = NaN → 排除候选
    - 因子 compute 抛错 → 单独 try-except，记录 warning，跳过该因子
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from etf_quant.alpha.factor_set import FactorSet
from etf_quant.alpha.weight_scheme import WeightScheme

logger = logging.getLogger(__name__)


@dataclass
class ScoringResult:
    """打分结果（含警告，方便调用方诊断）"""

    scores: dict[str, float]                  # {code: composite_score ∈ [0, 1]}
    rank_details: dict[str, dict[str, float]]  # {code: {factor: rank}}
    warnings: list[str]

    def top_k(self, k: int) -> list[tuple[str, float]]:
        """返回 top-k（按 score 降序），跳过 NaN。"""
        valid = [(c, s) for c, s in self.scores.items() if not np.isnan(s)]
        return sorted(valid, key=lambda x: -x[1])[:k]

    def has_data(self) -> bool:
        """是否至少有一个有效 score（不是空结果）"""
        return any(not np.isnan(s) for s in self.scores.values())


class CrossSectionalScorer:
    """横截面打分器（D-013 P0 修复）。

    Attributes:
        factor_set: 因子子集（从 FACTOR_REGISTRY 选）
        weight_scheme: 权重方案（D-004 已确定）

    Example:
        >>> scorer = CrossSectionalScorer.default_v2()
        >>> result = scorer.score("trend_up", {"510300": df1, "515050": df2})
        >>> result.top_k(5)
        [('515050', 0.85), ('510300', 0.42), ...]
    """

    def __init__(self, factor_set: FactorSet, weight_scheme: WeightScheme):
        self.factor_set = factor_set
        self.weight_scheme = weight_scheme

        # 校验：factor_set 的因子必须在 weight_scheme 中有权重
        # （避免 weight_scheme 引用了不在 factor_set 的因子）
        scheme_factors = weight_scheme.factor_names()
        fs_factors = set(factor_set.factor_names)
        missing_in_scheme = fs_factors - scheme_factors
        if missing_in_scheme:
            raise ValueError(
                f"FactorSet 因子 {missing_in_scheme} 在 WeightScheme 中无权重。"
                f"请确保 FactorSet ⊆ WeightScheme.factor_names()"
            )

    def score(
        self,
        market_mode: str,
        factor_data: dict[str, pd.DataFrame],
    ) -> ScoringResult:
        """横截面打分（Pipeline 3 Layer）。

        Args:
            market_mode: "trend_up" / "range_bound"
            factor_data: {code: OHLCV DataFrame}（日线，含 close/volume 等）

        Returns:
            ScoringResult（scores + rank_details + warnings）
            若数据全缺失 → scores 全 NaN + warnings 提示
        """
        weights = self.weight_scheme.get_weights(market_mode)
        warnings: list[str] = []

        # 空数据快速返回
        if not factor_data:
            return ScoringResult(
                scores={},
                rank_details={},
                warnings=["factor_data 为空"],
            )

        # Layer 1: compute（按 FactorSet）
        raw = self._layer1_compute(factor_data, warnings)

        if not raw:
            return ScoringResult(
                scores={code: float("nan") for code in factor_data},
                rank_details={code: {} for code in factor_data},
                warnings=warnings + ["所有因子 compute 失败"],
            )

        # Layer 2: rank normalize（横截面）
        rank_details = self._layer2_rank(raw, warnings)

        # Layer 3: weighted composite
        scores = self._layer3_composite(rank_details, weights, warnings)

        return ScoringResult(scores=scores, rank_details=rank_details, warnings=warnings)

    def _layer1_compute(
        self,
        factor_data: dict[str, pd.DataFrame],
        warnings: list[str],
    ) -> dict[str, dict[str, float]]:
        """Layer 1: 计算每个 (code, factor) 的最新值。

        Returns:
            {code: {factor_name: latest_value}}
        """
        from etf_quant.alpha.factors import FACTOR_REGISTRY

        raw: dict[str, dict[str, float]] = {}
        for code, df in factor_data.items():
            raw[code] = {}
            if df is None or df.empty:
                warnings.append(f"{code}: 数据为空")
                continue
            for fname in self.factor_set.factor_names:
                try:
                    factor_cls = FACTOR_REGISTRY[fname]
                    series = factor_cls().compute(df)
                    if series is None or series.empty:
                        warnings.append(f"{code} / {fname}: compute 返回空")
                        continue
                    # 取最新非 NaN 值
                    last_valid = series.dropna()
                    if last_valid.empty:
                        warnings.append(f"{code} / {fname}: 全 NaN")
                        continue
                    raw[code][fname] = float(last_valid.iloc[-1])
                except Exception as e:
                    warnings.append(
                        f"{code} / {fname}: compute 失败 ({type(e).__name__}: {str(e)[:80]})"
                    )
        return raw

    def _layer2_rank(
        self,
        raw: dict[str, dict[str, float]],
        warnings: list[str],
    ) -> dict[str, dict[str, float]]:
        """Layer 2: 横截面 rank 归一化到 [0, 1]。

        Returns:
            {code: {factor_name: rank ∈ [0, 1]}}
            rank=1 = 该因子横截面最高值，rank=0 = 最低
            NaN = 该 ETF 该因子无值
        """
        if not raw:
            return {}

        # 收集所有 factor
        all_factors = set()
        for factors in raw.values():
            all_factors.update(factors.keys())

        rank_details: dict[str, dict[str, float]] = {code: {} for code in raw}

        for fname in all_factors:
            # 收集该因子在所有 code 上的值
            values = []
            codes_with_value = []
            for code, factors in raw.items():
                if fname in factors and not np.isnan(factors[fname]):
                    values.append(factors[fname])
                    codes_with_value.append(code)

            if len(values) < 2:
                # 数据不足 2 个，无法排名
                for code in raw:
                    rank_details[code][fname] = float("nan")
                if values:
                    warnings.append(
                        f"因子 {fname}: 仅 {len(values)} 个有效值，无法横截面排名"
                    )
                continue

            # scipy.stats.rankdata: 默认升序排名
            # 我们希望 rank=1 = 因子值最高（适合选股）
            # 所以用 method="average" + ascending=False 等价于 ascending=True 后 1 - rank/(N-1)
            # 但更稳妥：ascending=False 直接 rank 降序
            ranks = rankdata([-v for v in values], method="average")  # 负值反转
            n = len(values)
            normalized = (ranks - 1) / (n - 1)  # 归一到 [0, 1]

            for code, rank in zip(codes_with_value, normalized):
                rank_details[code][fname] = float(rank)

        # 对无数据的 factor 也填 NaN
        for code in raw:
            for fname in all_factors:
                if fname not in rank_details[code]:
                    rank_details[code][fname] = float("nan")

        return rank_details

    def _layer3_composite(
        self,
        rank_details: dict[str, dict[str, float]],
        weights: dict[str, float],
        warnings: list[str],
    ) -> dict[str, float]:
        """Layer 3: 加权综合分。

        composite_score = Σ(weight_i × rank_i) / Σ(weight_i)
        用 Σ(weight_i) 归一化是为了处理"部分因子 NaN"的场景。

        Returns:
            {code: composite_score ∈ [0, 1]}
        """
        scores: dict[str, float] = {}
        for code, ranks in rank_details.items():
            weighted_sum = 0.0
            weight_sum = 0.0
            for fname, weight in weights.items():
                rank = ranks.get(fname, float("nan"))
                if np.isnan(rank):
                    continue
                weighted_sum += weight * rank
                weight_sum += weight
            if weight_sum > 0:
                scores[code] = weighted_sum / weight_sum
            else:
                scores[code] = float("nan")
                warnings.append(f"{code}: 所有权重对应因子都 NaN")
        return scores

    @classmethod
    def default_v2(cls) -> "CrossSectionalScorer":
        """默认 v2 工厂：FactorSet.eight_factor_v2() + WeightScheme.d004_b2()"""
        return cls(
            factor_set=FactorSet.eight_factor_v2(),
            weight_scheme=WeightScheme.d004_b2(),
        )


__all__ = ["CrossSectionalScorer", "ScoringResult"]