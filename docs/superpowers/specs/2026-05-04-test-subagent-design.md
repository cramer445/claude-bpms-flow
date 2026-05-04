# 测试 Subagent 设计文档

日期: 2026-05-04
主题: 代码编写后自动测试 subagent

## 概述

创建一个专门的测试 subagent，在代码编写完成后自动运行测试，确保代码质量。

## 触发机制

通过 `.claude/settings.json` 中的 `post-commit` hook 触发。每次 `git commit` 完成后，自动触发测试 subagent。

`git commit` 是一个自然的工作里程碑，标志着一个独立任务/功能的完成。一次完整的需求实现过程中，只会在最终提交时触发一次测试，避免频繁打断开发流程。

## 测试流程：分层递进

测试分三层，逐层递进执行，任一阶段失败即停止：

1. **单元测试** (`pytest -m unit`)
   - 通过 → 进入集成测试
   - 失败 → 报告结果，停止

2. **集成测试** (`pytest -m integration`)
   - 通过 → 进入端到端测试
   - 失败 → 报告结果，停止

3. **端到端测试** (`pytest -m e2e`)
   - 报告结果

## 上下文隔离

subagent 通过 Agent tool 启动，拥有独立上下文：

- 接收自包含的 prompt（包含被修改文件列表、测试运行指令）
- 测试详细日志不泄露到主对话
- 仅返回简短摘要到主会话

## 失败处理策略

- 任何一层测试失败，立即停止后续测试
- 返回失败报告：包含失败的测试名、错误类型、文件路径、行号
- 不自动修复代码，由开发者决定后续操作

## 输出格式

```
测试报告:
- 单元测试: ✅ 通过 (N tests)
- 集成测试: ❌ 失败 (1 failed)
  └─ test_xyz: AssertionError at tests/integration/xxx.py:42
- 端到端测试: ⏭ 跳过（集成测试未通过）
```

## 技术实现

- 在 `.claude/settings.json` 中配置 `post-commit` hook
- hook 中定义一个 prompt，要求 Claude 使用 Agent tool 启动测试 subagent
- subagent 使用 `general-purpose` 类型，拥有独立上下文
- subagent 内部调用 Bash 运行 pytest，分层递进
- 失败时解析 pytest 输出，提取关键信息
- 仅返回简短摘要到主会话
