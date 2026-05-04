# 流程编辑器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现基于 React + React Flow 的 Web 流程编辑器，支持流程图的可视化创建、编辑、保存和删除，与现有流程引擎数据模型无缝对接。

**Architecture:** FastAPI 内嵌在 bpms 包中提供 REST API 和 serve 前端静态文件。前端为 React SPA，使用 React Flow 做流程图渲染，Vite 做构建工具。前后端通过 JSON API 通信。

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, httpx (测试), React 18, React Flow, Vite, TypeScript

---

### 文件总览

| 状态 | 文件 | 职责 |
|------|------|------|
| 新增 | `src/bpms/server.py` | FastAPI 应用工厂 + uvicorn 启动 |
| 新增 | `src/bpms/api/__init__.py` | api 包 |
| 新增 | `src/bpms/api/routes.py` | REST API 路由 |
| 修改 | `src/bpms/cli.py` | 新增 `serve` 子命令 |
| 修改 | `pyproject.toml` | 添加 fastapi/uvicorn 依赖 |
| 新增 | `tests/unit/test_api/test_routes.py` | API 路由单元测试 |
| 新增 | `frontend/` 下全部文件 | React 前端 SPA |
| 修改 | `.gitignore` | 忽略前端构建产物 |

---

### Task 1: 后端 FastAPI 服务 + API 路由

**Files:**
- Create: `src/bpms/server.py`
- Create: `src/bpms/api/__init__.py`
- Create: `src/bpms/api/routes.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_api/test_routes.py`

- [ ] **Step 1: 添加 FastAPI + uvicorn 依赖到 pyproject.toml**

```toml
[project]
dependencies = ["fastapi>=0.104", "uvicorn>=0.24"]
```

- [ ] **Step 2: 编写 API 路由测试**

```python
"""API 路由单元测试。"""

import pytest
from httpx import ASGITransport, AsyncClient

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.store import Store


@pytest.fixture
def store(tmp_path):
    return Store(data_dir=tmp_path)


@pytest.fixture
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
        assert "error" in resp.json()


@pytest.mark.unit
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
```

- [ ] **Step 3: 创建 api/__init__.py**

```python
"""BPMS REST API。"""
```

- [ ] **Step 4: 实现 api/routes.py**

```python
"""FastAPI REST API 路由。"""

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

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
        import json
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
```

- [ ] **Step 5: 实现 server.py — uvicorn 启动入口**

```python
"""BPMS FastAPI 服务启动入口。"""

import uvicorn

from bpms.store import Store


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """启动 FastAPI 服务。"""
    store = Store()
    from bpms.api.routes import create_app_with_static
    from pathlib import Path
    static_dir = Path(__file__).parent / "static"
    app = create_app_with_static(store, str(static_dir))
    uvicorn.run(app, host=host, port=port)
```

- [ ] **Step 6: 修改 cli.py，添加 `serve` 子命令**

在 `create_parser` 函数中 `show_p` 定义之后添加：

```python
    serve_p = subparsers.add_parser("serve", help="启动 Web 服务")
    serve_p.add_argument("--host", default="127.0.0.1", help="监听地址")
    serve_p.add_argument("--port", type=int, default=8000, help="监听端口")
```

在 `run` 函数的命令分发中添加：

```python
    elif parsed.command == "serve":
        from bpms.server import serve
        serve(host=parsed.host, port=parsed.port)
        return
```

- [ ] **Step 7: 运行测试确认通过**

```bash
pytest tests/unit/test_api/test_routes.py -v
```

- [ ] **Step 8: 提交**

```bash
git add pyproject.toml src/bpms/api/__init__.py src/bpms/api/routes.py src/bpms/server.py src/bpms/cli.py tests/unit/test_api/test_routes.py
git commit -m "feat: 新增 FastAPI REST API 服务"
```

---

