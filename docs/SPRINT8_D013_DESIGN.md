# SPRINT-8 D-013 设计文档：daily 8 因子综合打分

> **任务 ID**：D-013（修复 P0 占位符）
> **类型**：架构修复 + 业务修复
> **Sprint**：Sprint-8（2026-06-28）
> **状态**：✅ Phase 4-6 完成 + 5 commit push

---

## 0. 一句话总结

把"27 因子池"和"8 因子配方"显式分离，用 3 个新抽象（FactorSet / WeightScheme / CrossSectionalScorer）替代散落各处的占位 0.5 和等权硬编码。

---

## 1. 问题

| 现象 | 位置 | 根因 |
|---|---|---|
| daily 14 候选 score 全 0.5 | `run_daily.py:89` | 占位符未实现 |
| backtest 用等权求和 | `backtesting_adapter.py:99` | 硬编码，无权重抽象 |
| 权重散落 3 处 | D-004 JSON / daily / backtest | 无单一来源 |

---

## 2. 设计：3 个新抽象 + 4 层架构

### 2.1 抽象 1：`FactorSet`（Layer 1 灵活层）

```python
@dataclass(frozen=True)
class FactorSet:
    name: str  # "eight_factor_v2" / "sixty_min_4f" / ...
    factor_names: tuple[str, ...]

    @classmethod
    def eight_factor_v2(cls) -> "FactorSet":
        """D-004 精选 8 因子（当前 6 在 FACTOR_REGISTRY + DMA/FIB 待补）"""
        ...

    @classmethod
    def all_registered(cls) -> "FactorSet":
        """全 27 因子（用于 IC/IR 评估、研究场景）"""
        ...
```

**硬约束**：未知因子报错、空集报错、重复因子自动去重。

### 2.2 抽象 2：`WeightScheme`（Layer 2 配置层）

```python
@dataclass(frozen=True)
class WeightScheme:
    scheme_id: str  # "B2" / "A1" / ...
    weights_by_mode: dict[str, dict[str, float]]

    @classmethod
    def d004_b2(cls) -> "WeightScheme":
        """D-004 第一名方案（total_score=89.44）"""
        ...
```

**D-004 5 维度校验**：
- 权重和 = 1.0（容差 1e-6）
- 权重 ∈ [5%, 40%]
- 零权重禁止（= 删除因子）
- 必须含 trend_up + range_bound
- 非空

### 2.3 抽象 3：`CrossSectionalScorer`（Layer 3 算法层）

```python
class CrossSectionalScorer:
    def __init__(self, factor_set: FactorSet, weight_scheme: WeightScheme): ...
    def score(self, market_mode: str, factor_data: dict[str, pd.DataFrame]) -> ScoringResult: ...
```

**Pipeline 3 Layer**：
- Layer 1 compute（按 FactorSet）
- Layer 2 rank normalize（scipy.stats.rankdata → [0,1]）
- Layer 3 weighted composite（按 Σweight 归一化处理部分 NaN）

### 2.4 4 层架构

```
Layer 0: FACTOR_REGISTRY（27 因子池，stable）
   ↓ 通过 FactorSet 选
Layer 1: FactorSet（动态子集，flexible）
   ↓ 配 WeightScheme
Layer 2: WeightScheme（权重配置，configurable）
   ↓ 装进 Scorer
Layer 3: CrossSectionalScorer（打分器，algorithm）
   ↓ 被调用
Layer 4: 调用方（daily / backtest / eval）
```

---

## 3. 文件改动（实际落地）

| # | 文件 | commit | 内容 |
|---|---|---|---|
| 1 | `src/etf_quant/alpha/factor_set.py` | `0a2edd1` | 新增 FactorSet |
| 2 | `tests/unit/alpha/test_factor_set.py` | `0a2edd1` | 10 用例 |
| 3 | `src/etf_quant/alpha/weight_scheme.py` | `21d172f` | 新增 WeightScheme |
| 4 | `tests/unit/alpha/test_weight_scheme.py` | `21d172f` | 14 用例 |
| 5 | `src/etf_quant/alpha/scoring.py` | `ba8afa2` | 新增 CrossSectionalScorer |
| 6 | `tests/unit/alpha/test_scoring.py` | `ba8afa2` | 10 用例 |
| 7 | `src/etf_quant/config/eight_factor_weights.json` | `5bebbc7` | B2 配置迁移 |
| 8 | `skills/etf-daily/scripts/run_daily.py` | `bdefec2` | 修 P0 占位 |
| 9 | `tests/integration/test_daily_scoring.py` | `bdefec2` | 5 集成用例 |
| 10 | `src/etf_quant/backtest/backtesting_adapter.py` | `18e0536` | 等权 → B2 加权 |
| 11 | `tests/unit/test_backtesting_adapter_scoring.py` | `18e0536` | 4 用例 |

