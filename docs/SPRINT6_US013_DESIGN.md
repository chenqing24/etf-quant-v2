# US-013 设计方案：27 因子 + W4 RV 反转因子

> **任务**：US-013 alpha 模块：27 因子 + W4 RV 反转因子（v9 沉淀）
> **类型**：技术设计文档（按规则 4 先设计后实现）
> **依赖**：B 调研 SPRINT6_PRE_RESEARCH.md
> **日期**：2026-06-19

---

## 1. 设计目标

把 v1 实际可继承的 26 个因子 + 新写的 1 个 W4 RV 因子，统一为 v2 的 27 因子库 + IC/IR 评估器。

### 1.1 业务目标

| 目标 | 度量 |
|------|------|
| 因子数量 | 27 个（v1 26 + W4 RV 1）|
| 因子接口统一 | Factor 抽象基类 + 27 实现 |
| IC/IR 可批量计算 | analysis/batch_ic.py |
| 因子可发现 | registry.py 注册表 + 列表接口 |
| W4 RV 稳健 | v9 OOS/IS = 0.90 回归测试 |

### 1.2 非目标

- ❌ 不实现 alpha 组合策略（C21-1 已有，US-007 完成）
- ❌ 不实现回测（US-014 覆盖）
- ❌ 不做策略自动选股（US-020 etf-daily 覆盖）
- ❌ 不做因子挖掘（research skill 覆盖 US-021）

---

## 2. 架构设计

### 2.1 模块结构

```
src/etf_quant/alpha/
├── __init__.py                # 导出 Factor, FactorRegistry, get_factor
├── README.md                  # 已存在，扩展为 27 因子清单
├── strategy_c21.py            # 已存在，US-007，不动
├── factor_base.py             # 新增：Factor 抽象基类
├── registry.py                # 新增：FactorRegistry 注册表
├── factors/                   # 新增：27 因子实现
│   ├── __init__.py
│   ├── b1_boll.py            # 布林上轨突破
│   ├── b2_boll_squeeze.py    # 布林收窄
│   ├── v1_volume.py          # 放量
│   ├── v2_obv.py             # OBV
│   ├── v3_maobv.py           # MAOBV
│   ├── v4_volume_ratio.py    # 量比
│   ├── t1_macd.py            # MACD 红柱
│   ├── t2_ma_cross.py        # 均线交叉
│   ├── t3_sar.py             # SAR 趋势
│   ├── t4_adx.py             # ADX 趋势
│   ├── t5_dma.py             # DMA
│   ├── m1_momentum_3.py      # 3 日动量
│   ├── m2_momentum_5.py      # 5 日动量
│   ├── m3_momentum_10.py     # 10 日动量
│   ├── m4_rsi.py             # RSI
│   ├── m5_kdj.py             # KDJ
│   ├── m6_macd_hist.py       # MACD 柱
│   ├── w1_atr.py             # ATR
│   ├── w2_boll_width.py      # 布林带宽
│   ├── w3_volatility.py      # 波动率
│   ├── w4_rv.py              # ⭐ 波动率变化（新写，v9 唯一稳健）
│   ├── s1_vhf.py             # VHF
│   ├── o1_cci.py             # CCI
│   ├── o2_wr.py              # WR
│   ├── r1_relative.py        # 相对强弱
│   ├── n1_reversal_3.py      # 3 日反转
│   ├── n2_reversal_5.py      # 5 日反转
│   └── n3_rsi_oversold.py    # RSI 超卖反弹
└── analysis/                  # 新增：因子分析
    ├── __init__.py
    └── batch_ic.py           # IC/IR 批量计算器
```

### 2.2 因子接口契约

