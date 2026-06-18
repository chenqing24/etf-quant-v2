# portfolio — 仓位/组合

> **职责**：仓位构建、调仓、持仓管理
> **依据**：v1 src/strategy/executor.py + C11 max_hold=99999 修复

## 核心原则

- **单一持仓 = 历史错误**（v1 US-005 教训，max_holdings=2 是 v8 沿用）
- **永远满仓**（C20 验证）—— 不是追高，是**永远不卖**
- **调仓周期 = 强制**（v1 config.rebalance）

## 接口契约

```python
class PortfolioBuilder(Protocol):
    """仓位构建器（v1 Position 模式）。"""
    def build(
        self,
        signals: list[Signal],
        positions: list[Position],
        capital: float,
        max_holdings: int = 2,  # v8 沿用（不是 1）
        market_regime: str = "震荡市",
    ) -> list[Order]:
        """根据信号 + 持仓 + 资金构建下单列表。"""

class PositionManager(Protocol):
    """持仓管理（v1 src/strategy/lifecycle.py 模式）。"""
    def update(self, position: Position, price: float) -> Position:
        """更新持仓市值、盈亏、持仓天数。"""

    def check_max_hold(self, position: Position) -> bool:
        """检查是否到期（v1 教训 L216 持仓管理 > 因子）。"""
```

## 关联

- `execution/tracker.py` — 持仓记录
- `risk/position_guide.py` — 22 字段决策
- `data_layer/contracts.py` — PositionStateSchema

## 关联教训

- L67（用户功能=补救措施）
- L69（擅自假设默认值错）
- L216（持仓管理 > 因子）
- L217（max_hold_days 修复验证）