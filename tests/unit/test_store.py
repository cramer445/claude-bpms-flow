"""存储层单元测试。"""

import pytest
from pathlib import Path

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.models.instance import ProcessInstance, TaskInstance
from bpms.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(data_dir=tmp_path)


@pytest.mark.unit
class TestStore:
    def test_save_and_load_process_definition(self, store: Store):
        start = BaseNode(id="start", name="开始", node_type=NodeType.START, outgoing=["t1"])
        task = UserTaskNode(id="t1", name="审批", assignee="manager", incoming=["start"], outgoing=["end"])
        end = BaseNode(id="end", name="结束", node_type=NodeType.END, incoming=["t1"])

        pd = ProcessDefinition(
            id="leave",
            name="请假流程",
            version="1.0",
            nodes={"start": start, "t1": task, "end": end},
            start_node_id="start",
        )

        store.save_process_definition(pd)
        loaded = store.load_process_definition("leave")

        assert loaded.id == "leave"
        assert isinstance(loaded.nodes["t1"], UserTaskNode)

    def test_list_process_definitions(self, store: Store):
        pd1 = ProcessDefinition(id="p1", name="流程1", version="1.0")
        pd2 = ProcessDefinition(id="p2", name="流程2", version="1.0")
        store.save_process_definition(pd1)
        store.save_process_definition(pd2)

        pds = store.list_process_definitions()
        assert len(pds) == 2
        ids = {pd.id for pd in pds}
        assert "p1" in ids
        assert "p2" in ids

    def test_save_and_load_instance(self, store: Store):
        instance = ProcessInstance(
            id="inst-001",
            process_id="leave",
            version="1.0",
            current_node_id="t1",
        )

        store.save_instance(instance)
        loaded = store.load_instance("inst-001")

        assert loaded.id == "inst-001"
        assert loaded.current_node_id == "t1"

    def test_save_and_load_tasks(self, store: Store):
        instance = ProcessInstance(
            id="inst-001",
            process_id="leave",
            version="1.0",
            current_node_id="t1",
        )
        store.save_instance(instance)

        task = TaskInstance(
            id="task-001",
            process_instance_id="inst-001",
            node_id="t1",
            assignee="alice",
        )
        store.save_task("inst-001", task)

        tasks = store.get_tasks_for_instance("inst-001")
        assert len(tasks) == 1
        assert tasks[0].id == "task-001"
        assert tasks[0].assignee == "alice"

    def test_load_nonexistent_definition_raises(self, store: Store):
        with pytest.raises(FileNotFoundError):
            store.load_process_definition("nonexistent")

    def test_load_nonexistent_instance_raises(self, store: Store):
        with pytest.raises(FileNotFoundError):
            store.load_instance("nonexistent")

    def test_save_task_nonexistent_instance_raises(self, store: Store):
        task = TaskInstance(id="task-001", process_instance_id="nonexistent", node_id="t1")
        with pytest.raises(FileNotFoundError):
            store.save_task("nonexistent", task)

    def test_get_tasks_for_nonexistent_instance_raises(self, store: Store):
        with pytest.raises(FileNotFoundError):
            store.get_tasks_for_instance("nonexistent")

    def test_save_task_update_existing(self, store: Store):
        instance = ProcessInstance(id="inst-001", process_id="leave", version="1.0")
        store.save_instance(instance)

        task = TaskInstance(id="task-001", process_instance_id="inst-001", node_id="t1", assignee="alice")
        store.save_task("inst-001", task)

        # Update the task
        task.assignee = "bob"
        task.status = "completed"
        store.save_task("inst-001", task)

        tasks = store.get_tasks_for_instance("inst-001")
        assert len(tasks) == 1
        assert tasks[0].assignee == "bob"
        assert tasks[0].status == "completed"