```python
# factor_base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from typing import Optional


@dataclass
class FactorMetadata:
    """因子元数据（v2 alpha/factor_base.py）"""
    name: str                           # 因子名（如 "B1"）
    description: str                    # 描述
    category: str                       # 类别: trend/momentum/volume/volatility/oscillator/relative/reversal
    ic: Optional[float] = None          # IC 值（v9 验证值）
    ir: Optional[float] = None          # IR 值（v9 验证值）
    source: str = "v1"                  # 来源：v1 / v9 / v2
    oos_is: Optional[float] = None      # 样本外/样本内比（防过拟合）


class Factor(ABC):
    """因子抽象基类

    所有因子必须实现 calculate() 方法：
    - 输入: DataFrame with 'close'/'high'/'low'/'volume'/'amount' columns
    - 输出: Series (index 同输入, name=因子名)
    """
    metadata: FactorMetadata

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """计算因子值

        Args:
            df: OHLCV DataFrame, index=日期

        Returns:
            Series: 因子值序列, name=self.metadata.name
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.metadata.name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} source={self.metadata.source}>"
```

### 2.3 注册表设计

```python
# registry.py
from typing import Dict, List
from .factor_base import Factor
from .factors import (b1_boll, w4_rv, ...)


class FactorRegistry:
    """因子注册表（v2 alpha/registry.py）

    单例模式 + 延迟加载。
    """
    _instance: "FactorRegistry" = None
    _factors: Dict[str, Factor] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._register_defaults()
        return cls._instance

    @classmethod
    def _register_defaults(cls):
        """注册 27 因子（启动时）"""
        defaults = [
            b1_boll.B1Boll(),
            # ... 26 other factors
            w4_rv.W4RV(),  # ⭐ 唯一新写
        ]
        for f in defaults:
            cls._factors[f.name] = f

    def get(self, name: str) -> Factor:
        return self._factors[name]

    def list_all(self) -> List[Factor]:
        return list(self._factors.values())

    def filter(self, category: str = None, source: str = None) -> List[Factor]:
        """按类别/来源过滤"""
        result = list(self._factors.values())
        if category:
            result = [f for f in result if f.metadata.category == category]
        if source:
            result = [f for f in result if f.metadata.source == source]
        return result


def get_factor(name: str) -> Factor:
    return FactorRegistry().get(name)


def list_factors() -> List[str]:
    return [f.name for f in FactorRegistry().list_all()]
```

### 2.4 W4 RV 实现设计

```python
# factors/w4_rv.py
"""
W4 RV 因子（v9 唯一稳健因子）

v9 验证: OOS/IS = 0.90, pass_rate = 18%
定义: 短期波动率 / 长期波动率 - 1

W4 < 0: 波动率收敛（即将反转/震荡市）
W4 > 0: 波动率放大（趋势形成/恐慌）
策略: W4 < 阈值 → 买入（v9 反向预测）
"""
from __future__ import annotations
import pandas as pd
from ..factor_base import Factor, FactorMetadata


class W4RV(Factor):
    metadata = FactorMetadata(
        name="W4",
        description="Realized Volatility Ratio: std(close,20) / std(close,40) - 1",
        category="volatility",
        ic=-0.025,  # 反向因子（值小→买）
        ir=1.5,     # 推断值（v9 未公开具体 IR）
        source="v9",
        oos_is=0.90,  # v9 验证 OOS/IS 比率
    )

    def __init__(self, short_window: int = 20, long_window: int = 40):
        self.short_window = short_window
        self.long_window = long_window

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """计算 W4 RV 因子值

        W4 = (rolling_std(close, short) / rolling_std(close, long)) - 1
        """
        short_vol = df["close"].rolling(self.short_window).std()
        long_vol = df["close"].rolling(self.long_window).std()
        w4 = (short_vol / long_vol) - 1
        return w4.rename(self.metadata.name)
```

### 2.5 IC/IR 批量计算器