### Task 2: 前端项目骨架 + 类型 + 转换器

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/transformer.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/styles/index.css`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "bpms-editor",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3",
    "react-dom": "^18.3",
    "@xyflow/react": "^12.4",
    "react-router-dom": "^7.1"
  },
  "devDependencies": {
    "@types/react": "^18.3",
    "@types/react-dom": "^18.3",
    "@vitejs/plugin-react": "^4.3",
    "typescript": "^5.6",
    "vite": "^6.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../src/bpms/static",
    emptyOutDir: true,
  },
});
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: 创建 index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BPMS 流程编辑器</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 src/types.ts**

```typescript
/** 后端 API 返回的流程定义摘要（列表接口）。 */
export interface ProcessSummary {
  id: string;
  name: string;
  version: string;
}

/** 后端 API 返回的完整流程定义。 */
export interface ProcessDefinition {
  id: string;
  name: string;
  version: string;
  start_node_id: string;
  nodes: Record<string, NodeData>;
}

/** 单个节点的数据（JSON 文件中的节点对象）。 */
export interface NodeData {
  id: string;
  name: string;
  type: "start" | "end" | "user_task";
  description?: string;
  incoming: string[];
  outgoing: string[];
  assignee?: string;
  candidate_groups?: string[];
  _position?: { x: number; y: number };
}

/** 保存流程时的请求体。 */
export interface SaveProcessPayload {
  id: string;
  name: string;
  version: string;
  start_node_id: string;
  nodes: Record<string, NodeData>;
}
```

- [ ] **Step 6: 创建 src/api.ts**

```typescript
import type { ProcessDefinition, ProcessSummary, SaveProcessPayload } from "./types";

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.error || body.detail || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export async function listProcesses(): Promise<ProcessSummary[]> {
  return request<ProcessSummary[]>("/processes");
}

export async function getProcess(id: string): Promise<ProcessDefinition> {
  return request<ProcessDefinition>(`/processes/${id}`);
}

