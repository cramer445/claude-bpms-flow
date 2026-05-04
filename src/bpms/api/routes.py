"""FastAPI REST API 路由。"""

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from bpms.models import BaseNode, NodeType, ProcessDefinition, ProcessDefinitionSerializer, UserTaskNode
from bpms.store import Store


def _build_app(store: Store) -> FastAPI:
    app = FastAPI(title="BPMS Process Editor API")
    router = APIRouter(prefix="/api")

    @router.get("/processes")
    def list_processes():
        pds = store.list_process_definitions()
        return [
            {"id": pd.id, "name": pd.name, "version": pd.version}
            for pd in pds
        ]

    @router.get("/processes/{process_id}")
    def get_process(process_id: str):
        try:
            pd = store.load_process_definition(process_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"流程定义不存在: {process_id}")
        return ProcessDefinitionSerializer.serialize(pd)

    @router.post("/processes", status_code=201)
    def create_process(payload: dict):
        try:
            store.load_process_definition(payload["id"])
            raise HTTPException(status_code=409, detail="流程定义已存在")
        except FileNotFoundError:
            pass
        pd = _deserialize_process(payload)
        store.save_process_definition(pd)
        return {"id": pd.id, "name": pd.name, "version": pd.version}

    @router.post("/processes/{process_id}")
    def update_process(process_id: str, payload: dict):
        try:
            store.load_process_definition(process_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="流程定义不存在")
        pd = _deserialize_process(payload)
        store.save_process_definition(pd)
        return {"id": pd.id, "name": pd.name, "version": pd.version}

    @router.delete("/processes/{process_id}", status_code=204)
    def delete_process(process_id: str):
        from pathlib import Path
        path = store._processes_dir / f"{process_id}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="流程定义不存在")
        path.unlink()

    app.include_router(router)
    return app


def _deserialize_process(data: dict) -> ProcessDefinition:
    """从 API 请求体反序列化为 ProcessDefinition。"""
    nodes = {}
    for node_id, node_data in data.get("nodes", {}).items():
        node_type = NodeType(node_data["type"])
        if node_type == NodeType.USER_TASK:
            node = UserTaskNode(
                id=node_data["id"],
                name=node_data["name"],
                assignee=node_data.get("assignee"),
                candidate_groups=node_data.get("candidate_groups", []),
                incoming=node_data.get("incoming", []),
                outgoing=node_data.get("outgoing", []),
            )
        else:
            node = BaseNode(
                id=node_data["id"],
                name=node_data["name"],
                node_type=node_type,
                incoming=node_data.get("incoming", []),
                outgoing=node_data.get("outgoing", []),
            )
        nodes[node_id] = node

    return ProcessDefinition(
        id=data["id"],
        name=data["name"],
        version=data.get("version", "1.0"),
        nodes=nodes,
        start_node_id=data.get("start_node_id", ""),
    )


def create_app(store: Store) -> FastAPI:
    """创建 FastAPI 应用（不含静态文件挂载，用于测试）。"""
    return _build_app(store)


def create_app_with_static(store: Store, static_dir: str) -> FastAPI:
    """创建 FastAPI 应用（含静态文件挂载，用于生产）。"""
    import os
    app = _build_app(store)
    static_path = os.path.join(static_dir, "index.html")
    if os.path.exists(static_path):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app