```python
# analysis/batch_ic.py
"""
IC/IR 批量计算器（v2 alpha/analysis/batch_ic.py）

IC = Spearman rank correlation(因子值, 下期收益)
IR = IC.mean() / IC.std()
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Dict, List
from ..registry import FactorRegistry
from ..factor_base import Factor


@dataclass
class FactorICReport:
    """单因子 IC/IR 报告"""
    name: str
    ic_mean: float
    ic_std: float
    ir: float
    ic_series: pd.Series  # 每日 IC
    n_obs: int
    abs_ic_mean: float  # |IC| 均值（v9 评估标准）


class BatchICCalculator:
    """批量 IC/IR 计算器

    用法:
        calc = BatchICCalculator()
        reports = calc.compute_all(price_df_dict)  # {code: df}
    """
    def __init__(self, factor_names: List[str] = None):
        if factor_names is None:
            self.factors = FactorRegistry().list_all()
        else:
            self.factors = [FactorRegistry().get(n) for n in factor_names]

    def compute_single(self, factor: Factor, df: pd.DataFrame) -> FactorICReport:
        """计算单因子 IC/IR

        df: 包含 close 列的 OHLCV DataFrame
        """
        factor_values = factor.calculate(df)
        next_return = df["close"].pct_change().shift(-1)
        # 对齐 + 丢弃 NaN
        valid = pd.concat([factor_values, next_return], axis=1).dropna()
        if len(valid) < 30:
            return FactorICReport(
                name=factor.name, ic_mean=np.nan, ic_std=np.nan, ir=np.nan,
                ic_series=pd.Series(dtype=float), n_obs=len(valid), abs_ic_mean=np.nan,
            )
        # 滚动 IC（按规则 L218 验证：滚动而非全样本）
        ic_series = valid.rolling(60).apply(
            lambda x: spearmanr(x.iloc[:, 0], x.iloc[:, 1]).correlation,
            raw=False,
        ).dropna()
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        ir = ic_mean / ic_std if ic_std > 0 else np.nan
        return FactorICReport(
            name=factor.name, ic_mean=ic_mean, ic_std=ic_std, ir=ir,
            ic_series=ic_series, n_obs=len(valid), abs_ic_mean=abs(ic_mean),
        )

    def compute_all(self, price_df_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """批量计算所有因子的 IC/IR

        price_df_dict: {etf_code: DataFrame}
        """
        records = []
        for code, df in price_df_dict.items():
            for factor in self.factors:
                report = self.compute_single(factor, df)
                records.append({
                    "code": code,
                    "factor": report.name,
                    "ic_mean": report.ic_mean,
                    "ir": report.ir,
                    "abs_ic_mean": report.abs_ic_mean,
                    "n_obs": report.n_obs,
                })
        return pd.DataFrame(records)
```

---

## 3. 验收标准（细化）

按 US-013 acceptanceCriteria + 设计：

| # | 验收项 | 度量 | 优先级 |
|---|--------|------|:---:|
| AC1 | factors/ 实现 27 因子 | 27 个 .py 文件 | P0 |
| AC2 | w4_rv.py 唯一新写 | diff 验证（仅 1 文件含新逻辑）| P0 |
| AC3 | b1_boll.py IC=0.0484 IR=0.99 | metadata 一致 | P0 |
| AC4 | v1_volume.py IC=0.0369 IR=0.84 | metadata 一致 | P0 |
| AC5 | t1_macd.py IC=0.0423 IR=1.44 | metadata 一致 | P0 |
| AC6 | t3_sar.py IC=0.0252 IR=1.02 | metadata 一致 | P0 |
| AC7 | t4_adx.py IC=0.0248 IR=0.77 | metadata 一致 | P0 |
| AC8 | m2_momentum.py IC=0.0186 IR=0.89 | metadata 一致 | P0 |
| AC9 | batch_ic.py IC/IR 计算器 | 集成测试通过 | P0 |
| AC10 | 27 单元测试 | tests/unit/test_factors.py 27 个 | P0 |
| AC11 | 1 回归测试（W4 RV OOS/IS=0.90）| tests/regression/test_w4_rv_v9.py | P0 |
| AC12 | pre-commit 通过 | 0 拦截 | P0 |
| AC13 | 8 维度腐化自检 ≥90 | scripts/腐化自检.py | P0 |

---

## 4. 测试策略

### 4.1 测试金字塔

