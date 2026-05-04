"""CLI 模块单元测试。"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from bpms.cli import create_parser, run
from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.store import Store


@pytest.mark.unit
class TestCLIParser:
    def test_create_parser_has_all_subcommands(self):
        parser = create_parser()
        subcommands = set()
        for action in parser._subparsers._actions:
            if hasattr(action, "choices") and action.choices:
                subcommands.update(action.choices.keys())

        assert "list-processes" in subcommands
        assert "start" in subcommands
        assert "tasks" in subcommands
        assert "complete" in subcommands
        assert "show" in subcommands

    def test_start_requires_process_id(self):
        parser = create_parser()
        parsed = parser.parse_args(["start", "my-process"])
        assert parsed.process_id == "my-process"

    def test_complete_requires_task_id(self):
        parser = create_parser()
        parsed = parser.parse_args(["complete", "task-123"])
        assert parsed.task_id == "task-123"

    def test_tasks_optional_instance_id(self):
        parser = create_parser()
        parsed = parser.parse_args(["tasks"])
        assert parsed.instance_id is None

        parsed = parser.parse_args(["tasks", "inst-001"])
        assert parsed.instance_id == "inst-001"


@pytest.mark.unit
class TestCLICommands:
    @pytest.fixture
    def engine_with_process(self, tmp_path: Path):
        """创建包含流程定义的 Store 和 Engine。"""
        store = Store(data_dir=tmp_path)
        start = BaseNode(id="start", name="开始", node_type=NodeType.START, outgoing=["apply"])
        apply_node = UserTaskNode(
            id="apply", name="提交申请", assignee="applicant",
            incoming=["start"], outgoing=["approve"],
        )
        approve_node = UserTaskNode(
            id="approve", name="主管审批", assignee="manager",
            incoming=["apply"], outgoing=["end"],
        )
        end = BaseNode(id="end", name="结束", node_type=NodeType.END, incoming=["approve"])
        pd = ProcessDefinition(
            id="leave", name="请假流程", version="1.0",
            nodes={"start": start, "apply": apply_node, "approve": approve_node, "end": end},
            start_node_id="start",
        )
        store.save_process_definition(pd)
        return store

    def _capture_output(self, store, args):
        from bpms.engine import ProcessEngine
        engine = ProcessEngine(store)
        parser = create_parser()
        parsed = parser.parse_args(args)

        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            if parsed.command == "list-processes":
                from bpms.cli import cmd_list_processes
                cmd_list_processes(engine)
            elif parsed.command == "start":
                from bpms.cli import cmd_start
                cmd_start(engine, parsed.process_id)
            elif parsed.command == "tasks":
                from bpms.cli import cmd_tasks
                cmd_tasks(engine, parsed.instance_id)
            elif parsed.command == "complete":
                from bpms.cli import cmd_complete
                cmd_complete(engine, parsed.task_id)
            elif parsed.command == "show":
                from bpms.cli import cmd_show
                cmd_show(engine, parsed.instance_id)
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def test_list_processes(self, engine_with_process):
        output = self._capture_output(engine_with_process, ["list-processes"])
        assert "leave" in output
        assert "请假流程" in output

    def test_start_process(self, engine_with_process):
        output = self._capture_output(engine_with_process, ["start", "leave"])
        assert "流程实例已创建" in output
        assert "apply" in output

    def test_error_nonexistent_process(self, engine_with_process):
        output = self._capture_output(engine_with_process, ["start", "nonexistent"])
        assert "错误" in output

    def test_error_nonexistent_task(self, engine_with_process):
        # 先发起一个流程实例
        from bpms.engine import ProcessEngine
        engine = ProcessEngine(engine_with_process)
        instance = engine.start_instance("leave")
        # 然后用一个不存在的任务 ID
        output = self._capture_output(engine_with_process, ["complete", "nonexistent"])
        assert "错误" in output