export async function createProcess(payload: SaveProcessPayload): Promise<ProcessSummary> {
  return request<ProcessSummary>("/processes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProcess(id: string, payload: SaveProcessPayload): Promise<ProcessSummary> {
  return request<ProcessSummary>(`/processes/${id}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteProcess(id: string): Promise<void> {
  return request<void>(`/processes/${id}`, { method: "DELETE" });
}
```

- [ ] **Step 7: 创建 src/transformer.ts**

React Flow 数据与后端 ProcessDefinition 数据的双向转换。

```typescript
import { type Node, type Edge, type XYPosition, MarkerType } from "@xyflow/react";
import type { ProcessDefinition, NodeData, SaveProcessPayload } from "./types";

/** React Flow 节点 data 的扩展类型。 */
export interface EditorNodeData {
  label: string;
  nodeType: "start" | "end" | "user_task";
  assignee?: string;
  originalId: string;
}

/** 默认初始位置偏移，防止节点重叠。 */
const DEFAULT_SPACING = 200;

/** 将 ProcessDefinition 转为 React Flow 的 nodes 和 edges。 */
export function toFlowNodesAndEdges(pd: ProcessDefinition): { nodes: Node<EditorNodeData>[]; edges: Edge[] } {
  const nodes: Node<EditorNodeData>[] = [];
  const edges: Edge[] = [];

  const nodeEntries = Object.entries(pd.nodes);
  for (const [id, data] of nodeEntries) {
    const pos = data._position || { x: 0, y: 0 };
    nodes.push({
      id,
      type: data.type === "user_task" ? "userTask" : data.type,
      position: pos,
      data: {
        label: data.name,
        nodeType: data.type,
        assignee: data.assignee,
        originalId: id,
      },
    });
  }

  for (const [id, data] of nodeEntries) {
    for (const targetId of data.outgoing) {
      edges.push({
        id: `${id}->${targetId}`,
        source: id,
        target: targetId,
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
      });
    }
  }

  return { nodes, edges };
}

/** 将 React Flow 的 nodes 和 edges 转为 SaveProcessPayload。 */
export function toPayload(
  id: string,
  name: string,
  version: string,
  startNodeId: string,
  nodes: Node<EditorNodeData>[],
  edges: Edge[],
): SaveProcessPayload {
  const nodeMap: Record<string, NodeData> = {};

  // 从 edges 重建 incoming/outgoing
  const incomingMap: Record<string, string[]> = {};
  const outgoingMap: Record<string, string[]> = {};
  for (const edge of edges) {
    if (!outgoingMap[edge.source]) outgoingMap[edge.source] = [];
    outgoingMap[edge.source].push(edge.target);
    if (!incomingMap[edge.target]) incomingMap[edge.target] = [];
    incomingMap[edge.target].push(edge.source);
  }

  for (const node of nodes) {
    const nd = node.data;
    const nodeData: NodeData = {
      id: node.id,
      name: nd.label,
      type: nd.nodeType,
      incoming: incomingMap[node.id] || [],
      outgoing: outgoingMap[node.id] || [],
      _position: node.position,
    };
    if (nd.nodeType === "user_task") {
      nodeData.assignee = nd.assignee;
    }
    nodeMap[node.id] = nodeData;
  }

  return { id, name, version, start_node_id: startNodeId, nodes: nodeMap };
}

/** 为新建流程生成默认的 start → end 初始节点。 */
export function defaultInitialNodes(): { nodes: Node<EditorNodeData>[]; edges: Edge[] } {
  const startPos: XYPosition = { x: 100, y: 200 };
  const endPos: XYPosition = { x: 500, y: 200 };
  return {
    nodes: [
      { id: "start", type: "start", position: startPos, data: { label: "开始", nodeType: "start", originalId: "start" } },
      { id: "end", type: "end", position: endPos, data: { label: "结束", nodeType: "end", originalId: "end" } },
    ],
    edges: [
      { id: "start->end", source: "start", target: "end", type: "smoothstep", markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 } },
    ],
  };
}
```

- [ ] **Step 8: 创建 src/styles/index.css**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1a1a1a;
  background: #f5f5f5;
}

a {
  color: inherit;
  text-decoration: none;
}
```

- [ ] **Step 9: 创建 src/main.tsx**

```typescript
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
```

- [ ] **Step 10: 创建 src/App.tsx（路由骨架）**

```typescript
import { Routes, Route } from "react-router-dom";
import ProcessList from "./components/ProcessList";
import ProcessEditor from "./components/ProcessEditor";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ProcessList />} />
      <Route path="/editor/new" element={<ProcessEditor />} />
      <Route path="/editor/:id" element={<ProcessEditor />} />
    </Routes>
  );
}
```

- [ ] **Step 11: 安装依赖并确认构建通过**

```bash
cd frontend && npm install && npm run build
```

- [ ] **Step 12: 提交**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/tsconfig.json frontend/index.html frontend/src/main.tsx frontend/src/App.tsx frontend/src/types.ts frontend/src/transformer.ts frontend/src/api.ts frontend/src/styles/index.css
git commit -m "feat: 新增前端项目骨架、类型定义和数据转换器"
```

---

### Task 3: 前端自定义节点 + FlowCanvas 画布

**Files:**
- Create: `frontend/src/components/nodes/StartNode.tsx`
- Create: `frontend/src/components/nodes/EndNode.tsx`
- Create: `frontend/src/components/nodes/UserTaskNode.tsx`
- Create: `frontend/src/components/nodes/index.ts`
- Create: `frontend/src/components/FlowCanvas.tsx`

- [ ] **Step 1: 创建 StartNode.tsx**

```typescript
import { type NodeProps, Handle, Position } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

export default function StartNode({ data }: NodeProps<Node<EditorNodeData>>) {
  const nd = data as EditorNodeData;
  return (
    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500 text-white font-semibold shadow-md">
      <Handle type="source" position={Position.Right} />
      {nd.label}
    </div>
  );
}
```

- [ ] **Step 2: 创建 EndNode.tsx**

```typescript
import { type NodeProps, Handle, Position } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

export default function EndNode({ data }: NodeProps<Node<EditorNodeData>>) {
  const nd = data as EditorNodeData;
  return (
    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-500 text-white font-semibold shadow-md">
      <Handle type="target" position={Position.Left} />
      {nd.label}
    </div>
  );
}
```

