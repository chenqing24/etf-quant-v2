# SOP_03_EXPERIMENT — 实验流程

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：v1 SOP-03 + Sprint-7 业务完整化

---

## 1. 8 步实验流程

```
Step 1: 数据准备（IS-001）
   ↓
Step 2: 候选因子（IS-002）
   ↓
Step 3: 单因子 IC/IR（IS-003）
   ↓
Step 4: 因子组合（IS-004）
   ↓
Step 5: 5 折 WFO（IS-005）
   ↓
Step 6: 蒙特卡洛（IS-006）
   ↓
Step 7: Cross-ETF 泛化（IS-007）
   ↓
Step 8: 综合验证 + 反思（IS-008）
```

## 2. 自动化反思（v9 沉淀）

```python
# scripts/experiment/auto_reflect.py
- 收集每 Sprint 实验结果
- 计算通过率
- 通过率 < 5% 触发反思
- 输出反思报告
```

## 3. IC/IR 评估标准（Grinold-Kahn 2000）

| 指标 | 阈值 | 说明 |
|------|------|------|
| IC > 0.02 | ✅ 可投资 | 行业最低门槛 |
| IR > 0.5 | ✅ 稳健 | 月度 IR |
| OOS/IS > 0.7 | ✅ 抗过拟合 | López de Prado 2018 |
| pass_rate > 10% | ✅ 通过 | 5 折 WFO |

## 4. 防过拟合

1. **样本外测试**（L219）：5 折 WFO
2. **数据时长**（L220）：≥ 5 年
3. **Deflated Sharpe Ratio**：考虑多因子测试的 multiplicity bias
4. **Cross-ETF 泛化**：在不同 ETF 上验证

## 5. 数据时长校验（L220）

```
每只 ETF 实际数据范围：
- 14 只 core 池：≥ 5 年（~1250 个交易日）
- 40 只 reference：≥ 3 年（~750 个交易日）
- 训练期对每只 ETF 单独定义
```

## 6. 实验结果记录

每次实验输出到 `data/experiments/YYYY-MM-DD-HHMM/`：
- `config.yaml`：实验配置
- `results.json`：实验结果
- `reflection.md`：反思文档

## 7. 实验失败处理

- 通过率 < 5%：自动反思
- 通过率 < 1%：abort（暂停当前方向）
- 反思 5 个假设：
  - H1：数据质量问题
  - H2：参数过紧
  - H3：因子选择问题
  - H4：训练期过拟合
  - H5：因子组合冲突
