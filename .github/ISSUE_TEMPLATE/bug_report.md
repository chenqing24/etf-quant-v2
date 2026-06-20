---
name: Bug Report
about: 报告 bug 帮助我们改进
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug 描述

清晰简明地描述 bug。

## 复现步骤

1. 执行 `...`
2. 输入 `...`
3. 看到 `...`
4. 期望 `...`

## 预期行为

清晰简明地描述你期望发生什么。

## 实际行为

实际发生了什么（包括错误堆栈、截图）。

## 环境信息

- OS: [e.g. Ubuntu 22.04 / macOS 14 / Windows 11]
- Python 版本: [e.g. 3.11.5]
- etf-quant-v2 版本: [e.g. 2.0.0a1]
- 关键依赖版本: [e.g. akshare 1.18.63 / pandas 2.0.3]

```bash
python -c "import sys; print(sys.version)"
pip show etf-quant-v2 2>/dev/null || pip show -f etf-quant-v2 | head -3
```

## 关联

- 相关 Issue: #___
- 相关 PR: #___
- 相关 US: US-___

## 严重程度

- [ ] Critical（核心功能不可用 / 数据丢失 / 安全漏洞）
- [ ] High（主要功能异常）
- [ ] Medium（次要功能异常）
- [ ] Low（文档错误 / UI 优化）

## 截图 / 日志

如适用，添加截图或粘贴关键日志（**脱敏后**）。

## 参考来源

- SOP-02：[docs/SOP_02_REFACTOR_DEV.md](../../blob/main/docs/SOP_02_REFACTOR_DEV.md)
- SECURITY.md：[SECURITY.md](../../blob/main/SECURITY.md)
