"""流程引擎核心单元测试。"""

import pytest
from pathlib import Path

from bpms.engine import ProcessEngine
from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.models.instance import ProcessStatus, TaskStatus
from bpms.store import Store


@pytest.fixture
def engine(tmp_path: Path) -> ProcessEngine:
    return ProcessEngine(store=Store(data_dir=tmp_path))


def _create_sample_process_definition() -> ProcessDefinition:
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
    return ProcessDefinition(
        id="leave",
        name="请假流程",
        version="1.0",
        nodes={"start": start, "apply": apply_node, "approve": approve_node, "end": end},
        start_node_id="start",
    )


def _register_sample_process(engine: ProcessEngine) -> ProcessDefinition:
    pd = _create_sample_process_definition()
    engine.store.save_process_definition(pd)
    return pd


@pytest.mark.unit
class TestEngineLoadDefinition:
    def test_load_process_definition_from_file(self, engine: ProcessEngine):
        _register_sample_process(engine)

        loaded = engine.load_process_definition("leave")
        assert loaded.id == "leave"
        assert len(loaded.nodes) == 4


@pytest.mark.unit
class TestEngineStartInstance:
    def test_start_instance_advances_to_first_user_task(self, engine: ProcessEngine):
        _register_sample_process(engine)
        instance = engine.start_instance("leave")

        assert instance.status == ProcessStatus.RUNNING
        assert instance.process_id == "leave"
        assert instance.current_node_id == "apply"

        tasks = engine.get_pending_tasks(instance.id)
        assert len(tasks) == 1
        assert tasks[0].node_id == "apply"
        assert tasks[0].assignee == "applicant"

    def test_start_instance_creates_tasks_in_store(self, engine: ProcessEngine):
        _register_sample_process(engine)
        instance = engine.start_instance("leave")

        tasks = engine.store.get_tasks_for_instance(instance.id)
        assert len(tasks) == 1


@pytest.mark.unit
class TestEngineCompleteTask:
    def test_complete_task_advances_to_next_user_task(self, engine: ProcessEngine):
        _register_sample_process(engine)
        instance = engine.start_instance("leave")

        pending = engine.get_pending_tasks(instance.id)
        task = pending[0]

        result = engine.complete_task(task.id)

        assert result.current_node_id == "approve"
        assert result.status == ProcessStatus.RUNNING

        new_pending = engine.get_pending_tasks(result.id)
        assert len(new_pending) == 1
        assert new_pending[0].node_id == "approve"
        assert new_pending[0].assignee == "manager"

    def test_complete_task_marks_old_task_completed(self, engine: ProcessEngine):
        _register_sample_process(engine)
        instance = engine.start_instance("leave")

        pending = engine.get_pending_tasks(instance.id)
        engine.complete_task(pending[0].id)

        all_tasks = engine.store.get_tasks_for_instance(instance.id)
        completed = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
        assert len(completed) == 1
        assert len(pending_tasks) == 1

    def test_complete_task_on_last_node_finishes_instance(self, engine: ProcessEngine):
        _register_sample_process(engine)
        instance = engine.start_instance("leave")

        # 完成第一个任务 (apply)
        pending = engine.get_pending_tasks(instance.id)
        instance = engine.complete_task(pending[0].id)

        # 完成第二个任务 (approve)
        pending = engine.get_pending_tasks(instance.id)
        result = engine.complete_task(pending[0].id)

        assert result.status == ProcessStatus.COMPLETED
        assert result.current_node_id == "end"

        pending = engine.get_pending_tasks(result.id)
        assert len(pending) == 0


@pytest.mark.unit
class TestEngineErrors:
    def test_start_instance_nonexistent_process_raises(self, engine: ProcessEngine):
        with pytest.raises(FileNotFoundError):
            engine.start_instance("nonexistent")

    def test_complete_task_nonexistent_task_raises(self, engine: ProcessEngine):
        with pytest.raises(ValueError):
            engine.complete_task("nonexistent")
