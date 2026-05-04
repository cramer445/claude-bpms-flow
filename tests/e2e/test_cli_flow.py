"""CLI 完整流程端到端测试。"""

import json
import re
import pytest
from pathlib import Path

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.store import Store


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """创建包含流程定义的 data 目录。"""
    processes_dir = tmp_path / "processes"
    instances_dir = tmp_path / "instances"
    processes_dir.mkdir()
    instances_dir.mkdir()

    # 注册请假流程
    start = BaseNode(id="start", name="开始", node_type=NodeType.START, outgoing=["apply"])
    apply_node = UserTaskNode(
        id="apply",
        name="提交申请",
        assignee="applicant",
        incoming=["start"],
        outgoing=["approve"],
    )
    approve_node = UserTaskNode(
        id="approve",
        name="主管审批",
        assignee="manager",
        incoming=["apply"],
        outgoing=["end"],
    )
    end = BaseNode(id="end", name="结束", node_type=NodeType.END, incoming=["approve"])
    pd = ProcessDefinition(
        id="leave",
        name="请假流程",
        version="1.0",
        nodes={"start": start, "apply": apply_node, "approve": approve_node, "end": end},
        start_node_id="start",
    )
    from bpms.models import ProcessDefinitionSerializer
    data = ProcessDefinitionSerializer.serialize(pd)
    (processes_dir / "leave.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))

    return tmp_path


@pytest.fixture
def cli(data_dir: Path):
    """创建一个使用自定义 data_dir 的 CLI 运行环境。"""

    class CLIRunner:
        def __init__(self):
            self.output = []

        def run(self, *args: str) -> str:
            self.output = []
            import sys
            from io import StringIO

            old_stdout = sys.stdout
            sys.stdout = StringIO()

            # 创建使用自定义 data_dir 的 Store
            store = Store(data_dir=data_dir)
            from bpms.engine import ProcessEngine
            engine = ProcessEngine(store)

            # 解析命令
            from bpms.cli import create_parser
            parser = create_parser()
            parsed = parser.parse_args(args)

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

            result = sys.stdout.getvalue()
            sys.stdout = old_stdout
            return result

    return CLIRunner()


@pytest.mark.e2e
class TestCLIWorkflow:
    def test_list_processes(self, cli):
        output = cli.run("list-processes")
        assert "leave" in output
        assert "请假流程" in output

    def test_full_workflow_via_cli(self, cli):
        """通过 CLI 完成完整流程流转"""
        # 发起流程
        output = cli.run("start", "leave")
        assert "流程实例已创建" in output
        assert "apply" in output

        # 提取实例 ID
        instance_id = output.split("流程实例已创建: ")[1].split("\n")[0].strip()

        # 查看待办
        output = cli.run("tasks", instance_id)
        assert "apply" in output

        # 完成第一个任务
        match = re.search(r'\[([^\]]+)\]', output)
        task_id = match.group(1)
        output = cli.run("complete", task_id)
        assert "任务完成" in output
        assert "approve" in output

        # 查看待办（应该在审批节点）
        output = cli.run("tasks", instance_id)
        assert "approve" in output

        # 完成第二个任务
        match = re.search(r'\[([^\]]+)\]', output)
        task_id = match.group(1)
        output = cli.run("complete", task_id)
        assert "已完成" in output

    def test_show_instance(self, cli):
        output = cli.run("start", "leave")
        instance_id = output.split("流程实例已创建: ")[1].split("\n")[0].strip()

        output = cli.run("show", instance_id)
        assert instance_id in output
        assert "running" in output