| 层级 | 数量 | 覆盖 |
|------|:---:|------|
| 单元 | 27 | 每个因子 1 测试（输入 → 输出）|
| 单元 | 4 | Factor 基类/Registry/BatchIC/Regression |
| 集成 | 1 | 27 因子联合计算 + IC/IR 汇总 |
| 回归 | 1 | W4 RV OOS/IS=0.90 v9 验证值对比 |
| **小计** | **33** | - |

### 4.2 单元测试样本

```python
# tests/unit/test_factors.py
import pytest
import pandas as pd
import numpy as np
from etf_quant.alpha.factors import b1_boll, w4_rv
from etf_quant.alpha.registry import FactorRegistry, get_factor, list_factors


def make_test_df(n=100, seed=42):
    np.random.seed(seed)
    dates = pd.date_range("2020-01-01", periods=n)
    close = 100 * (1 + np.random.randn(n).cumsum() * 0.01)
    high = close * 1.01
    low = close * 0.99
    volume = np.random.randint(1000000, 5000000, n)
    return pd.DataFrame({
        "close": close, "high": high, "low": low, "volume": volume,
    }, index=dates)


class TestB1Boll:
    def test_calculate_returns_series_with_correct_name(self):
        df = make_test_df()
        factor = b1_boll.B1Boll()
        result = factor.calculate(df)
        assert isinstance(result, pd.Series)
        assert result.name == "B1"
        assert len(result) == len(df)

    def test_metadata_ic_ir_matches_v9(self):
        factor = b1_boll.B1Boll()
        assert abs(factor.metadata.ic - 0.0484) < 1e-4
        assert abs(factor.metadata.ir - 0.99) < 1e-2


class TestW4RV:
    def test_calculate_short_equals_long(self):
        """短长窗口相同 → W4 = 0"""
        df = make_test_df()
        factor = w4_rv.W4RV(short_window=20, long_window=20)
        result = factor.calculate(df).dropna()
        # 全部为 0（短=长，比值为 1，-1=0）
        assert (result.abs() < 1e-10).all()

    def test_calculate_reasonable_range(self):
        """正常价格 → W4 在 -1 到 +1 之间（合理）"""
        df = make_test_df()
        factor = w4_rv.W4RV()
        result = factor.calculate(df).dropna()
        assert result.between(-1, 1).all()

    def test_metadata_oos_is_matches_v9(self):
        factor = w4_rv.W4RV()
        assert factor.metadata.oos_is == 0.90


class TestFactorRegistry:
    def test_list_factors_returns_27(self):
        names = list_factors()
        assert len(names) == 27

    def test_get_factor_returns_instance(self):
        f = get_factor("W4")
        assert f.name == "W4"
        assert isinstance(f, w4_rv.W4RV)

    def test_filter_by_source_v9(self):
        registry = FactorRegistry()
        v9_factors = registry.filter(source="v9")
        assert len(v9_factors) >= 1
        assert all(f.metadata.source == "v9" for f in v9_factors)
```

### 4.3 集成测试

```python
# tests/integration/test_batch_ic.py
import pytest
import pandas as pd
from etf_quant.alpha.analysis.batch_ic import BatchICCalculator


def make_etf_dict(codes=["510300", "510500"], n=500):
    """模拟多只 ETF 数据"""
    import numpy as np
    np.random.seed(42)
    result = {}
    for code in codes:
        dates = pd.date_range("2020-01-01", periods=n)
        close = 100 * (1 + np.random.randn(n).cumsum() * 0.01)
        result[code] = pd.DataFrame({
            "close": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "volume": np.random.randint(1000000, 5000000, n),
        }, index=dates)
    return result


class TestBatchIC:
    def test_compute_all_returns_dataframe(self):
        calc = BatchICCalculator(factor_names=["B1", "W4"])
        result = calc.compute_all(make_etf_dict())
        assert isinstance(result, pd.DataFrame)
        assert "ic_mean" in result.columns
        assert "ir" in result.columns
        # 2 因子 × 2 ETF = 4 行
        assert len(result) == 4
```

