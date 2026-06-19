---
name: etf-research
description: |
  ETF 深度研究（回测 + 验证 + 评分）。

  触发场景：
  - 用户要求 ETF 深度分析
  - 用户要求 ETF 策略验证
  - QwenPaw cron 每周日 14:30 完整评估

  执行方式：
    python skills/etf-research/scripts/run_validate.py [action]
  参数：
    action: validate | factor | backtest（默认 validate）

  输出：
    - 综合验证报告（pass/fail + composite_score）
    - 因子分解（4 验证器详细评分）
    - 回测样本（最近 10 个）

  触发词：ETF 深度研究 / ETF 验证 / ETF 评分
---

# ETF Research Skill

按 v2 设计（US-021）。

## 6 段标准注释

用途：
    etf-research skill 入口（v1 etf-quant-decision -m eval 拆分）。
    整合 backtest + ComprehensiveValidator 模块。

被谁调用：
    - QwenPaw cron 每周日 14:30
    - skills/etf-daily/scripts/run_daily.py (eval mode)
    - 用户直接调用

功能说明：
    - validate: 综合验证（4 验证器）
    - factor: 因子分解
    - backtest: 回测样本

使用方式：
    python skills/etf-research/scripts/run_validate.py validate
    python skills/etf-research/scripts/run_validate.py factor

依赖：
    - src/etf_quant/backtest/comprehensive_validator.py（4 验证器）
    - src/etf_quant/alpha/strategy_c21.py（C21-1）
    - src/etf_quant/data_layer/（4 Repo）

注意事项：
    - v1 6/1 增强版配置（pass_threshold=0.6）
    - 输出按规则 6 简洁（结论先行）