- [ ] **Step 3: 创建 UserTaskNode.tsx**

```typescript
import { type NodeProps, Handle, Position } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

export default function UserTaskNode({ data, selected }: NodeProps<Node<EditorNodeData>>) {
  const nd = data as EditorNodeData;
  return (
    <div
      className={`rounded-lg border-2 px-4 py-3 min-w-[160px] bg-white shadow-md ${
        selected ? "border-blue-500" : "border-gray-300"
      }`}
    >
      <Handle type="target" position={Position.Left} />
      <div className="font-semibold text-sm">{nd.label}</div>
      {nd.assignee && <div className="text-xs text-gray-500 mt-1">处理人: {nd.assignee}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
```

- [ ] **Step 4: 创建 nodes/index.ts（导出全部自定义节点）**

```typescript
import StartNode from "./StartNode";
import EndNode from "./EndNode";
import UserTaskNode from "./UserTaskNode";

export const nodeTypes = {
  start: StartNode,
  end: EndNode,
  userTask: UserTaskNode,
};
```

- [ ] **Step 5: 创建 FlowCanvas.tsx**

React Flow 画布组件，接受 nodes/edges 作为 props，支持拖拽、连线、选择节点。使用 `useImperativeHandle` 暴露当前 nodes/edges 供父组件读取（用于保存）。

```typescript
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  type OnConnect,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { nodeTypes } from "./nodes";
import { type EditorNodeData } from "../transformer";

export interface FlowCanvasRef {
  getNodes: () => Node<EditorNodeData>[];
  getEdges: () => Edge[];
  addNode: (node: Node<EditorNodeData>) => void;
  deleteNode: (nodeId: string) => void;
}

interface FlowCanvasProps {
  initialNodes: Node<EditorNodeData>[];
  initialEdges: Edge[];
  onNodeClick: (node: Node<EditorNodeData>) => void;
}

const FlowCanvas = forwardRef<FlowCanvasRef, FlowCanvasProps>(
  ({ initialNodes, initialEdges, onNodeClick }, ref) => {
    const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);

    // 暴露当前 nodes/edges 给父组件
    useImperativeHandle(ref, () => ({
      getNodes: () => nodes,
      getEdges: () => edges,
      addNode: (node: Node<EditorNodeData>) => setNodes((nds) => [...nds, node]),
      deleteNode: (nodeId: string) => {
        setNodes((nds) => nds.filter((n) => n.id !== nodeId));
        setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      },
    }));

    // 当父组件传入新的初始数据时同步（例如加载已有流程）
    const loadedId = useRef<string | null>(null);
    useEffect(() => {
      const key = initialNodes.map((n) => n.id).join(",");
      if (key && key !== loadedId.current) {
        setNodes(initialNodes);
        loadedId.current = key;
      }
    }, [initialNodes, setNodes]);

    useEffect(() => {
      const key = initialEdges.map((e) => e.id).join(",");
      if (key) {
        setEdges(initialEdges);
      }
    }, [initialEdges, setEdges]);

    const handleNodesChange: OnNodesChange = (changes) => {
      onNodesChangeInternal(changes);
    };

    const handleEdgesChange: OnEdgesChange = (changes) => {
      onEdgesChangeInternal(changes);
    };

    const onConnect: OnConnect = (connection) => {
      setEdges((eds) => addEdge(connection, eds));
    };

    return (
      <div style={{ width: "100%", height: "100%" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => onNodeClick(node as Node<EditorNodeData>)}
          fitView
          deleteKeyCode="Backspace"
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    );
  },
);

export default FlowCanvas;
```

- [ ] **Step 6: 安装 Tailwind CSS**

由于 React Flow 节点使用了 Tailwind 类，需要添加 Tailwind：

```bash
cd frontend && npm install -D tailwindcss @tailwindcss/vite
```

在 `frontend/vite.config.ts` 顶部添加：

```typescript
import tailwindcss from "@tailwindcss/vite";
```

