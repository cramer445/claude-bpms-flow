#!/bin/bash
# 分层递进测试脚本：unit → integration → e2e
# 任一层失败即停止
# stdout 只输出摘要（注入 Claude 上下文），详细日志写入文件

cd "${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR not set}" || exit 1

# 激活虚拟环境（如果存在）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

LOG_FILE="$CLAUDE_PROJECT_DIR/.claude/hooks/last-test-output.log"
SUMMARY_FILE="$CLAUDE_PROJECT_DIR/.claude/hooks/last-test-summary.txt"
UNIT_RESULT="--"
INTEG_RESULT="--"
E2E_RESULT="--"
OVERALL_EXIT_CODE=0

# 运行指定标记的测试，返回 0 表示通过（含 exit code 5 无测试）
run_tests() {
    local marker=$1
    local output
    output=$(pytest -m "$marker" -v --tb=short 2>&1)
    local ec=$?
    echo "=== $marker ===" >> "$LOG_FILE"
    echo "$output" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    if [ $ec -eq 0 ] || [ $ec -eq 5 ]; then
        return 0
    fi
    return 1
}

# 清空上次日志
> "$LOG_FILE"

# 分层递进测试
if run_tests unit; then
    UNIT_RESULT="[PASS] 通过"
    if run_tests integration; then
        INTEG_RESULT="[PASS] 通过"
        if run_tests e2e; then
            E2E_RESULT="[PASS] 通过"
        else
            E2E_RESULT="[FAIL] 失败"
            OVERALL_EXIT_CODE=1
        fi
    else
        INTEG_RESULT="[FAIL] 失败"
        E2E_RESULT="[SKIP] 跳过（集成测试未通过）"
        OVERALL_EXIT_CODE=1
    fi
else
    UNIT_RESULT="[FAIL] 失败"
    INTEG_RESULT="[SKIP] 跳过（单元测试未通过）"
    E2E_RESULT="[SKIP] 跳过（单元测试未通过）"
    OVERALL_EXIT_CODE=1
fi

# stdout 只输出摘要，注入 Claude 上下文
cat > "$SUMMARY_FILE" <<SUMMARY
=== 测试报告 ===
- 单元测试: $UNIT_RESULT
- 集成测试: $INTEG_RESULT
- 端到端测试: $E2E_RESULT

详细日志: $LOG_FILE
SUMMARY

cat "$SUMMARY_FILE"

exit $OVERALL_EXIT_CODE
