#!/bin/bash
# Stop hook: 检查是否有待报告的测试结果
# 如果有，将摘要注入 Claude 上下文

cd "${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR not set}" || exit 1

SUMMARY_FILE="$CLAUDE_PROJECT_DIR/.claude/hooks/last-test-summary.txt"

if [ -f "$SUMMARY_FILE" ]; then
    # 检查文件是否是最近 2 分钟内生成的
    LAST_MOD=$(stat -f %m "$SUMMARY_FILE" 2>/dev/null || stat -c %Y "$SUMMARY_FILE" 2>/dev/null || echo 0)
    CURRENT_TIME=$(date +%s)
    DIFF=$((CURRENT_TIME - LAST_MOD))

    if [ "$DIFF" -lt 120 ]; then
        cat "$SUMMARY_FILE"
        # 清理，避免下次 Stop 时重复注入
        rm -f "$SUMMARY_FILE"
    fi
fi