# CLAUDE.md

本文档为 Claude Code 在此项目中的工作提供指引。

## 项目概述

BPMS 流程引擎服务 — 一个业务工作流/流程管理服务。

## 技术栈

- Python >= 3.10
- pytest（测试框架，支持 unit / integration / e2e 分层）
- ruff（代码检查与格式化）

## 快速命令

```bash
# 初始化虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 启动
python -m bpms
```

## 项目结构

```
├── docs/              # 项目文档
├── src/bpms/          # 源代码
├── tests/             # 测试代码
│   ├── unit/          # 单元测试
│   ├── integration/   # 集成测试
│   └── e2e/           # 端到端测试
├── .gitignore
├── pyproject.toml     # 项目配置
└── requirements-dev.txt
```

## 开发规范

### 编码

- 遵循 PEP 8，使用 ruff 检查
- 提交信息使用简明中文，描述"做了什么"及"为什么"
- 所有注释和文档使用中文
- 最小化代码：只实现需求，不做多余抽象、多余容错

### 修改原则

- 只改动必要的文件，不要顺手优化无关代码
- 改动产生的废弃引用需清理，已有的历史遗留代码不动
- 代码风格与现有代码保持一致

### 提交规范

每个独立步骤完成后，执行以下命令提交并推送：

```bash
git add <变更文件>
git commit -m "<简明中文提交信息>"
git push
```

- 提交信息使用简明中文，描述"做了什么"及"为什么"
- 每个步骤一个独立提交，不要合并多个步骤
- 提交前确认变更范围正确

### 自动测试

项目配置了 `git commit` 后自动运行测试的 hook（详见 `.claude/settings.json`）。
每次 commit 后，hook 会自动分层运行 pytest（unit → integration → e2e），测试结果会注入到对话中。

**测试结果查看方式：**

| 内容 | 路径 |
|------|------|
| 摘要（注入 Claude 上下文） | 对话中自动显示 |
| 详细 pytest 输出 | `.claude/hooks/last-test-output.log` |

**如果测试失败：**
1. 阅读对话中的测试报告摘要，确认哪一层失败
2. 运行 `cat .claude/hooks/last-test-output.log` 查看详细错误信息
3. 修复代码后重新 commit，hook 会再次触发测试

**注意：** 如果某一层没有对应标记的测试（exit code 5），视为通过，不阻塞后续层级。

**重要：** 所有测试执行由 hook 自动处理。写代码时不需要手动运行 pytest，commit 后 hook 会自动触发测试并报告结果。不要在实现功能的过程中穿插运行测试命令。

### 需求迭代流程

正常的功能迭代遵循以下循环：

1. **理解需求** — 明确目标和验证标准，多步任务先列简要计划
2. **编写测试** — 在 `tests/` 对应目录下添加测试用例（标注 `@pytest.mark.unit` 等标记）
3. **实现代码** — 在 `src/bpms/` 中编写实现
4. **提交** — `git add` + `git commit` + `git push`
5. **查看测试结果** — commit 后 hook 自动运行测试，结果注入对话
   - 测试通过 → 继续下一个需求
   - 测试失败 → 运行 `cat .claude/hooks/last-test-output.log` 查看详细错误，修复后重新提交（回到第 4 步）

```
理解需求 → 编写测试 → 实现代码 → 提交 → hook 自动测试 ──┬── 通过 → 下一个需求
                                                          │
                                                          └── 失败 → 查看日志 → 修复 → 重新提交
```

### 执行原则

- 动手前先明确目标与验证标准
- 多步任务先列简要计划
- 遇到歧义先提问，不要自行猜测

## 文档索引

- 项目文档：[docs/README.md](docs/README.md)
- 流程引擎设计文档：[docs/superpowers/specs/2026-05-04-process-engine-design.md](docs/superpowers/specs/2026-05-04-process-engine-design.md)
- 流程引擎实现计划：[docs/superpowers/plans/2026-05-04-process-engine-plan.md](docs/superpowers/plans/2026-05-04-process-engine-plan.md)
