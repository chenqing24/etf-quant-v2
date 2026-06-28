"""
backtest/backtesting_adapter.py — v2 因子 ↔ Backtesting.py 适配器

用途：把 v2 28 因子映射成 Backtesting.py 兼容的 Strategy，
     让真实回测替换 run_validate.py 里的硬编码 mock 数据。

被谁调用：
- scripts/run_real_backtest.py（CLI 入口，single/all 子命令）
- skills/etf-research/scripts/run_validate.py（即将改造，TODO）

借鉴业界实践（按规则 13）：
- Backtesting.py (github.com/kernc/backtesting.py, MIT) 的 Strategy 模式
- Qlib (github.com/microsoft/qlib, MIT) 的多因子合成打分思路

设计原则（按规则 10/12/15）：
- 不重写 Backtesting.py 内核（规则 12）
- 通过 Strategy 子类注入 v2 28 因子（规则 15：架构改造有回归测试）
- 输出与 v1 时代 backtest_*.py 同结构的结果（规则 20：行为变化同步测试）
- 数据读取走 DataLoader（规则 15：业务代码禁止直接 DB 连接）

接口契约：
    engine = RealBacktestEngine(factor_names=['T1_macd_bar', 'M2_momentum_5d'], top_k=5)
    result = engine.run(code='510300', start='2024-01-01', end='2025-12-31')
    result.sharpe, result.max_drawdown, result.total_return
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

from etf_quant.alpha.factors import FACTOR_REGISTRY
from etf_quant.data_layer.loader import DataLoader


@dataclass
class BacktestResult:
    """回测结果（与 v1 时代 backtest_*.py 输出对齐）"""
    code: str
    start: str
    end: str
    total_return: float      # 总收益率
    annual_return: float     # 年化收益率
    sharpe: float            # Sharpe 比率
    max_drawdown: float      # 最大回撤（负数）
    n_trades: int            # 交易次数
    win_rate: float          # 胜率


def _load_etf_data(code: str, db_path: Path) -> pd.DataFrame:
    """通过 DataLoader 读 ETF 日线，转 Backtesting.py 格式（大写列名 + DatetimeIndex）

    按 SOUL.md 规则 15：业务代码禁止直接 DB 连接，必须走 DataLoader。
    DataLoader 返回小写列名 + date 列（非 index），需转换。
    """
    loader = DataLoader(db_path=str(db_path))
    df = loader.load_single(code=code, min_rows=1)
    if df is None or df.empty:
        raise ValueError(f"ETF {code} 在数据库无数据")

    df = df.rename(columns={
        'date': 'Date', 'open': 'Open', 'high': 'High',
        'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    return df


def _make_strategy_class(factor_names: List[str], top_k: int):
    """工厂：动态生成 Backtesting.py 兼容的 Strategy 类"""
    from backtesting import Strategy

    class FactorCompositeStrategy(Strategy):
        """多因子合成打分 → Top K 触发买入"""

        def init(self):
            # 预计算所有因子（用 Backtesting.py 的 self.I() 包装，便于 plot）
            self.factors = {}
            for fname in factor_names:
                if fname not in FACTOR_REGISTRY:
                    raise ValueError(
                        f"Unknown factor '{fname}'. "
                        f"Available: {list(FACTOR_REGISTRY.keys())[:5]}..."
                    )
                factor = FACTOR_REGISTRY[fname]()
                # 因子值（self.I 包装让 Backtesting.py 能 plot）
                series = self.I(
                    lambda f=factor, d=self.data: f.compute(_ohlcv_from_data(d)).fillna(0).values
                )
                self.factors[fname] = series

            # 合成 score = D-004 B2 加权求和（D-013 取代等权硬编码）
            # 设计依据：reports/2026-06-28_d013_daily_scoring/DECISIONS.md
            from etf_quant.alpha.weight_scheme import WeightScheme
            scheme = WeightScheme.d004_b2()
            # 当前 Backtesting.py 是单标的回测（不是横截面），所以用 trend_up 权重作为默认
            # 横截面打分应在 multi-ETF 场景使用 CrossSectionalScorer
            weights_t = scheme.get_weights("trend_up")
            weighted_sum = sum(
                weights_t.get(fname, 1.0 / len(self.factors)) * self.factors[fname]
                for fname in self.factors
            )
            self.composite = weighted_sum

        def next(self):
            # Top K 触发买入（这里简化：单标的，所以 score > 0 就持有）
            if len(self.composite) < 2:
                return
            if self.composite[-1] > 0 and not self.position:
                self.buy()
            elif self.composite[-1] < 0 and self.position:
                self.position.close()

    return FactorCompositeStrategy


def _ohlcv_from_data(data) -> pd.DataFrame:
    """Backtesting.py data → v2 Factor 需要的 OHLCV DataFrame（小写列名）"""
    return pd.DataFrame({
        'open': data.Open,
        'high': data.High,
        'low': data.Low,
        'close': data.Close,
        'volume': data.Volume,
    })


class RealBacktestEngine:
    """真实回测引擎：v2 因子 + Backtesting.py"""

    def __init__(
        self,
        factor_names: Optional[List[str]] = None,
        top_k: int = 5,
        cash: float = 100_000,
        commission: float = 0.001,
    ):
        # 默认懒人版 7 因子（v1 时代常用）
        self.factor_names = factor_names or [
            'T1_macd_bar', 'T3_sar_trend', 'T4_adx_trend',
            'M2_momentum_5d', 'M3_momentum_10d',
            'V1_volume', 'W1_atr',
        ]
        self.top_k = top_k
        self.cash = cash
        self.commission = commission

    def run(
        self,
        code: str,
        db_path: Path,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> BacktestResult:
        """跑单只 ETF 回测"""
        from backtesting import Backtest

        df = _load_etf_data(code, db_path)
        if start:
            df = df[df.index >= pd.to_datetime(start)]
        if end:
            df = df[df.index <= pd.to_datetime(end)]

        strategy_cls = _make_strategy_class(self.factor_names, self.top_k)
        # Backtesting.py 要求所有参数（finalize_trades 等）作为 Strategy 类变量
        # 在 Backtest() 构造时传入，run() 不接受
        bt = Backtest(
            df, strategy_cls,
            cash=self.cash, commission=self.commission,
            finalize_trades=True,  # 平掉未平仓交易，纳入统计
        )
        stats = bt.run()

        return BacktestResult(
            code=code,
            start=str(df.index[0].date()) if hasattr(df.index[0], 'date') else str(df.index[0]),
            end=str(df.index[-1].date()) if hasattr(df.index[-1], 'date') else str(df.index[-1]),
            total_return=float(stats['Return [%]']),
            annual_return=float(stats['Return (Ann.) [%]']),
            sharpe=float(stats['Sharpe Ratio']),
            max_drawdown=float(stats['Max. Drawdown [%]']),
            n_trades=int(stats['# Trades']),
            win_rate=float(stats['Win Rate [%]']),
        )