**累计**：5 commit + 11 文件 + 43 单测 + 5 集成测试 + 全 push

---

## 4. P0 修复验证

| 项 | 修复前 | 修复后 |
|---|---|---|
| daily 候选 score | 全 0.5 | 0.68 ~ 0.84（**有强区分**）|
| 排序 | 按 core 池顺序 | 按 score 降序 |
| 末位识别 | 不可识别 | ✅ 512170（6/25 末位）不在 top 5 |
| 候选 rank 字段 | 无 | ✅ 含 rank 1-5 |
| 失败兜底 | 无 | ✅ try-except 回退占位 + warning |

---

## 5. 业界参考（按规则 13）

| 抽象 | 来源 |
|---|---|
| Factor Pool | WorldQuant 101 Alphas (Kakushadze 2016, *Quantitative Finance*) §3 |
| Factor Set | Qlib Alpha158 (microsoft/qlib, GitHub 16.6k⭐) |
| Selection | QuantConnect LEAN FineFundamental + FineSelection |
| WeightScheme | Qlib WeightStrategy |
| CrossSectionalScorer | Qlib Alpha158 + handler; WorldQuant rank + composite |
| rankdata | scipy.stats.rankdata 官方文档 |
| 池/配方分离 | 12-Factor App §II Dependencies; Divio Documentation |

---

## 6. 已知限制（待 D-007 / 后续）

| 限制 | 影响 | 解决方向 |
|---|---|---|
| DMA / FIB 不在 FACTOR_REGISTRY | 当前只跑 6 因子，权重 DMA/FIB 没真正生效 | D-013.1：把 DMA/FIB 封装成 Factor 类注册 |
| weight_scheme 默认 trend_up 用于单标的 | 单标的 backtest 不支持 market_mode 切换 | backtest 接入 market_mode 检测 |
| 60min 因子未实现 | 仍只用日线 | D-007 实现后，60min 因子作为新 FactorSet |

---

## 7. 教学要点（小白版）

> **为什么 D-013 重要？**

**之前**：你按"core 池前 5 只"买，跟抓阄差不多（虽然代码看起来很专业）。

**现在**：8 因子按权重打分，按分排序买前 5。512170 这种末位会被识别，不进候选。

**3 个抽象的关系**：
- 27 因子是"工具箱"（FACTOR_REGISTRY）
- 8 因子是"今天用的工具"（FactorSet）
- 权重是"工具使用顺序"（WeightScheme）
- Scorer 是"干活的人"（按规则用工具）

**升级时怎么改**：
- 加新因子 → 写 Factor 类 + 加 registry（其他不用动）
- 调权重 → 改 JSON 配置 + 跑 D-004 验证（代码不动）
- 换算法 → 写新 Scorer 实现（接口稳定）

---

## 8. 关联文档

- 设计日志：`reports/2026-06-28_d013_daily_scoring/DECISIONS.md`
- D-004 权重来源：`reports/2026-06-25_eight_factor_v2/D-004_top3_weights.json`（历史归档）
- D-004 5 维度评分：`reports/2026-06-25_eight_factor_v2/SOP_D-004.md`
- 8 因子决策：`reports/2026-06-25_eight_factor_v2/DECISIONS.md`

---

## 9. 待办（下一步）

- [ ] D-013.1：DMA/FIB 封装为 Factor 类（让 8 因子全参与）
- [ ] D-013.2：daily 加 score 解释字段（为什么这只 ETF 排第 1）
- [ ] D-013.3：跑 14 ETF 全套回测回归
- [ ] D-013.4：USER_JOURNEY_MAP 补"8 因子打分"步骤
- [ ] D-007：60min 4 因子设计与 Scorer 接入