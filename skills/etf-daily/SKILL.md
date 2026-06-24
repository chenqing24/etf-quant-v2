---
name: etf-daily
description: |
  运行 ETF 量化投资决策（每日/完整评估/历史）。

  触发场景：
  - 用户要求运行 ETF 每日决策
  - 用户要求 ETF 评估/回测
  - 用户要求查看 ETF 历史
  - QwenPaw cron 每日 14:30 工作日

  执行方式：
    # 方式 1：直接 python（输出控制台 + 报告文件）
    python skills/etf-daily/scripts/run_daily.py [mode]

    # 方式 2：bash 包装器（输出三份分离日志：decision/stdout/stderr）
    bash scripts/run_and_log.sh [mode]

  参数：
    mode: daily | eval | history（默认 daily）
    --db-path: 数据库路径（默认用 ETF_QUANT_DB_PATH 环境变量或项目根 data/etf.db）
    --report-dir: 报告输出根目录（默认 reports/etf-daily/YYYY-MM-DD/）
    LOG_DIR: bash 包装器日志目录（默认 reports/etf-daily-logs/YYYY-MM-DD/）

  输出：
    - 控制台：JSON 格式决策结果
    - 文件 1：reports/etf-daily/YYYY-MM-DD/{mode}_{HHMMSS}.json（L321 教训 P1-2）
    - 文件 2（bash 包装器）：三份分离日志
        - decision_{mode}_{HHMMSS}.json（机器读）
        - stdout_{mode}_{HHMMSS}.log（人读）
        - stderr_{mode}_{HHMMSS}.log（debug）
    - 钉钉推送（买卖信号 + 警告）
    - 决策快照（decision_snapshot.json 落库）

  触发词：ETF 决策 / ETF 每日检查 / 跑 ETF / ETF 评估
---

# ETF Daily Skill

按 v2 设计（EXECUTION_REFACTOR_DESIGN.md + US-020）。

## 6 段标准注释

用途：
    etf-daily skill 入口（v1 etf-quant-decision -m daily 拆分）。
    整合 alpha + portfolio + risk + notify 模块。

被谁调用：
    - QwenPaw cron 每日 14:30 工作日
    - skills/etf-research/scripts/run_validate.py
    - 用户直接调用

功能说明：
    - daily: 每日决策（采集+分析+钉钉+快照）
    - eval: 完整评估（多时段回测）
    - history: 查询历史

使用方式：
    python skills/etf-daily/scripts/run_daily.py daily
    python skills/etf-daily/scripts/run_daily.py eval
    python skills/etf-daily/scripts/run_daily.py history

依赖：
    - src/etf_quant/alpha/strategy_c21.py（C21-1 策略）
    - src/etf_quant/data_layer/（4 Repo）
    - src/etf_quant/risk/position_guide.py（22 字段）
    - src/etf_quant/notify/（钉钉推送）
    - configs/c21_strategy.json（v1 真实策略配置）

注意事项：
    - v1 真实数据通过 etf_data_live/etf.db 读取（v2 schema 已对齐 v1）
    - 钉钉推送 target-session=WoXtGw==（L222 教训）
    - 决策快照持久化到 decision_snapshot 表（schema 007+009）
