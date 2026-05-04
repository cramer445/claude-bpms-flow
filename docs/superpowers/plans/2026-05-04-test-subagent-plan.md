# 测试 Subagent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 git commit 后自动运行测试并通过 subagent 返回结果到主对话

**Architecture:** 使用 `PostToolUse` hook 匹配 `Bash(git commit *)`，触发命令 hook 运行测试脚本。脚本分层递进执行 pytest，将结果注入 Claude 上下文。

**Tech Stack:** Python pytest, Bash hooks, Claude Code settings.json

---

### Task 1: 创建测试运行脚本

**Files:**
- Create: `.claude/hooks/run-tests.sh`

- [ ] **Step 1: 创建测试运行脚本**

```bash
#!/bin/bash
# 分层递进测试脚本：unit → integration → e2e
# 任一层失败即停止，返回格式化结果

set -e

cd "$CLAUDE_PROJECT_DIR"

UNIT_RESULT=""
INTEG_RESULT=""
E2E_RESULT=""

# 1. 单元测试
echo "=== 单元测试 ==="
if pytest -m unit -v --tb=short 2>&1; then
    UNIT_RESULT="✅ 通过"
    echo ""
    echo "=== 集成测试 ==="
    if pytest -m integration -v --tb=short 2>&1; then
        INTEG_RESULT="✅ 通过"
        echo ""
        echo "=== 端到端测试 ==="
        if pytest -m e2e -v --tb=short 2>&1; then
            E2E_RESULT="✅ 通过"
        else
            E2E_RESULT="❌ 失败"
        fi
    else
        INTEG_RESULT="❌ 失败"
        E2E_RESULT="⏭ 跳过（集成测试未通过）"
    fi
else
    UNIT_RESULT="❌ 失败"
    INTEG_RESULT="⏭ 跳过（单元测试未通过）"
    E2E_RESULT="⏭ 跳过（单元测试未通过）"
fi

echo ""
echo "=== 测试报告 ==="
echo "单元测试: $UNIT_RESULT"
echo "集成测试: $INTEG_RESULT"
echo "端到端测试: $E2E_RESULT"
```

- [ ] **Step 2: 设置可执行权限**

```bash
chmod +x .claude/hooks/run-tests.sh
```

### Task 2: 配置 PostToolUse Hook

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: 更新 settings.json 添加 hook 配置**

读取当前 `.claude/settings.json` 内容，添加 `PostToolUse` hook：

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "code-review@claude-plugins-official": true,
    "code-simplifier@claude-plugins-official": true,
    "github@claude-plugins-official": true,
    "claude-md-management@claude-plugins-official": true,
    "commit-commands@claude-plugins-official": true,
    "gitlab@claude-plugins-official": true
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "if": "Bash(git commit *)",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests.sh",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

> 注意：`PostToolUse` hook 的 stdout 不会自动注入上下文。脚本输出会显示在 transcript 中。如果需要在对话中看到结果，可通过 `Stop` hook 读取脚本输出并注入。

### Task 3: 配置 Stop Hook 注入测试结果到对话

为了将测试结果注入 Claude 的上下文（让 Claude 能看到并响应），需要额外的 `Stop` hook。

**Files:**
- Create: `.claude/hooks/inject-test-results.sh`
- Modify: `.claude/settings.json`

- [ ] **Step 1: 创建结果注入脚本**

```bash
#!/bin/bash
# Stop hook: 检测本次对话是否执行了 git commit
# 如果执行了，运行测试并将结果注入 Claude 上下文

cd "$CLAUDE_PROJECT_DIR"

# 检查最近 1 分钟内是否有 commit（表明本次 turn 中提交了）
LAST_COMMIT_TIME=$(git log -1 --format=%ct 2>/dev/null || echo 0)
CURRENT_TIME=$(date +%s)
DIFF=$((CURRENT_TIME - LAST_COMMIT_TIME))

if [ "$DIFF" -lt 60 ]; then
    echo "检测到新的 git commit，运行测试..."
    echo ""
    "$CLAUDE_PROJECT_DIR/.claude/hooks/run-tests.sh"
    echo ""
    echo "请根据测试结果判断是否需要修复。"
fi
```

- [ ] **Step 2: 设置可执行权限**

```bash
chmod +x .claude/hooks/inject-test-results.sh
```

- [ ] **Step 3: 更新 settings.json 添加 Stop hook**

在已有的 `hooks` 对象中添加 `Stop` 事件：

```json
{
  "enabledPlugins": { ... },
  "hooks": {
    "PostToolUse": [ ... ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/inject-test-results.sh",
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

### Task 4: 验证 Hook 配置

- [ ] **Step 1: 验证 JSON 格式**

```bash
python3 -c "import json; json.load(open('.claude/settings.json'))"
```

- [ ] **Step 2: 验证脚本可执行**

```bash
ls -la .claude/hooks/
```

- [ ] **Step 3: 提交并推送**

```bash
git add .claude/settings.json .claude/hooks/run-tests.sh .claude/hooks/inject-test-results.sh
git commit -m "feat: 添加 git commit 后自动测试 hook"
git push
```
