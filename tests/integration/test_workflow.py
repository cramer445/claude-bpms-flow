"""完整流程流转集成测试。"""

import pytest
from pathlib import Path

from bpms.engine import ProcessEngine
from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.models.instance import ProcessStatus, TaskStatus
from bpms.store import Store


@pytest.fixture
def engine(tmp_path: Path) -> ProcessEngine:
    return ProcessEngine(store=Store(data_dir=tmp_path))


def _register_leave_process(engine: ProcessEngine) -> None:
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
    engine.store.save_process_definition(pd)


@pytest.mark.integration
class TestFullWorkflow:
    def test_leave_process_full_lifecycle(self, engine: ProcessEngine):
        """完整请假流程：发起 → 提交申请 → 审批 → 结束"""
        _register_leave_process(engine)

        # 发起流程
        instance = engine.start_instance("leave")
        assert instance.status == ProcessStatus.RUNNING
        assert instance.current_node_id == "apply"

        pending = engine.get_pending_tasks(instance.id)
        assert len(pending) == 1
        assert pending[0].node_id == "apply"

        # 完成提交申请
        instance = engine.complete_task(pending[0].id)
        assert instance.current_node_id == "approve"
        assert instance.status == ProcessStatus.RUNNING

        pending = engine.get_pending_tasks(instance.id)
        assert len(pending) == 1
        assert pending[0].node_id == "approve"
        assert pending[0].assignee == "manager"

        # 完成审批
        instance = engine.complete_task(pending[0].id)
        assert instance.status == ProcessStatus.COMPLETED
        assert instance.current_node_id == "end"

        pending = engine.get_pending_tasks(instance.id)
        assert len(pending) == 0

        # 验证所有任务状态
        all_tasks = engine.store.get_tasks_for_instance(instance.id)
        statuses = [t.status for t in all_tasks]
        assert statuses.count(TaskStatus.COMPLETED) == 2