在 `plugins` 数组中加上 `tailwindcss()`：

```typescript
plugins: [react(), tailwindcss()],
```

在 `frontend/src/styles/index.css` 顶部添加：

```css
@import "tailwindcss";
```

- [ ] **Step 7: 提交**

```bash
git add frontend/src/components/nodes/StartNode.tsx frontend/src/components/nodes/EndNode.tsx frontend/src/components/nodes/UserTaskNode.tsx frontend/src/components/nodes/index.ts frontend/src/components/FlowCanvas.tsx
git commit -m "feat: 新增 React Flow 自定义节点和画布组件"
```

---

### Task 4: 前端流程列表页 + 工具栏

**Files:**
- Create: `frontend/src/components/ProcessCard.tsx`
- Create: `frontend/src/components/ProcessList.tsx`
- Create: `frontend/src/components/NodeToolbar.tsx`

- [ ] **Step 1: 创建 ProcessCard.tsx**

```typescript
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { deleteProcess } from "../api";
import type { ProcessSummary } from "../types";

interface ProcessCardProps {
  process: ProcessSummary;
  onDeleted: () => void;
}

export default function ProcessCard({ process, onDeleted }: ProcessCardProps) {
  const [confirming, setConfirming] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteProcess(process.id);
      onDeleted();
    } catch (e) {
      alert(`删除失败: ${e}`);
    }
  };

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm border border-gray-200">
      <Link to={`/editor/${process.id}`} className="flex-1">
        <div className="font-semibold">{process.name}</div>
        <div className="text-sm text-gray-500">{process.id} · v{process.version}</div>
      </Link>
      {confirming ? (
        <div className="flex gap-2 ml-4">
          <button onClick={handleDelete} className="px-3 py-1 text-sm bg-red-500 text-white rounded">
            确认
          </button>
          <button onClick={() => setConfirming(false)} className="px-3 py-1 text-sm border rounded">
            取消
          </button>
        </div>
      ) : (
        <button
          onClick={() => setConfirming(true)}
          className="ml-4 px-3 py-1 text-sm text-red-500 border border-red-300 rounded hover:bg-red-50"
        >
          删除
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 创建 ProcessList.tsx**

```typescript
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProcesses } from "../api";
import type { ProcessSummary } from "../types";
import ProcessCard from "./ProcessCard";

