# CHANGELOG

按业界参考（https://keepachangelog.com/zh-CN/1.1.0/）。

## [Unreleased]

### Added
- **Sprint-7 业务完整化**：5 模块业务实现 + 8 核心文档 + 4 项 P1 改进
  - universe/loader.py：ETFListLoader（1486 ETF 加载、14 核心、40 参考）
  - scheduler/cron.py：CronSync（封装 qwenpaw cron API，4 默认 jobs）
  - monitor/data_health.py：DataHealthMonitor（L62 教训动态化阈值）
  - monitor/system_health.py：SystemHealthMonitor
  - monitor/business_alert.py：BusinessAlertMonitor
  - performance/metrics.py：8 大类 43 指标（按 v1 v7 评价体系）
  - notify/dingtalk.py：DingTalkClient
  - notify/notifier.py：SignalNotifier + TradeSignal
  - notify/scenario.py：ScenarioAdapter
  - portfolio/portfolio.py：组合管理（holdings + rebalance + attribution）
  - 8 核心文档：ARCHITECTURE/INTERFACE_CONTRACT/DATA_DICTIONARY + 5 SOP
  - etf-daily 详细输出（11 字段，holdings_count=0 有解释）
  - stock-analyze 错误友好化（available_examples + suggestion）
  - stock-analyze 占位符实现（sector_avg + market_avg）
  - alpha/README 扩 27 因子清单
- **Sprint-6 US-013**：27 因子 + W4 RV（v9 沉淀）
  - alpha/factor_base.py：Factor 抽象基类
  - alpha/factors/：27 因子（26 继承 + 1 W4 RV 新写）
  - alpha/analysis/batch_ic.py：IC/IR 批量计算器
  - tests/unit/alpha + integration/alpha + regression/alpha：46 测试
- Sprint-5 数据迁移：v1 → v2 71034 行真实验证
- Sprint-5 性能基准测试（pytest-benchmark）
- Sprint-4 5 skill 入口（etf-daily/etf-research/stock-analyze/stock-portfolio/quant-knowledge）
- Sprint-2/3 alpha C21-1 策略 + execution tracker + risk PositionGuide + ComprehensiveValidator

### Changed
- v2 schema 完全对齐 v1 业务库（L244 教训：必须比较列名 + 列类型 + 约束）
- init_database.py 幂等性增强（L245 教训：修复脚本必须幂等）

### Fixed
- v1 业务库 20 列缺失（trade_history 5 + decision_snapshot 5 + etf_names 8 + stock_info 2）
- 4 表列名差异（etf_name_metrics/etf_name_retry_queue/realtime_cache/stock_info）

### Security
- pre-commit 钩子真实验证 4 条硬错误（L241 教训）

## [2.0.0a1] - 2026-06-19

### Added
- Sprint-0 机制基础设施（5 道防跑偏机制 + CHECKPOINT + COMMIT_TEMPLATE + 腐化自检）
- Sprint-1 P0 基础设施（data_layer + 4 Repo + 9 迁移 + 41 测试全过）

### Notes
- v2 项目从立项到 Sprint-5 累计：23 US + 176 测试 + 9 commits B 调研 + 12 commits A 实现 + 自评 84→97
- v1 → v2 数据迁移：71034 行
- 8 维度自评客观反映腐化程度（L243 教训）
## [v3] - 2026-06-21 — mission-20260621-193542

### Added (v3 mission 12/12 US 全部 PASS，业务自评 275/225 = 122%)
- **Sprint 1 别名体系**（US-001+002）
  - FactorMetadata 加 aliases 字段（规则 28 必填，默认 [] 黑名单模式）
  - FactorMetadata 加 ic_eval_date 字段（规则 27 必填）
  - 27 因子全填 ALIASES_REGISTRY（业界通用缩写：MA5/RSI/MACD/ATR/BOLL_W/OBV/CCI/WR/VHF/ADX/KDJ）
  - 删除 M6_macd_diff 重复因子（公式与 T1_macd_bar 完全重复：DIF-DEA = MACD 红柱）
  - S2_adx 改名 S2_adx_strength（区别 T4_adx_trend）
  - LEGACY_FACTOR_MAP 兼容旧选择（M6→T1, S2→S2_adx_strength）
- **Sprint 2 IC 评估**（US-003~006）
  - scripts/run_factor_evaluation.py：27 因子在 510300 近 2 年（504 交易日）IC/IR
  - data/factor_icir.csv：27 行 IC 评估结果
  - data/factor_icir_history.csv：append 模式，季度对比
  - BatchICEvaluator 修：单标的场景加滚动窗口（60 日窗，5 日步长）
  - SKILL.md alpha 块显示 IC/IR + AI 推荐 top 3 因子
  - L271 业务自评误判纠正：v2 仓已有 daily 表 69,480 行（不用新建 etf_price_history）
- **Sprint 3 入库校验**（US-007~009）
  - register_factor() 函数校验 4 字段：ic/ir/ic_eval_date/aliases（规则 27 阻断式）
  - FactorICMissingError 异常类
  - _IC_IR_TABLE 动态从 data/factor_icir.csv 读
  - 27/27 因子 IC 完备
- **Sprint 4 季度巡检**（US-010~012）
  - scripts/check_ic_decay.py：对比上季度 IC，|ΔIC|>0.03 或 |IR|<0.5 报警
  - 输出 reports/ic_decay_YYYYMMDD.md + 钉钉 Markdown（按规则 4.3 警告信息）
  - config/cron/ic_decay_check.json：90 天一次 + 钉钉推送

### Changed
- 28 因子 → 27 因子（US-002 删 M6）
- eval_date 含时分（避免同日多次跑合并为 1 次）

### Lessons (L286~L295)
- L286: 因子入库必带 IC/IR/ic_eval_date（阻断式，规则 27 沉淀）
- L287: 季度 IC 巡检 |ΔIC|>0.03 或 IR<0.5 报警（Grinold 经验值）
- L288: 因子命名必带 aliases 业界通用缩写（TA-Lib / akshare 惯例，规则 28 沉淀）
- L289: SOUL.md 规则 6.2 标题重复 → 改名 6.3
- L290: edit_file 前必须 read_file 看真实状态（L260 教训重犯）
- L291: state 文件被 onboard 测试污染，测试不依赖 state 内容
- L292: BatchICEvaluator 单标的要滚动窗口
- L293: business_check.py 找错文件 (factors/__init__.py → factor_base.py)
- L294: eval_date 必须含时分
- L295: 业务自评缺"文档完整性 v3 增量"维度（本次 mission 修正）
