# alpha — 信号/因子

> **职责**：因子计算、信号生成、策略实现
> **依据**：v1 src/strategy/scorer.py + src/indicators/ + 6/16 C20 颠覆性发现
> **Sprint-6**：27 因子库（US-013 完成）

## 核心原则（v1 教训 L225 沉淀）

**alpha 真正来源 = 入场过滤 + 永远满仓**，不是 4 因子组合。

```
max_hold_days = 99999      # C11 修复（持仓管理核心）
entry: BOLL_strict_middle + close > MA60  # C21 网格最优
exit: enabled = false       # C20 验证（卖出是 alpha 拖累）
```

## 27 因子清单（v9 沉淀 + Sprint-6 US-013 实施）

| 类别 | 数量 | 因子 |
|------|:---:|------|
| 趋势 (TREND) | 4 | T1_macd_bar / T2_ma_bull / T3_sar_trend / T4_adx_trend |
| 动量 (MOMENTUM) | 6 | M1_momentum_3d / M2_momentum_5d / M3_momentum_10d / M4_rsi / M5_kdj / M6_macd_diff |
| 量能 (VOLUME) | 4 | V1_volume / V2_obv / V3_maobv / V4_volume_ratio |
| 波动 (VOLATILITY) | 5 | W1_atr / W2_boll_width / W3_volatility / B1_boll_upper / **W4_rv** ⭐ |
| 强度 (STRENGTH) | 2 | S1_vhf / S2_adx |
| 振荡 (OSCILLATOR) | 2 | O1_cci / O2_wr |
| 相对 (RELATIVE) | 1 | R1_relative |
| 反转 (REVERSAL) | 3 | N1_reversal_3d / N2_reversal_5d / N3_rsi_oversold |
| **总计** | **27** | - |

## 6 因子 IC/IR 验证值（v9 mission）

| 因子 | IC | IR | 状态 |
|------|:---:|:---:|------|
| B1_boll_upper | 0.0484 | 0.99 | ✅ |
| V1_volume | 0.0369 | 0.84 | ✅ |
| T1_macd_bar | 0.0423 | 1.44 | ✅ |
| T3_sar_trend | 0.0252 | 1.02 | ✅ |
| T4_adx_trend | 0.0248 | 0.77 | ✅ |
| M2_momentum_5d | 0.0186 | 0.89 | ⚠️ IC < 0.02 |

## 接口契约

### Factor

```python
@dataclass
class Factor:
    """单个因子（27 个，v9 沉淀）。"""
    name: str
    description: str
    ic: float  # 信息系数
    ir: float  # 信息比率
    source: str  # 来源（v1 / v9 / v2）
    code: str  # 因子计算代码
```

### Strategy

```python
class Strategy(Protocol):
    """策略接口（v1 src/strategy/base.py 模式）。"""
    def calculate_score(self, df: pd.DataFrame) -> float:
        """计算单只 ETF 的策略评分（0-1）。"""

    def should_buy(self, score: float, context: dict) -> bool:
        """判断是否买入（基于入场过滤 + 市场模式）。"""

    def should_sell(self, position: Position, context: dict) -> bool:
        """判断是否卖出（v1 C20 验证：永远 false）。"""
```

## W4 RV 唯一新写（v9 唯一稳健）

```
W4_RV(t) = std(close(t-19:t)) / std(close(t-39:t)) - 1
```

- OOS/IS = 0.90（v9 验证）
- pass_rate = 18%
- 反向因子：W4 < 0 → 买入（即将反转）

## 关联教训

- L218-L221（alpha 验证 + 样本外 + 数据时长）
- **L223-L227**（C20 颠覆性发现：金三角 + 6 场景剥离）
- L209（8 维度腐化自检）
- L248（27 因子 = 26 继承 + 1 W4 RV 新写）

## Sprint 历史

- Sprint-2 US-006：C21-1 金三角策略
- Sprint-6 US-013：27 因子 + W4 RV（v9 沉淀）
