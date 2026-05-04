#!/bin/bash
# Stop hook: 检测本次对话是否执行了 git commit
# 如果执行了，运行测试并将结果注入 Claude 上下文

set -eo pipefail

cd "${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR not set}" || exit 1

# 检查最近 1 分钟内是否有 commit（表明本次 turn 中提交了）
LAST_COMMIT_TIME=$(git log -1 --format=%ct 2>/dev/null || echo 0)
CURRENT_TIME=$(date +%s)
DIFF=$((CURRENT_TIME - LAST_COMMIT_TIME))

if [ "$DIFF" -lt 60 ]; then
    echo "检测到新的 git commit，运行测试..."
    echo ""
    "$CLAUDE_PROJECT_DIR/.claude/hooks/run-tests.sh"
    TEST_EXIT_CODE=$?
    echo ""
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        echo "测试失败，请修复后重新提交。"
    fi
fi
exit ${TEST_EXIT_CODE:-0}