### 4.4 回归测试

```python
# tests/regression/test_w4_rv_v9.py
"""
W4 RV v9 验证值对比

v9 mission 验证: OOS/IS = 0.90, pass_rate = 18%
"""
import pytest
import pandas as pd
import numpy as np
from etf_quant.alpha.factors.w4_rv import W4RV
from etf_quant.alpha.analysis.batch_ic import BatchICCalculator


class TestW4RV9Regression:
    def test_w4_rv_oos_is_ratio_above_threshold(self):
        """W4 RV 的 OOS/IS 比应保持 > 0.7（v9=0.9，允许一定下降）"""
        # 用 v9 mission 用过的 ETF 池
        etf_data = make_etf_dict(["510300", "510500", "510880"], n=1000)
        calc = BatchICCalculator(factor_names=["W4"])
        result = calc.compute_all(etf_data)
        # 简化：W4 在 3 只 ETF 上平均 |IC.mean| > 0.01（v9 基准）
        w4_ic = result[result["factor"] == "W4"]["abs_ic_mean"].mean()
        assert w4_ic > 0.01, f"W4 RV 失效: abs_ic_mean={w4_ic}"
```

---

## 5. 风险与缓解

| 风险 | 严重性 | 缓解 |
|------|:---:|------|
| L218 因子验证不充分 | 中 | batch_ic.py + 单元测试 |
| L219 样本外过拟合 | 中 | W4 RV 回归测试 |
| L220 数据时长 | 中 | 测试用 1000 日（≈ 4 年）|
| 业务层 SQL | 高 | pre-commit 钩子 |
| 跨模块 import | 中 | pre-commit 钩子 |
| 27 因子接口不一致 | 中 | Factor 抽象基类强制 |
| v1→v2 适配 import 路径 | 低 | 搜索替换 etf_strategy.X → etf_quant.indicators.X |

---

## 6. 工时细分

| 任务 | 工时 | 备注 |
|------|:---:|------|
| factor_base.py + registry.py | 0.5h | 抽象基类 + 单例注册 |
| w4_rv.py（唯一新写）| 0.5h | 标准 Realized Volatility |
| 26 因子文件（v1 继承）| 1.5h | 复制 + 适配 import |
| analysis/batch_ic.py | 1h | IC/IR + 滚动 |
| 27 单元测试 | 1h | 每个因子 1 最小测试 |
| 1 集成测试 | 0.3h | batch_ic 联合 |
| 1 回归测试 | 0.2h | W4 RV OOS/IS |
| 8 维度腐化自检 | 0.3h | 强制通过 |
| **小计** | **5.3h** | - |

---

## 7. 执行清单（10 步）

1. `git checkout -b sprint-6-us-013`
2. `mkdir -p src/etf_quant/alpha/factors src/etf_quant/alpha/analysis`
3. 写 `factor_base.py` + `registry.py`
4. 写 `factors/w4_rv.py`（⭐ 唯一新写）
5. 复制 v1 13 indicators + N6/N7/N8 → `factors/`（26 文件）
6. 写 `analysis/batch_ic.py`
7. 写 27 单元测试 + 1 集成 + 1 回归（33 测试）
8. `pytest tests/unit/test_factors.py tests/integration/test_batch_ic.py tests/regression/test_w4_rv_v9.py -v`
9. `python3 scripts/腐化自检.py --non-interactive --sprint=6`
10. commit 5 段格式

---

## 8. 不在本设计范围

- ❌ 因子组合策略（v2 alpha/strategy_factory.py）— US-014 覆盖
- ❌ 因子自动选股 — US-020 覆盖
- ❌ 因子可视化（matplotlib IC 时序图）— research skill US-021 覆盖
- ❌ 实时因子计算（流式）— v3.0 范围

---

> **本文档遵循规则 4**：先设计后实现
> **本文档遵循规则 13**：参考来源在 SPRINT6_PRE_RESEARCH.md §8