export default function ProcessList() {
  const [processes, setProcesses] = useState<ProcessSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadProcesses = async () => {
    setLoading(true);
    try {
      const data = await listProcesses();
      setProcesses(data);
    } catch (e) {
      alert(`加载失败: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProcesses();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">BPMS 流程编辑器</h1>
        <Link
          to="/editor/new"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          新建流程
        </Link>
      </header>

      <main className="max-w-3xl mx-auto p-6">
        {loading ? (
          <p className="text-gray-500">加载中...</p>
        ) : processes.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">暂无流程定义</p>
            <Link
              to="/editor/new"
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              创建第一个流程
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {processes.map((p) => (
              <ProcessCard key={p.id} process={p} onDeleted={loadProcesses} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 3: 创建 NodeToolbar.tsx**

画布顶部工具栏，用于向画布添加新节点。

```typescript
import { useCallback } from "react";
import { type Node, Panel, useReactFlow } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

interface NodeToolbarProps {
  onAddNode: (node: Node<EditorNodeData>) => void;
}

let newNodeId = 1;

export default function NodeToolbar({ onAddNode }: NodeToolbarProps) {
  const { screenToFlowPosition } = useReactFlow();

  const addUserTask = useCallback(() => {
    const position = screenToFlowPosition({ x: 300, y: 200 });
    const id = `node_${newNodeId++}`;
    onAddNode({
      id,
      type: "userTask",
      position,
      data: { label: "新任务", nodeType: "user_task", assignee: "", originalId: id },
    });
  }, [screenToFlowPosition, onAddNode]);

  return (
    <Panel position="top-left">
      <div className="flex gap-2 p-2 bg-white rounded-lg shadow-md border border-gray-200">
        <button
          onClick={addUserTask}
          className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + 任务节点
        </button>
      </div>
    </Panel>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ProcessCard.tsx frontend/src/components/ProcessList.tsx frontend/src/components/NodeToolbar.tsx
git commit -m "feat: 新增流程列表页和节点添加工具栏"
```

---

### Task 5: 前端流程编辑器 + 属性面板 + 保存

**Files:**
- Create: `frontend/src/components/PropertyPanel.tsx`
- Create: `frontend/src/components/ProcessEditor.tsx`
- Modify: `frontend/src/App.tsx` (更新路由样式)
- Modify: `.gitignore`

- [ ] **Step 1: 创建 PropertyPanel.tsx**

右侧属性编辑面板，点击节点后显示可编辑字段。

```typescript
import { useState, useEffect } from "react";
import { type Node } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

interface PropertyPanelProps {
  node: Node<EditorNodeData> | null;
  onUpdateNode: (node: Node<EditorNodeData>) => void;
  onDeleteNode: (nodeId: string) => void;
  onClose: () => void;
}

export default function PropertyPanel({ node, onUpdateNode, onDeleteNode, onClose }: PropertyPanelProps) {
  const [label, setLabel] = useState("");
  const [assignee, setAssignee] = useState("");

  useEffect(() => {
    if (node) {
      setLabel(node.data.label);
      setAssignee(node.data.assignee || "");
    }
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onUpdateNode({
      ...node,
      data: { ...node.data, label, assignee: node.data.nodeType === "user_task" ? assignee : undefined },
    });
  };

  return (
    <div className="w-64 bg-white border-l border-gray-200 p-4 h-full overflow-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">节点属性</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ✕
        </button>
      </div>

      <div className="text-xs text-gray-400 mb-3">ID: {node.id}</div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm text-gray-600 mb-1">名称</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
          />
        </div>

        {node.data.nodeType === "user_task" && (
          <div>
            <label className="block text-sm text-gray-600 mb-1">处理人</label>
            <input
              type="text"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              placeholder="例如: manager"
            />
          </div>
        )}

        <button
          onClick={handleSave}
          className="w-full px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          应用
        </button>

        {node.data.nodeType !== "start" && node.data.nodeType !== "end" && (
          <button
            onClick={() => onDeleteNode(node.id)}
            className="w-full px-3 py-1.5 bg-red-500 text-white rounded text-sm hover:bg-red-600"
          >
            删除节点
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 ProcessEditor.tsx**

编辑器主页面，组装 FlowCanvas、NodeToolbar、PropertyPanel，处理加载和保存逻辑。

```typescript
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { type Node, type Edge } from "@xyflow/react";
import { getProcess, createProcess, updateProcess } from "../api";
import type { ProcessDefinition, SaveProcessPayload } from "../types";
import { toFlowNodesAndEdges, toPayload, defaultInitialNodes, type EditorNodeData } from "../transformer";
import FlowCanvas, { type FlowCanvasRef } from "./FlowCanvas";
import NodeToolbar from "./NodeToolbar";
import PropertyPanel from "./PropertyPanel";

export default function ProcessEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === "new";
  const canvasRef = useRef<FlowCanvasRef>(null);

  const [initialNodes, setInitialNodes] = useState<Node<EditorNodeData>[]>([]);
  const [initialEdges, setInitialEdges] = useState<Edge[]>([]);
  const [processName, setProcessName] = useState("");
  const [processId, setProcessId] = useState("");
  const [selectedNode, setSelectedNode] = useState<Node<EditorNodeData> | null>(null);
  const [startNodeId] = useState("start");

  // 加载已有流程
  useEffect(() => {
    if (!isNew && id) {
      getProcess(id).then((pd: ProcessDefinition) => {
        setProcessName(pd.name);
        setProcessId(pd.id);
        const { nodes: n, edges: e } = toFlowNodesAndEdges(pd);
        setInitialNodes(n);
        setInitialEdges(e);
      }).catch((e: Error) => {
        alert(`加载失败: ${e.message}`);
        navigate("/");
      });
    } else {
      const def = defaultInitialNodes();
      setInitialNodes(def.nodes);
      setInitialEdges(def.edges);
      setProcessName("新流程");
    }
  }, [id, isNew, navigate]);

  // 保存
  const handleSave = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const currentNodes = canvas.getNodes();
    const currentEdges = canvas.getEdges();
    // 过滤已删除的节点
    const nodes = currentNodes.filter((n) => !(n.data as any)._deleted);

    const name = prompt("流程名称:", processName);
    if (!name) return;

    let pid = processId;
    if (!pid) {
      pid = prompt("流程 ID（英文数字和连字符）:") || "";
      if (!pid) return;
    }

    const payload = toPayload(pid, name, "1.0", startNodeId, nodes, currentEdges);

    try {
      if (isNew) {
        await createProcess(payload);
        alert("流程已创建");
      } else {
        await updateProcess(pid, payload);
        alert("流程已更新");
      }
      navigate("/");
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    }
  };

  const handleNodeClick = useCallback((node: Node<EditorNodeData>) => {
    setSelectedNode(node);
  }, []);

  const handleUpdateNode = useCallback((updated: Node<EditorNodeData>) => {
    setSelectedNode(updated);
  }, []);

  const handleDeleteNode = useCallback((nodeId: string) => {
    canvasRef.current?.deleteNode(nodeId);
    setSelectedNode(null);
  }, []);

  const handleAddNode = useCallback((node: Node<EditorNodeData>) => {
    canvasRef.current?.addNode(node);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* 顶部栏 */}
      <header className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate("/")} className="text-sm text-gray-500 hover:text-gray-700">
            ← 返回列表
          </button>
          <span className="font-semibold">{processName || "新流程"}</span>
        </div>
        <button
          onClick={handleSave}
          className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          保存
        </button>
      </header>

      {/* 主内容 */}
      <div className="flex-1 flex">
        <div className="flex-1 relative">
          <FlowCanvas
            ref={canvasRef}
            initialNodes={initialNodes}
            initialEdges={initialEdges}
            onNodeClick={handleNodeClick}
          />
          <NodeToolbar onAddNode={handleAddNode} />
        </div>
        <PropertyPanel node={selectedNode} onUpdateNode={handleUpdateNode} onDeleteNode={handleDeleteNode} onClose={() => setSelectedNode(null)} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 更新 .gitignore**

在 `.gitignore` 中添加：

```
# 前端构建产物
src/bpms/static/
frontend/node_modules/
```

- [ ] **Step 4: 构建前端并验证**

```bash
cd frontend && npm run build
```

构建产物应输出到 `src/bpms/static/` 目录。

- [ ] **Step 5: 提交**

```bash
git add .gitignore frontend/src/components/PropertyPanel.tsx frontend/src/components/ProcessEditor.tsx
git commit -m "feat: 新增流程编辑器页面、属性面板和保存功能"
```

---

### Task 6: 集成 — 构建前端 + 启动验证

**Files:**
- Modify: `src/bpms/__init__.py` (确保 static 目录存在)

- [ ] **Step 1: 构建前端产物到 static 目录**

```bash
cd frontend && npm run build
```

确认 `src/bpms/static/index.html` 存在。

- [ ] **Step 2: 手动启动服务验证**

```bash
python -m bpms serve
```

打开浏览器访问 `http://127.0.0.1:8000`，验证：

1. 流程列表页正常显示
2. 点击"新建流程"进入编辑器
3. 画布上显示开始和结束节点
4. 可以拖拽节点位置
5. 可以添加任务节点
6. 可以连线节点
7. 点击节点弹出属性面板，可编辑名称和 assignee
8. 保存流程后返回列表页可以看到新流程
9. 点击已有流程进入编辑，可以修改并保存

- [ ] **Step 3: 运行全部测试确认通过**

```bash
pytest tests/unit/ -v
```

- [ ] **Step 4: 提交**

```bash
git add src/bpms/static/
git commit -m "feat: 构建前端产物并集成到 FastAPI 服务"
```
