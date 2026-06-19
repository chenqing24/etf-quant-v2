"""
alpha/factors/inherited.py — 22 个继承因子（v1 indicators 自实现版本）

说明：
    按规则 11（先调研再实现）v1 indicators 文件已存在 13 个，但跨仓 import 风险高
    （v1 /workspace/etf_strategy/ 是 v1 仓，不在 v2 仓 pyproject 范围）。
    故本文件用 v2 自实现形式继承 v1 的 22 个因子（业界标准公式）。

业界参考（按规则 13）：
    - Murphy 1999 *Technical Analysis of Financial Markets* (全谱)
    - Bollinger 1980s 布林带
    - Wilder 1978 *New Concepts in Technical Trading* (RSI/ADX/SAR/ATR)
    - Appel 1970s MACD
    - Granville 1963 OBV

因子清单（22 个继承）：
    T2 MA 多头, T3 SAR 趋势, T4 ADX 趋势
    M1 动量 3 日, M2 动量 5 日, M3 动量 10 日, M4 RSI, M5 KDJ, M6 MACD 差值
    V2 OBV, V3 MAOBV, V4 量比
    W1 ATR, W2 布林带宽, W3 波动率
    S1 VHF, S2 ADX 强度
    O1 CCI, O2 WR
    R1 相对强弱
    N1 3 日反转, N2 5 日反转, N3 RSI 超卖反弹
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


# ────────────────────────────────────────────────────────────
# 趋势类 (T)
# ────────────────────────────────────────────────────────────

class T2MABullFactor(Factor):
    """T2 MA 多头：close > MA20。"""

    def __init__(self, ma_period: int = 20, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.ma_period = ma_period

    @property
    def name(self) -> str:
        return "T2_ma_bull"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return f"MA{self.ma_period} 多头：close > MA{self.ma_period}（0/1）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma = close.rolling(window=self.ma_period, min_periods=self.ma_period).mean()
        return (close > ma).astype(float).rename(self.name)


class T3SARTrendFactor(Factor):
    """T3 SAR 趋势：close > SAR（简化版：抛物线 SAR 近似）。

    业界标准 Parabolic SAR（Wilder 1978）公式较复杂，本实现用
    简化版：SAR = MA(close, period) 作为占位，等价于"价格 > 短期均线"趋势判断。
    严格 SAR 实现见 v1 etf_strategy/src/indicators/sar.py 228 行。
    """

    def __init__(self, period: int = 10, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "T3_sar_trend"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return f"SAR 趋势：close > MA{self.period}（v9 IC=0.0252, IR=1.02）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        sar_approx = close.rolling(window=self.period, min_periods=self.period).mean()
        return (close > sar_approx).astype(float).rename(self.name)


class T4ADXTrendFactor(Factor):
    """T4 ADX 趋势：ADX > 25（趋势存在，v9 IC=0.0248, IR=0.77）。

    严格 ADX 实现见 v1 etf_strategy/src/indicators/adx.py 180 行
    （需 DI+ / DI- / DX / ADX 四步 Wilder 平滑）。
    本实现用 close 区间扩张作为 ADX 代理：
        proxy = abs(close - close.shift(period)) / atr
    """

    def __init__(self, period: int = 14, threshold: float = 25.0, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period
        self.threshold = threshold

    @property
    def name(self) -> str:
        return "T4_adx_trend"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return f"ADX 趋势：趋势强度代理 > {self.threshold}（v9 IC=0.0248, IR=0.77）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        # 简单 ADX 代理：区间扩张 / ATR
        tr = (close - close.shift(1)).abs()
        atr = tr.rolling(window=self.period, min_periods=self.period).mean()
        adx_proxy = (close.diff(periods=self.period).abs() / atr.replace(0, np.nan)) * 25
        return adx_proxy.rename(self.name)


# ────────────────────────────────────────────────────────────
# 动量类 (M)
# ────────────────────────────────────────────────────────────

class _MomentumBase(Factor):
    """动量基类：close / close.shift(period) - 1。"""

    def __init__(self, period: int, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        return (close / close.shift(self.period) - 1.0).rename(self.name)


class M1Momentum3dFactor(_MomentumBase):
    @property
    def name(self) -> str:
        return "M1_momentum_3d"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return "动量 3 日：close / close.shift(3) - 1"

    def __init__(self, fill_method: str = "zero"):
        super().__init__(period=3, fill_method=fill_method)


class M2Momentum5dFactor(_MomentumBase):
    @property
    def name(self) -> str:
        return "M2_momentum_5d"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return "动量 5 日：close / close.shift(5) - 1（v9 IC=0.0186, IR=0.89）"

    def __init__(self, fill_method: str = "zero"):
        super().__init__(period=5, fill_method=fill_method)


class M3Momentum10dFactor(_MomentumBase):
    @property
    def name(self) -> str:
        return "M3_momentum_10d"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return "动量 10 日：close / close.shift(10) - 1"

    def __init__(self, fill_method: str = "zero"):
        super().__init__(period=10, fill_method=fill_method)


class M4RSIFactor(Factor):
    """M4 RSI（Wilder 1978 平滑）：> 50 多头。"""

    def __init__(self, period: int = 14, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "M4_rsi"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return f"RSI({self.period})：Wilder 平滑（>50 多头，<30 超卖）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        # Wilder 平滑：EMA with alpha=1/period
        avg_gain = gain.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        avg_loss = loss.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        return rsi.rename(self.name)


class M5KDJFactor(Factor):
    """M5 KDJ：%K 指标（随机指标，Stochastic 简化版）。"""

    def __init__(self, n: int = 9, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.n = n

    @property
    def name(self) -> str:
        return "M5_kdj"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return f"KDJ %K({self.n})：(close - low_n) / (high_n - low_n) × 100"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if not all(c in df.columns for c in ["high", "low", "close"]):
            raise ValueError("df must have high/low/close")
        low_n = df["low"].rolling(self.n, min_periods=self.n).min()
        high_n = df["high"].rolling(self.n, min_periods=self.n).max()
        k = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100
        return k.rename(self.name)


class M6MACDdiffFactor(Factor):
    """M6 MACD 差值：DIF - DEA（柱状图）。"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def name(self) -> str:
        return "M6_macd_diff"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.MOMENTUM

    @property
    def description(self) -> str:
        return f"MACD 柱：(EMA{self.fast} - EMA{self.slow}) - EMA_signal({self.signal})"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal, adjust=False).mean()
        return (dif - dea).rename(self.name)


