---
name: quantor-onboard
description: |
  散户从 0 到 1 建立量化模型（择股 + 择时 + 仓位管理）的对话式引导。

  触发场景：
  - 用户要求从 0 建立量化模型
  - 用户要求对话式引导（择股/择时/仓位）
  - QwenPaw cron（暂未配置）

  执行方式：
    python skills/quantor-onboard/scripts/run_onboard.py onboard [--block X] [--confirm]  # L274：原 [action] 占位符跑不通，已改
  参数：
    onboard | status | reset | skip | back
    --confirm: 确认完成当前块并推进到下一块（US-005）
    --block {universe,alpha,risk}: 指定块（skip/back 用）

  触发词：帮我从 0 建立模型 / 我想调整 ETF 池 / 我想加因子 / 我要调止损

  输出：
    - 3 块对话式引导（4 步：原理 → 默认 → 调整 → 验证）
    - state.json 持久化（支持中断 / 跳过 / 回头）
    - 每个 modify/add 命令真改 etf.db / FACTOR_REGISTRY（不是只打印文案）
---

# Quantor Onboard Skill

按 Mission quantor-onboard（mission-20260621-091017）US-001~012 设计。
v2 修复 v1 的 5 个致命 bug（--help 崩溃 / 哑参数 / 一键通关）。

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
    - onboard: 整合（按 3 块顺序引导，逐块 confirm）

使用方式：

### 1. 整合入口（按 3 块顺序）
```bash
python skills/quantor-onboard/scripts/run_onboard.py reset  # 清空 state
python skills/quantor-onboard/scripts/run_onboard.py onboard  # 跑当前块第 1 步（不推进）
python skills/quantor-onboard/scripts/run_onboard.py onboard --confirm  # 确认完成并推进
python skills/quantor-onboard/scripts/run_onboard.py status  # 看状态
```

### 2. universe 单独用（择股）
```bash
python skills/quantor-onboard/scripts/run_universe.py interactive  # 4 步引导（一次）
python skills/quantor-onboard/scripts/run_universe.py explain       # 第 1 步：原理
python skills/quantor-onboard/scripts/run_universe.py default       # 第 2 步：v2 默认池（14 core + 40 ref）
python skills/quantor-onboard/scripts/run_universe.py modify --add 159915 --remove 512170  # 第 3 步：调池（真改 etf.db）
python skills/quantor-onboard/scripts/run_universe.py verify --add 159915 --remove 512170  # 第 4 步：验证改动
python skills/quantor-onboard/scripts/run_universe.py test          # 单元测试
```

### 3. alpha 单独用（择时）
```bash
python skills/quantor-onboard/scripts/run_alpha.py interactive                  # 4 步引导
python skills/quantor-onboard/scripts/run_alpha.py explain                      # 第 1 步：什么是因子 + C21-1
python skills/quantor-onboard/scripts/run_alpha.py factors                      # 第 2 步：v2 27 因子
python skills/quantor-onboard/scripts/run_alpha.py add --factor MY_RSI_30       # 第 3 步：加因子（真注册 FACTOR_REGISTRY）
python skills/quantor-onboard/scripts/run_alpha.py validate --factor MY_RSI_30  # 第 4 步：综合分
python skills/quantor-onboard/scripts/run_alpha.py test                         # 单元测试
```

### 4. risk 单独用（仓位管理）
```bash
python skills/quantor-onboard/scripts/run_risk.py interactive                                          # 4 步引导
python skills/quantor-onboard/scripts/run_risk.py explain                                              # 第 1 步：什么是纪律 + 仓位逻辑顺序
python skills/quantor-onboard/scripts/run_risk.py default                                              # 第 2 步：v2 默认 6 个关键纪律
python skills/quantor-onboard/scripts/run_risk.py modify --stop_loss -0.05 --max_position_pct 0.30    # 第 3 步：调纪律（真改 state/risk_config.json）
python skills/quantor-onboard/scripts/run_risk.py verify                                               # 第 4 步：验证改动
python skills/quantor-onboard/scripts/run_risk.py test                                                 # 单元测试
```

依赖：
    - src/etf_quant/universe/loader.py（ETFListLoader）
    - src/etf_quant/alpha/factors/（27 因子 + registry）
    - src/etf_quant/risk/position_guide.py（22 字段）
    - src/etf_quant/data_layer/（DataLoader/DataWriter）
    - etf.db（etf_names 表，pool_role + is_reference 字段）

注意事项：
    - AI 是脚手架，不替用户做决定
    - 每步 ≥100 字解释 + 含数据点 + 不给 yes/no
    - 综合分阈值：<0.4 放弃 / 0.4-0.6 大改 / 0.6-0.7 小资金 / ≥0.7 继续观察
    - 业务对象用 pool_role 标记，不删（规则 21）
    - onboard 命令必须 --confirm 才推进（US-005）
    - 所有 modify/add 命令真持久化（不是只打印文案）
    - alpha_state.json 持久化散户因子，restart 自动恢复

文件位置：
    skills/quantor-onboard/
    ├── SKILL.md (本文件)
    ├── state.json (onboard 进度：current_block + completed_blocks)
    └── state/
        ├── universe_state.json (择股改动)
        ├── alpha_state.json (因子注册，含 user_factors list)
        ├── risk_config.json (仓位纪律)
        └── audit_log.jsonl (所有改动留痕)