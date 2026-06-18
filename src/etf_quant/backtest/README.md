# backtest — 回测

> **职责**：回测引擎 + 过拟合验证
> **依据**：v1 src/backtest/engine.py + ComprehensiveValidator 4 验证器

## 核心组件

### ComprehensiveValidator（v1 6/1 增强）

| 验证器 | 阈值 | 权重 |
|--------|------|:---:|
| WalkForwardEngine | min_windows=6 | 0.40 |
| MonteCarloEngine | p-value < 0.05 | 0.15 |
| CrossEtfValidator | min_train=7, min_test=5 | 0.35 |
| 一致性 | - | 0.10 |
| **综合** | pass_threshold=0.6 | 1.0 |

**关键教训（L218-L221）**：
- alpha 验证必须 buy & hold 基准对比
- 样本外测试（中度过拟合检测）
- 长数据 ETF 重跑（短数据高估胜率）

## 接口契约

```python
class BacktestEngine(Protocol):
    def run(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        config: BacktestConfig,
    ) -> BacktestResult:
        """回测单策略单 ETF。"""

class ComprehensiveValidator(Protocol):
    def validate(self, results: list[BacktestResult]) -> ValidationReport:
        """4 验证器综合验证。"""
```

## 关联教训

- v8_sop MC p-value=1.0 教训
- L223-L227（C20 颠覆性发现）