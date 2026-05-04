"""序列化模块单元测试。"""

import pytest

from bpms.models.serialization import ProcessDefinitionSerializer
from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode


@pytest.mark.unit
class TestProcessDefinitionSerializer:
    def test_serialize_process_definition(self):
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

        data = ProcessDefinitionSerializer.serialize(pd)
        assert data["id"] == "leave"
        assert data["name"] == "请假流程"
        assert data["version"] == "1.0"
        assert data["start_node_id"] == "start"
        assert len(data["nodes"]) == 3
        assert data["nodes"]["start"]["type"] == "start"
        assert data["nodes"]["t1"]["type"] == "user_task"
        assert data["nodes"]["t1"]["assignee"] == "manager"
        assert data["nodes"]["end"]["type"] == "end"

    def test_deserialize_process_definition(self):
        data = {
            "id": "leave",
            "name": "请假流程",
            "version": "1.0",
            "start_node_id": "start",
            "nodes": {
                "start": {"id": "start", "name": "开始", "type": "start", "outgoing": ["t1"]},
                "t1": {
                    "id": "t1",
                    "name": "审批",
                    "type": "user_task",
                    "assignee": "manager",
                    "incoming": ["start"],
                    "outgoing": ["end"],
                },
                "end": {"id": "end", "name": "结束", "type": "end", "incoming": ["t1"]},
            },
        }

        pd = ProcessDefinitionSerializer.deserialize(data)
        assert pd.id == "leave"
        assert pd.name == "请假流程"
        assert pd.version == "1.0"
        assert pd.start_node_id == "start"
        assert isinstance(pd.nodes["start"], BaseNode)
        assert isinstance(pd.nodes["t1"], UserTaskNode)
        assert pd.nodes["t1"].assignee == "manager"
        assert isinstance(pd.nodes["end"], BaseNode)

    def test_roundtrip(self):
        start = BaseNode(id="start", name="开始", node_type=NodeType.START, outgoing=["t1"])
        task = UserTaskNode(id="t1", name="审批", assignee="manager", incoming=["start"], outgoing=["end"])
        end = BaseNode(id="end", name="结束", node_type=NodeType.END, incoming=["t1"])

        pd = ProcessDefinition(
            id="p1",
            name="测试流程",
            version="0.1",
            nodes={"start": start, "t1": task, "end": end},
            start_node_id="start",
        )

        data = ProcessDefinitionSerializer.serialize(pd)
        restored = ProcessDefinitionSerializer.deserialize(data)

        assert restored.id == pd.id
        assert restored.start_node_id == pd.start_node_id
        assert isinstance(restored.nodes["t1"], UserTaskNode)
