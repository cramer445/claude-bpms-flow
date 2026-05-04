"""节点数据类型单元测试。"""

import pytest

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode


@pytest.mark.unit
class TestNodeType:
    def test_node_type_values(self):
        assert NodeType.START.value == "start"
        assert NodeType.END.value == "end"
        assert NodeType.USER_TASK.value == "user_task"


@pytest.mark.unit
class TestBaseNode:
    def test_create_base_node(self):
        node = BaseNode(id="n1", name="开始", node_type=NodeType.START)
        assert node.id == "n1"
        assert node.name == "开始"
        assert node.node_type == NodeType.START
        assert node.description == ""
        assert node.incoming == []
        assert node.outgoing == []

    def test_base_node_with_edges(self):
        node = BaseNode(
            id="n2",
            name="中间节点",
            node_type=NodeType.USER_TASK,
            incoming=["n1"],
            outgoing=["n3"],
        )
        assert node.incoming == ["n1"]
        assert node.outgoing == ["n3"]


@pytest.mark.unit
class TestUserTaskNode:
    def test_create_user_task_node(self):
        node = UserTaskNode(id="t1", name="审批", assignee="alice")
        assert node.id == "t1"
        assert node.name == "审批"
        assert node.node_type == NodeType.USER_TASK
        assert node.assignee == "alice"
        assert node.candidate_groups == []

    def test_user_task_with_candidates(self):
        node = UserTaskNode(
            id="t2",
            name="会签",
            candidate_groups=["managers", "directors"],
        )
        assert node.candidate_groups == ["managers", "directors"]
        assert node.assignee is None


@pytest.mark.unit
class TestProcessDefinition:
    def test_create_process_definition(self):
        start = BaseNode(id="start", name="开始", node_type=NodeType.START)
        task = UserTaskNode(id="t1", name="审批", assignee="alice")
        end = BaseNode(id="end", name="结束", node_type=NodeType.END)

        process = ProcessDefinition(
            id="proc-1",
            name="请假流程",
            version="1.0",
            nodes={"start": start, "t1": task, "end": end},
            start_node_id="start",
        )

        assert process.id == "proc-1"
        assert process.name == "请假流程"
        assert process.version == "1.0"
        assert len(process.nodes) == 3
        assert process.start_node_id == "start"

    def test_empty_process_definition(self):
        process = ProcessDefinition(id="p1", name="空流程", version="0.1")
        assert process.nodes == {}
        assert process.start_node_id == ""