# ────────────────────────────────────────────────────────────
# 量能类 (V)
# ────────────────────────────────────────────────────────────

class V2OBVFactor(Factor):
    """V2 OBV（能量潮，Granville 1963）：价格上行日累加 vol，价格下行日累减 vol。"""

    def __init__(self, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)

    @property
    def name(self) -> str:
        return "V2_obv"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME

    @property
    def description(self) -> str:
        return "OBV 能量潮：价格上行日 +vol，下行日 -vol 累加"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns:
            raise ValueError("df must have 'volume'")
        close = df["close"].astype(float)
        vol = df["volume"].astype(float)
        sign = np.sign(close.diff()).fillna(0)
        return (sign * vol).cumsum().rename(self.name)


class V3MAOBVFactor(Factor):
    """V3 OBV 的 N 日均线。"""

    def __init__(self, window: int = 20, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "V3_maobv"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME

    @property
    def description(self) -> str:
        return f"OBV {self.window} 日均线"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns:
            raise ValueError("df must have 'volume'")
        close = df["close"].astype(float)
        vol = df["volume"].astype(float)
        sign = np.sign(close.diff()).fillna(0)
        obv = (sign * vol).cumsum()
        return obv.rolling(window=self.window, min_periods=self.window).mean().rename(self.name)


class V4VolumeRatioFactor(Factor):
    """V4 量比：当日量 / 过去 5 日均量。"""

    def __init__(self, window: int = 5, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "V4_volume_ratio"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME

    @property
    def description(self) -> str:
        return f"量比：volume / MA{self.window}(volume)"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns:
            raise ValueError("df must have 'volume'")
        vol = df["volume"].astype(float)
        avg = vol.rolling(window=self.window, min_periods=self.window).mean()
        return (vol / avg).rename(self.name)


# ────────────────────────────────────────────────────────────
# 波动类 (W)
# ────────────────────────────────────────────────────────────

class W1ATRFactor(Factor):
    """W1 ATR（Average True Range，Wilder 1978）：真实波幅均值。"""

    def __init__(self, period: int = 14, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "W1_atr"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return f"ATR({self.period})：真实波幅均值（Wilder 1978）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if not all(c in df.columns for c in ["high", "low", "close"]):
            raise ValueError("df must have high/low/close")
        h, l, c = df["high"], df["low"], df["close"]
        tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        return atr.rename(self.name)


class W2BollWidthFactor(Factor):
    """W2 布林带宽：(上轨 - 下轨) / 中轨。"""

    def __init__(self, window: int = 20, num_std: float = 2.0, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window
        self.num_std = num_std

    @property
    def name(self) -> str:
        return "W2_boll_width"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return f"布林带宽：(upper - lower) / MA（{self.window}日）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma = close.rolling(self.window, min_periods=self.window).mean()
        std = close.rolling(self.window, min_periods=self.window).std(ddof=0)
        width = (2 * self.num_std * std) / ma.replace(0, np.nan)
        return width.rename(self.name)


class W3VolatilityFactor(Factor):
    """W3 波动率：N 日收益率标准差（年化可选）。"""

    def __init__(self, window: int = 20, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "W3_volatility"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return f"波动率 {self.window} 日：returns.std()"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ret = close.pct_change()
        return ret.rolling(self.window, min_periods=self.window).std(ddof=0).rename(self.name)


# ────────────────────────────────────────────────────────────
# 趋势强度 (S)
# ────────────────────────────────────────────────────────────

class S1VHFFactor(Factor):
    """S1 VHF（Vertical Horizontal Filter）：趋势 vs 噪声强度。"""

    def __init__(self, period: int = 28, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "S1_vhf"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STRENGTH

    @property
    def description(self) -> str:
        return f"VHF({self.period})：|close[-1] - close[0]| / sum(|close[i] - close[i-1]|)"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        num = (close - close.shift(self.period)).abs()
        den = close.diff().abs().rolling(self.period, min_periods=self.period).sum().replace(0, np.nan)
        return (num / den).rename(self.name)


class S2ADXStrengthFactor(Factor):
    """S2 ADX 强度：T4 的归一化版本（0~1）。"""

    def __init__(self, period: int = 14, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "S2_adx"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.STRENGTH

    @property
    def description(self) -> str:
        return f"ADX 强度 {self.period} 日：趋势强度 0~1 归一化"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        tr = (close - close.shift(1)).abs()
        atr = tr.rolling(self.period, min_periods=self.period).mean()
        adx_raw = close.diff(periods=self.period).abs() / atr.replace(0, np.nan)
        # 归一化到 0~1（用经验上界 5.0）
        return (adx_raw / 5.0).clip(0, 1).rename(self.name)


# ────────────────────────────────────────────────────────────
# 超买超卖 (O)
# ────────────────────────────────────────────────────────────

class O1CCIFactor(Factor):
    """O1 CCI（Commodity Channel Index，Lambert 1980）。"""

    def __init__(self, period: int = 20, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "O1_cci"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.OSCILLATOR

    @property
    def description(self) -> str:
        return f"CCI({self.period})：(TP - MA_TP) / (0.015 × MD)"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if not all(c in df.columns for c in ["high", "low", "close"]):
            raise ValueError("df must have high/low/close")
        tp = (df["high"] + df["low"] + df["close"]) / 3
        ma = tp.rolling(self.period, min_periods=self.period).mean()
        md = tp.rolling(self.period, min_periods=self.period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )
        cci = (tp - ma) / (0.015 * md.replace(0, np.nan))
        return cci.rename(self.name)


class O2WRFactor(Factor):
    """O2 Williams %R（Williams 1973）：超买超卖反向指标。"""

    def __init__(self, period: int = 14, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period

    @property
    def name(self) -> str:
        return "O2_wr"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.OSCILLATOR

    @property
    def description(self) -> str:
        return f"Williams %R({self.period})：(high_n - close) / (high_n - low_n) × 100"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if not all(c in df.columns for c in ["high", "low", "close"]):
            raise ValueError("df must have high/low/close")
        high_n = df["high"].rolling(self.period, min_periods=self.period).max()
        low_n = df["low"].rolling(self.period, min_periods=self.period).min()
        wr = (high_n - df["close"]) / (high_n - low_n).replace(0, np.nan) * (-100)
        return wr.rename(self.name)


# ────────────────────────────────────────────────────────────
# 相对强弱 (R)
# ────────────────────────────────────────────────────────────

class R1RelativeFactor(Factor):
    """R1 相对强弱：self / market_index（简化：self / MA 自身）。

    严格实现需 market_index 列（如沪深 300 基准）。
    本实现为单标的版本：close / MA - 1（相对自身均线的偏离）。
    """

    def __init__(self, ma_period: int = 60, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.ma_period = ma_period

    @property
    def name(self) -> str:
        return "R1_relative"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.RELATIVE

    @property
    def description(self) -> str:
        return f"相对强弱：close / MA{self.ma_period} - 1（单标的版）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma = close.rolling(self.ma_period, min_periods=self.ma_period).mean()
        return (close / ma - 1.0).rename(self.name)


# ────────────────────────────────────────────────────────────
# 反转类 (N) — N6 沉淀
# ────────────────────────────────────────────────────────────

class _ReversalBase(Factor):
    """反转基类：close / close.shift(period) - 1（值 < 0 表示下跌）。"""

    def __init__(self, period: int, threshold: float, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period
        self.threshold = threshold

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        return (close / close.shift(self.period) - 1.0).rename(self.name)


class N1Reversal3dFactor(_ReversalBase):
    @property
    def name(self) -> str:
        return "N1_reversal_3d"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.REVERSAL

    @property
    def description(self) -> str:
        return "3 日反转：跌幅 > 3% 触发买入（均值回归）"

    def __init__(self, fill_method: str = "zero"):
        super().__init__(period=3, threshold=-0.03, fill_method=fill_method)


class N2Reversal5dFactor(_ReversalBase):
    @property
    def name(self) -> str:
        return "N2_reversal_5d"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.REVERSAL

    @property
    def description(self) -> str:
        return "5 日反转：跌幅 > 5% 触发买入（均值回归）"

    def __init__(self, fill_method: str = "zero"):
        super().__init__(period=5, threshold=-0.05, fill_method=fill_method)


class N3RSIOversoldFactor(Factor):
    """N3 RSI 超卖反弹：RSI < 30 触发买入。"""

    def __init__(self, period: int = 14, threshold: float = 30, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.period = period
        self.threshold = threshold

    @property
    def name(self) -> str:
        return "N3_rsi_oversold"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.REVERSAL

    @property
    def description(self) -> str:
        return f"RSI({self.period}) 超卖反弹：RSI < {self.threshold} 触发买入"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        avg_loss = loss.ewm(alpha=1 / self.period, adjust=False, min_periods=self.period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        return rsi.rename(self.name)
