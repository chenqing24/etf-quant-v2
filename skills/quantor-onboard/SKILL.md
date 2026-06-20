---
name: quantor-onboard
description: |
  散户从 0 到 1 建立量化模型（择股 + 择时 + 仓位管理）的对话式引导。

  触发场景：
  - 用户要求从 0 建立量化模型
  - 用户要求对话式引导（择股/择时/仓位）
  - QwenPaw cron（暂未配置）

  执行方式：
    python skills/quantor-onboard/scripts/run_onboard.py [action]
  参数：
    action: universe | alpha | risk | onboard（默认 onboard）

  输出：
    - 3 块对话式引导（4 步：原理 → 默认 → 调整 → 验证）
    - state.json 持久化（支持中断 / 跳过 / 回头）

  触发词：帮我从 0 建立模型 / 我想调整 ETF 池 / 我想加因子 / 我要调止损
---

# Quantor Onboard Skill

按 Mission quantor-onboard（mission-20260620-235022）设计。

## 6 段标准注释

用途：
    quantor-onboard skill 入口。
    让散户通过对话完成量化模型 3 块的建立：择股 + 择时 + 仓位管理。

被谁调用：
    - QwenPaw 对话（用户说"帮我从 0 建立模型"）
    - 用户直接调用
    - v2 散户版指南的入口（NEW_USER_GUIDE_INVESTOR.md）

功能说明：
    - universe: 择股（建立 ETF 池）
    - alpha: 择时（多因子 + 加自己的因子）
    - risk: 仓位管理（交易纪律）
    - onboard: 整合（按 3 块顺序引导）

使用方式：
    python skills/quantor-onboard/scripts/run_onboard.py
    python skills/quantor-onboard/scripts/run_universe.py
    python skills/quantor-onboard/scripts/run_alpha.py
    python skills/quantor-onboard/scripts/run_risk.py

依赖：
    - src/etf_quant/universe/loader.py（ETFListLoader）
    - src/etf_quant/alpha/factors/（27 因子 + registry）
    - src/etf_quant/risk/position_guide.py（22 字段）
    - src/etf_quant/data_layer/（DataLoader/DataWriter）

注意事项：
    - AI 是脚手架，不替用户做决定
    - 每步 ≥100 字解释 + 含数据点 + 不给 yes/no
    - 综合分阈值：<0.4 放弃 / 0.4-0.6 大改 / ≥0.6 小资金
    - 业务对象用 pool_role 标记，不删（规则 21）