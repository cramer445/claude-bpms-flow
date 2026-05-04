"""流程实例数据类型单元测试。"""

import pytest

from bpms.models.instance import ProcessInstance, TaskInstance, ProcessStatus, TaskStatus


@pytest.mark.unit
class TestProcessStatus:
    def test_status_values(self):
        assert ProcessStatus.RUNNING == "running"
        assert ProcessStatus.COMPLETED == "completed"
        assert ProcessStatus.TERMINATED == "terminated"


@pytest.mark.unit
class TestTaskStatus:
    def test_status_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.SKIPPED == "skipped"


@pytest.mark.unit
class TestProcessInstance:
    def test_create_instance(self):
        instance = ProcessInstance(
            id="inst-001",
            process_id="leave",
            version="1.0",
        )
        assert instance.id == "inst-001"
        assert instance.process_id == "leave"
        assert instance.version == "1.0"
        assert instance.status == ProcessStatus.RUNNING
        assert instance.current_node_id == ""
        assert instance.variables == {}
        assert instance.created_at == ""

    def test_instance_with_variables(self):
        instance = ProcessInstance(
            id="inst-002",
            process_id="leave",
            version="1.0",
            variables={"days": 5, "reason": "旅游"},
        )
        assert instance.variables == {"days": 5, "reason": "旅游"}


@pytest.mark.unit
class TestTaskInstance:
    def test_create_task(self):
        task = TaskInstance(
            id="task-001",
            process_instance_id="inst-001",
            node_id="apply",
            assignee="alice",
        )
        assert task.id == "task-001"
        assert task.process_instance_id == "inst-001"
        assert task.node_id == "apply"
        assert task.status == TaskStatus.PENDING
        assert task.assignee == "alice"
        assert task.started_at != ""
        assert task.completed_at is None

    def test_complete_task(self):
        task = TaskInstance(
            id="task-001",
            process_instance_id="inst-001",
            node_id="apply",
            assignee="alice",
        )
        task.status = TaskStatus.COMPLETED
        task.completed_at = "2026-05-04T10:00:00"
        assert task.status == TaskStatus.COMPLETED
