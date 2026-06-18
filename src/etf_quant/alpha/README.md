# alpha — 信号/因子

> **职责**：因子计算、信号生成、策略实现
> **依据**：v1 src/strategy/scorer.py + src/indicators/ + 6/16 C20 颠覆性发现

## 核心原则（v1 教训 L225 沉淀）

**alpha 真正来源 = 入场过滤 + 永远满仓**，不是 4 因子组合。

```
max_hold_days = 99999      # C11 修复（持仓管理核心）
entry: BOLL_strict_middle + close > MA60  # C21 网格最优
exit: enabled = false       # C20 验证（卖出是 alpha 拖累）
```

## 接口契约

### Factor

```python
@dataclass
class Factor:
    """单个因子（27 个候选，v9 沉淀）。"""
    name: str
    description: str
    ic: float  # 信息系数
    ir: float  # 信息比率
    source: str  # 来源（v9-us026-027 等）
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

## 27 因子清单（v9 沉淀）

| 编号 | 因子 | IC | IR | 状态 |
|------|------|:---:|:---:|:---:|
| B1 | 布林上轨突破 | 0.0484 | 0.99 | ✅ |
| V1 | 放量 | 0.0369 | 0.84 | ✅ |
| T1 | MACD 红柱 | 0.0423 | 1.44 | ✅ |
| T3 | SAR 趋势 | 0.0252 | 1.02 | ✅ |
| T4 | ADX 趋势 | 0.0248 | 0.77 | ✅ |
| M2 | 5 日动量 | 0.0186 | 0.89 | ✅ |
| **W4** | **RV 反转** | - | - | **🟢 v9 唯一稳健** |

## 关联教训

- L218-L221（alpha 验证 + 样本外 + 数据时长）
- **L223-L227**（C20 颠覆性发现：金三角 + 6 场景剥离）
- L209（8 维度腐化自检）