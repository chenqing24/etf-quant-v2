---
name: stock-analyze
description: |
  个股深度分析（单只 vs 板块 vs 大盘）。

  触发场景：
  - 用户要求个股深度分析
  - 用户要求查询 stock_info 表

  执行方式：
    python skills/stock-analyze/scripts/run_analyze.py [action]
  参数：
    action: info | compare | sector（默认 info）

  输出：
    - 个股基本信息（stock_info 表）
    - vs 板块对比
    - vs 大盘对比

  触发词：个股分析 / 股票研究 / stock info
---

# Stock Analyze Skill

按 v2 设计（US-022）。

## 6 段标准注释

用途：
    stock-analyze skill 入口（v1 stock-analyze.py 拆分）。
    整合 stock_info Repository。

被谁调用：
    - QwenPaw 用户直接调用
    - skills/stock-portfolio/scripts/run_portfolio.py（组合配置）

功能说明：
    - info: 单只股票基本信息
    - compare: vs 板块/大盘对比
    - sector: 板块成分股

使用方式：
    python skills/stock-analyze/scripts/run_analyze.py info 600519

依赖：
    - schema/migrations/013/014/015（stock_info + 实时缓存 + 名称重试）

注意事项：
    - v1 stock_info 66 行（已迁移到 v2 schema 012）
    - v2 数据为空（需 v1 → v2 数据迁移）