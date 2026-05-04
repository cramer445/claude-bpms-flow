"""API 路由单元测试。"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.store import Store


@pytest.fixture
def store(tmp_path):
    return Store(data_dir=tmp_path)


@pytest_asyncio.fixture
async def client(store):
    """创建使用自定义 Store 的 FastAPI 测试客户端。"""
    from bpms.api.routes import create_app
    app = create_app(store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _sample_process_definition() -> ProcessDefinition:
    start = BaseNode(id="start", name="开始", node_type=NodeType.START, outgoing=["apply"])
    apply_node = UserTaskNode(
        id="apply", name="提交申请", assignee="applicant",
        incoming=["start"], outgoing=["approve"],
    )
    end = BaseNode(id="end", name="结束", node_type=NodeType.END, incoming=["apply"])
    return ProcessDefinition(
        id="leave", name="请假流程", version="1.0",
        nodes={"start": start, "apply": apply_node, "end": end},
        start_node_id="start",
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestListProcesses:
    async def test_empty_list(self, client):
        resp = await client.get("/api/processes")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_processes(self, client, store):
        pd = _sample_process_definition()
        store.save_process_definition(pd)

        resp = await client.get("/api/processes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "leave"
        assert data[0]["name"] == "请假流程"


@pytest.mark.unit
@pytest.mark.asyncio
class TestGetProcess:
    async def test_get_process(self, client, store):
        pd = _sample_process_definition()
        store.save_process_definition(pd)

        resp = await client.get("/api/processes/leave")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "leave"
        assert data["name"] == "请假流程"
        assert "nodes" in data
        assert "start" in data["nodes"]
        assert data["nodes"]["apply"]["type"] == "user_task"
        assert data["nodes"]["apply"]["assignee"] == "applicant"

    async def test_get_nonexistent(self, client):
        resp = await client.get("/api/processes/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()


@pytest.mark.unit
@pytest.mark.asyncio
class TestCreateProcess:
    async def test_create_process(self, client):
        payload = {
            "id": "test",
            "name": "测试流程",
            "version": "1.0",
            "start_node_id": "start",
            "nodes": {
                "start": {
                    "id": "start", "name": "开始", "type": "start",
                    "incoming": [], "outgoing": ["end"],
                },
                "end": {
                    "id": "end", "name": "结束", "type": "end",
                    "incoming": ["start"], "outgoing": [],
                },
            },
        }
        resp = await client.post("/api/processes", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "test"

    async def test_create_duplicate(self, client, store):
        pd = _sample_process_definition()
        store.save_process_definition(pd)

        payload = {
            "id": "leave",
            "name": "重复",
            "version": "1.0",
            "start_node_id": "start",
            "nodes": {},
        }
        resp = await client.post("/api/processes", json=payload)
        assert resp.status_code == 409


@pytest.mark.unit
@pytest.mark.asyncio
class TestUpdateProcess:
    async def test_update_process(self, client, store):
        pd = _sample_process_definition()
        store.save_process_definition(pd)

        payload = {
            "id": "leave",
            "name": "更新后的名称",
            "version": "1.0",
            "start_node_id": "start",
            "nodes": {
                "start": {
                    "id": "start", "name": "开始", "type": "start",
                    "incoming": [], "outgoing": ["end"],
                },
                "end": {
                    "id": "end", "name": "结束", "type": "end",
                    "incoming": ["start"], "outgoing": [],
                },
            },
        }
        resp = await client.post("/api/processes/leave", json=payload)
        assert resp.status_code == 200
        assert resp.json()["name"] == "更新后的名称"

    async def test_update_nonexistent(self, client):
        resp = await client.post("/api/processes/nonexistent", json={})
        assert resp.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
class TestDeleteProcess:
    async def test_delete_process(self, client, store):
        pd = _sample_process_definition()
        store.save_process_definition(pd)

        resp = await client.delete("/api/processes/leave")
        assert resp.status_code == 204

        # 确认已删除
        resp = await client.get("/api/processes/leave")
        assert resp.status_code == 404

    async def test_delete_nonexistent(self, client):
        resp = await client.delete("/api/processes/nonexistent")
        assert resp.status_code == 404
