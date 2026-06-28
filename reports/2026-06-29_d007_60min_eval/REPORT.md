# D-007 60min 因子评估报告

**日期**：2026-06-29 07:01:33
**评估脚本**：`scripts/eval_60min_factors.py`
**前瞻窗口**：12 bar (≈3.0 天)
**评估 ETF 数**：14 / 14

## 4 因子 IC 汇总

| 因子 | IC 均值 | IC 标准差 | IR | 样本数 |
|------|---------|-----------|-----|--------|
| H1_intraday_trend | 0.1387 | 0.0299 | 4.6455 | 14 |
| H2_volume_breakout | -0.0090 | 0.0587 | -0.1533 | 14 |
| H3_boll_width_pct | 0.0759 | 0.0468 | 1.6232 | 14 |
| H4_price_volume_corr | 0.0068 | 0.0529 | 0.1289 | 14 |

## 业务解读

- **H1 日内趋势**：捕捉盘中单边趋势（Barber 2005）
- **H2 量能突破**：捕捉资金异动（TA-Lib AD 类似）
- **H3 布林挤压**：捕捉变盘前兆（Bollinger 2001）
- **H4 量价背离**：捕捉趋势转折（Granville 1976）

## 5 项隔离原则（D-007 强约束）

1. ✅ 不参与实时决策（HOLD/BUY/SELL 不读 60min score）
2. ✅ 不污染 8 因子权重（独立 FactorSet `sixty_min_4f`）
3. ✅ 不参与 rank（不进入横截面打分）
4. ✅ 不参与止盈/止损
5. ✅ 不进 decision_snapshot（只入 IC history 表）

## 后续建议

**IC 显著因子（|IC| > 0.02）**：
- H1_intraday_trend（IC=0.1387）
- H3_boll_width_pct（IC=0.0759）

**建议**：保留为研究素材，季度重跑 IC 评估（D-013.5）
