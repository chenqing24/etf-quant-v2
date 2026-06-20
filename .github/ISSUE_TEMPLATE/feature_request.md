---
name: Feature Request
about: 提议新功能
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## 功能描述

清晰简明地描述你希望添加的功能。

## 使用场景

什么场景下会用到？解决什么痛点？

## 期望 API（如适用）

```python
# 期望的 API 形式
from etf_quant.alpha import NewFactor

factor = NewFactor(window=20)
signal = factor.compute(data)
```

## 替代方案

你考虑过哪些替代方案？为什么这个方案更好？

## 优先级

- [ ] P0（核心功能，阻塞开发）
- [ ] P1（重要功能，影响业务）
- [ ] P2（锦上添花）
- [ ] P3（可选优化）

## 关联

- 相关 US: US-___
- 相关 Issue: #___
- 业界参考: [e.g. Murphy 1999 / Bollinger 1980s]

## 验收标准

- [ ] 单元测试覆盖核心路径
- [ ] 文档更新（README / docs/）
- [ ] 8 维自检通过
- [ ] pre-commit 通过
- [ ] CHANGELOG 更新

## 参考来源

- SOP-02：[docs/SOP_02_REFACTOR_DEV.md](../../blob/main/docs/SOP_02_REFACTOR_DEV.md)
- AGENTS.md：[AGENTS.md](../../blob/main/AGENTS.md)
