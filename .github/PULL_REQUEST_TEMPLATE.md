<!-- 按 v1 实践 + v2 改进：5 段 PR 模板 -->

## 【背景】解决什么问题

> 必填。说明 PR 解决的具体问题、关联的 US/Issue、相关讨论。

- US 编号：US-___
- Issue 链接：#___
- 业务场景：

## 【改动】改了什么

> 必填。列出所有改动的文件 + 1 行说明。

- `src/etf_quant/alpha/factor_base.py`：新增 FactorBase 抽象类
- `src/etf_quant/alpha/factors/w4_rv.py`：实现 W4 RV 反转因子
- `tests/unit/alpha/test_w4_rv.py`：单元测试 8 个
- `docs/SPRINT6_US013_DESIGN.md`：设计文档

## 【测试】验证情况

> 必填。说明测试覆盖和回归影响。

- [ ] 单元测试：___ 个新增 / ___ 个通过
- [ ] 集成测试：___ 个新增 / ___ 个通过
- [ ] 回归测试：217/217 全过
- [ ] 8 维自检：100/100
- [ ] pre-commit：通过

## 【自评】6 维（按规则 6.2）

> 必填。诚实评分，不美化。

| 维度 | 评分 |
|------|:----:|
| 1. 设计文档输出（Phase 3） | /20 |
| 2. 调研参考来源明确 | /20 |
| 3. 按 SOP Phase 执行 | /20 |
| 4. 单元测试覆盖核心路径 | /15 |
| 5. 回归测试通过 | /15 |
| 6. Git 小步提交 | /10 |
| **总分** | **/100** |

## 【下一步】后续行动

> 必填。明确到具体动作（不写"继续完善"这类模糊词）。

- [ ] 跑 `pytest tests/ -v` 全过
- [ ] 更新 `CHANGELOG.md` 加新条目
- [ ] merge 后删除 mission 分支
- [ ] 通知 ___ 关注

## 【关联】

- v1 仓归档说明：https://github.com/chenqing24/etf-quant-strategy/blob/main/README.md
- v2 仓 AGENTS.md：[AGENTS.md](../blob/main/AGENTS.md)
- v2 仓 MEMORY.md：[MEMORY.md](../blob/main/MEMORY.md)
