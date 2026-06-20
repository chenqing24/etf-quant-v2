# SOP 文档索引

> 按 v1 实践（v1 SOP_INDEX.md）—— SOP 集中入口，快速定位标准流程。
>
> 版本：v2.0 | 创建：2026-06-20 | 维护人：福猫管家 🐱

---

## 一、SOP 总览

| # | 文档 | 用途 | 触发场景 |
|---|------|------|----------|
| **SOP-01** | [数据采集规范](./SOP_01_DATA.md) | 数据获取/存储/查询 | 新数据源接入 / 数据质量异常 |
| **SOP-02** | [重构与修复开发流程](./SOP_02_REFACTOR_DEV.md) | 问题发现→修复→验证 | 发现 bug / 需要重构 |
| **SOP-03** | [实验流程](./SOP_03_EXPERIMENT.md) | 实验设计→执行→分析 | 批量因子/组合测试 |
| **SOP-04** | [数据源接入规范](./SOP_04_DATASOURCE.md) | 接入新数据源 | 新 API/数据源验证 |
| **SOP-05** | [备份与恢复](./SOP_05_BACKUP.md) | 数据备份/灾难恢复 | 数据库升级 / 误操作 |
| **SOP-06** | [脱敏规范](./SOP_06_DESENSITIZE.md) | PII 脱敏 / 数据分享 | 提交数据 / 截图 |
| **SOP-07** | [Mission 流程](./SOP_07_MISSION.md) | 多 Sprint 协作 | 启动新 Mission |

---

## 二、SOP 之间的关系

```
┌────────────────────────────────────────────────────────────┐
│  SOP-01 (数据)  ←  SOP-03 (实验)  ←  SOP-07 (Mission)     │
│       ↓                  ↓                  ↓              │
│  SOP-04 (数据源)  SOP-02 (重构)   SOP-05 (备份)            │
│       ↓                  ↓                  ↓              │
│  SOP-06 (脱敏) ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                 │
└────────────────────────────────────────────────────────────┘
```

- **SOP-01**：所有数据相关任务的基础
- **SOP-02**：发现问题后的标准修复流程（最常用）
- **SOP-03**：批量实验的标准化（避免每次发明轮子）
- **SOP-04**：新数据源必须先验证再使用
- **SOP-05**：所有数据库变更前必须备份
- **SOP-06**：数据分享/截图前必须脱敏
- **SOP-07**：跨 Sprint / Mission 的协作流程

---

## 三、按场景查找

### 3.1 接到新需求时

1. 读 [PRD.md](PRD.md) 确认 US 定义
2. 找对应 SOP（通常 SOP-02）
3. 按 SOP Phase 1-6 执行

### 3.2 接到 bug 报告时

1. 复现 bug（SOP-02 Phase 1）
2. 根因分析（SOP-02 Phase 2）
3. 方案设计（SOP-02 Phase 3）
4. 修复 + 测试（SOP-02 Phase 4-5）
5. 复盘交付（SOP-02 Phase 6）

### 3.3 新数据源接入时

1. 调研候选数据源（SOP-04 Phase 1）
2. 文档化字段格式（SOP-04 Phase 2）
3. 写测试用例验证（SOP-04 Phase 3）
4. 集成到 DataSourceRouter（SOP-04 Phase 4）

### 3.4 数据备份时

1. 选备份策略（SOP-05）
2. 执行备份
3. 验证可恢复
4. 记录到 audit log

---

## 四、SOP 维护

- **last_review**：每周检查
- **review_interval**：weekly
- **变更流程**：PR + 至少 1 个 reviewer

---

## 五、v1 SOP 映射

| v1 SOP | v2 SOP | 差异 |
|--------|--------|------|
| SOP_01_DATA_MINING | SOP_01_DATA | 整合数据挖掘+数据规范 |
| SOP_02_REFACTOR_DEV | SOP_02_REFACTOR_DEV | 一致（v2 直接继承） |
| SOP_03_EXPERIMENT | SOP_03_EXPERIMENT | 一致 |
| SOP_04_DATA_SOURCE | SOP_04_DATASOURCE | 略调整 |
| SOP_05_DUAL_MODE | （未继承） | v9 模式已废弃 |
| SOP_06_MANUAL_TRADE | SOP_06_DESENSITIZE | 主题调整（脱敏 vs 手动交易） |
| SOP_07_V9_MISSION_INTEGRATION | SOP_07_MISSION | 主题扩展 |

---

## 参考来源

- v1 SOP_INDEX.md（v1 仓 zip 验证存在，9 个 SOP）
- v2 仓 docs/ 当前有 7 个 SOP
- SOP 命名：v1 用 `_` 连接，v2 用 `_` 保持一致
