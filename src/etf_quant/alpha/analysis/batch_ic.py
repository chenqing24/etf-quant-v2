"""
alpha/analysis/batch_ic.py — IC/IR 批量计算器（US-013）

用途：
    对 27 因子在历史数据上做 IC/IR 批量评估。
    IC = Spearman rank correlation（因子值 vs 下期 N 日收益）
    IR = IC.mean() / IC.std()

被谁调用：
    - scripts/run_factor_evaluation.py（CLI 入口）
    - tests/integration/alpha/test_batch_ic.py（集成测试）

功能说明：
    - calculate_ic: 单因子 IC 计算
    - calculate_ir: IC 序列 → 均值/标准差
    - BatchICEvaluator: 多因子批量评估

使用方式：
    from etf_quant.alpha.analysis.batch_ic import BatchICEvaluator
    from etf_quant.alpha.factors import get_factor

    evaluator = BatchICEvaluator(factor_names=["T1_macd_bar", "W4_rv"], forward_window=5)
    result_df = evaluator.evaluate(df)  # df 含 close + 因子列

依赖：
    - pandas: DataFrame
    - scipy.stats.spearmanr: 秩相关
    - L218 教训（IC/IR 验证）
    - L219 教训（样本外防过拟合）
    - L220 教训（数据时长校验）

注意事项：
    - 必须用 t 期因子值配对 t+1 ~ t+N 期收益（不能 shift 反向）
    - 至少需要 30 个有效样本（防 IR 不稳定）
    - 结果写入 data/factor_icir.csv（不入 git）

业界参考（按规则 13）：
    - Grinold & Kahn 2000 *Active Portfolio Management* Ch 4 (IC/IR 定义)
    - López de Prado 2018 *Advances in Financial ML* Ch 16 (PBO + CPR 防过拟合)
    - WorldQuant 101 Alphas paper (Kakushadze 2016) IC 评估流程
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


@dataclass
class ICResult:
    """单因子 IC/IR 评估结果。"""

    factor_name: str
    ic: float                          # IC 均值（Spearman ρ）
    ir: float                          # IR = IC.mean() / IC.std()
    ic_std: float                      # IC 标准差
    sample_count: int                  # 有效样本数
    forward_window: int                # 前瞻 N 日
    ic_series: list[float] = field(default_factory=list)  # 各期 IC


def calculate_ic(factor_series: pd.Series, returns: pd.Series) -> float:
    """
    计算单期 IC（Spearman rank correlation）。

    Args:
        factor_series: 因子值（t 期）
        returns: 下期收益（t+1 ~ t+N，已 shift）

    Returns:
        Spearman ρ（-1 ~ 1）
    """
    # 对齐索引
    aligned = pd.concat([factor_series, returns], axis=1).dropna()
    if len(aligned) < 5:
        return np.nan
    f = aligned.iloc[:, 0]
    r = aligned.iloc[:, 1]
    if f.std() == 0 or r.std() == 0:
        return np.nan
    rho, _ = spearmanr(f, r)
    return float(rho) if not np.isnan(rho) else np.nan


def calculate_ir(ic_series: list[float]) -> tuple[float, float]:
    """
    IR = IC.mean() / IC.std()。

    Returns:
        (ir, ic_std)
    """
    s = pd.Series([x for x in ic_series if not np.isnan(x)])
    if len(s) < 2:
        return np.nan, np.nan
    return float(s.mean() / s.std()) if s.std() > 0 else np.nan, float(s.std())


class BatchICEvaluator:
    """
    批量 IC/IR 评估器。

    Attributes:
        factor_names: 要评估的因子名列表
        forward_window: 前瞻 N 日收益（默认 5 日）
        min_samples: 最小样本数（默认 30）
    """

    def __init__(
        self,
        factor_names: list[str],
        forward_window: int = 5,
        min_samples: int = 30,
    ):
        self.factor_names = factor_names
        self.forward_window = forward_window
        self.min_samples = min_samples

    def evaluate(self, df: pd.DataFrame) -> list[ICResult]:
        """
        对每只 ETF（按 code 分组）/ 每因子计算滚动 IC。

        Args:
            df: DataFrame（多 code × 多日期 × 多 factor）

        Returns:
            ICResult 列表
        """
        results = []
        for factor_name in self.factor_names:
            ic_series = self._calculate_factor_ic_series(df, factor_name)
            if len(ic_series) < self.min_samples:
                results.append(ICResult(
                    factor_name=factor_name,
                    ic=np.nan, ir=np.nan, ic_std=np.nan,
                    sample_count=len(ic_series),
                    forward_window=self.forward_window,
                ))
                continue
            ir, ic_std = calculate_ir(ic_series)
            ic_mean = float(np.nanmean(ic_series))
            results.append(ICResult(
                factor_name=factor_name,
                ic=ic_mean, ir=ir, ic_std=ic_std,
                sample_count=len(ic_series),
                forward_window=self.forward_window,
                ic_series=ic_series,
            ))
        return results

    def _calculate_factor_ic_series(self, df: pd.DataFrame, factor_name: str) -> list[float]:
        """对单因子算滚动 IC 序列（适配单标的场景，v3 mission US-004 修复）。

        逻辑：
            - 单标的（1 个 code）：每 window_size 日算 1 个 IC，步长 step_size
              → 504 日 / 60 日窗 / 5 日步长 ≈ 89 个 IC
            - 多标的：每 (code, date) pair 算 1 个横截面 IC（原行为）
        """
        if factor_name not in df.columns or "close" not in df.columns:
            return []
        f = df[factor_name]
        fwd_ret = df.groupby("code")["close"].pct_change(self.forward_window).shift(-self.forward_window)

        codes = df["code"].unique() if "code" in df.columns else [None]
        ic_list = []

        if len(codes) == 1 and codes[0] is not None:
            # 单标的：滚动窗口
            window_size = 60   # 60 日窗口
            step_size = 5      # 5 日步长
            f_single = df[df["code"] == codes[0]][factor_name]
            r_single = fwd_ret.loc[f_single.index]
            for start in range(0, len(f_single) - window_size + 1, step_size):
                end = start + window_size
                f_win = f_single.iloc[start:end]
                r_win = r_single.iloc[start:end]
                ic_val = calculate_ic(f_win, r_win)
                if not np.isnan(ic_val):
                    ic_list.append(ic_val)
        else:
            # 多标的：每 group 算 1 个横截面 IC
            for _, grp in df.groupby("code"):
                f_grp = f.loc[grp.index]
                r_grp = fwd_ret.loc[grp.index]
                ic_val = calculate_ic(f_grp, r_grp)
                if not np.isnan(ic_val):
                    ic_list.append(ic_val)
        return ic_list

    def to_dataframe(self, results: list[ICResult]) -> pd.DataFrame:
        """结果转 DataFrame。"""
        rows = []
        for r in results:
            rows.append({
                "factor_name": r.factor_name,
                "ic": r.ic,
                "ir": r.ir,
                "ic_std": r.ic_std,
                "sample_count": r.sample_count,
                "forward_window": r.forward_window,
            })
        return pd.DataFrame(rows)

    def save(self, results: list[ICResult], path: str = "data/factor_icir.csv") -> None:
        """保存结果到 CSV。"""
        df = self.to_dataframe(results)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8")
