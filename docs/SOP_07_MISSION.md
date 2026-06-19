# SOP_07_MISSION — Mission 工作流

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：v1 教训 L228 + Sprint-7 业务完整化

---

## 1. Mission 生命周期

```
┌─────────────────────────────────────────────┐
│  Phase 1: PRD 生成（自动）                   │
├─────────────────────────────────────────────┤
│  Phase 2: PRD 用户确认（停止点）              │
├─────────────────────────────────────────────┤
│  Phase 3: SOP 计划（停止点）                  │
├─────────────────────────────────────────────┤
│  Phase 4: 执行（按 Sprint）                  │
├─────────────────────────────────────────────┤
│  Phase 5: 复盘（8 维自评）                    │
├─────────────────────────────────────────────┤
│  Phase 6: Mission 完结（git 同步）            │
└─────────────────────────────────────────────┘
```

## 2. Phase 1：PRD 生成

- 自动根据上下文生成 PRD.md / PRD.json
- 30 US + 5 Sprint
- 输出 docs/PRD.md + docs/PRD.json

## 3. Phase 2：PRD 用户确认

- 用户确认或修改
- 确认后更新 `loop_config.json` 的 `current_phase: execution_confirmed`
- 修改 PRD.json 时诚实改 passes 字段

## 4. Phase 3：SOP 计划（停止点）

- 复制相关 SOP 到仓
- 输出 B 调研 + 设计文档
- 列出涉及模块清单（L117 防半途改造）
- 等待用户拍板

## 5. Phase 4：执行

- 按 Sprint 实施（每 Sprint 一个 PR/tag）
- 每个 US 一个 commit（5 段格式）
- 跑测试 + 8 维自检 + pre-commit

## 6. Phase 5：复盘

- Sprint 复盘模板（docs/sprint-reviews/）
- 8 维自评（满分 100）
- 沉淀教训（MEMORY.md）

## 7. Phase 6：Mission 完结

- 切回 main 分支
- 拉最新
- tag 标记
- 更新 progress.txt
- 通知用户

## 8. 5 道防跑偏机制

| 机制 | 实施 |
|------|------|
| 1. SOP-02 重构 | docs/SOP_02_REFACTOR_DEV.md |
| 2. CHECKPOINT.md | missions/.../CHECKPOINT.md |
| 3. COMMIT 模板 5 段 | COMMIT_TEMPLATE.md |
| 4. 8 维度腐化自检 | scripts/腐化自检.py |
| 5. Sprint 复盘 | docs/sprint-reviews/ |

## 9. 诚实声明（规则 6.1）

每次 Phase 完成后自评：
- 真实业务完成度（非"接口契约"完成度）
- 失败的诚实记录
- 不补文档刷分
