---
name: quant-knowledge
description: |
  量化知识库（策略 + 教训 + 业界参考）。

  触发场景：
  - 用户要求查询策略知识
  - 用户要求查询教训
  - 用户要求查询业界参考

  执行方式：
    python skills/quant-knowledge/scripts/run_knowledge.py [action]
  参数：
    action: strategy | lesson | reference（默认 strategy）

  输出：
    - 策略列表（从 configs/ 读）
    - 教训列表（从 memory/lessons/ 读）
    - 业界参考（从 v2-roadmap/ 读）

  触发词：量化知识 / 策略 / 教训
---

# Quant Knowledge Skill

按 v2 设计（US-024）。

## 6 段标准注释

用途：
    quant-knowledge skill 入口（v1 L228 教训"先查再答"工具化）。
    整合 strategies + lessons + references。

被谁调用：
    - QwenPaw 用户直接调用
    - skills/etf-research（决策上下文）

功能说明：
    - strategy: 策略列表
    - lesson: 教训列表
    - reference: 业界参考

使用方式：
    python skills/quant-knowledge/scripts/run_knowledge.py strategy
    python skills/quant-knowledge/scripts/run_knowledge.py lesson 240

依赖：
    - configs/*.json
    - memory/lessons/L*.md（104 条教训）
    - v2-roadmap/notes/*.md

注意事项：
    - 教训检索按 L228 教训"先查再答"
    - 不直接修改决策（只查询）