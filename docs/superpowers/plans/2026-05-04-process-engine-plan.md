# 流程引擎实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现可运行的流程引擎，支持从 JSON 文件加载流程定义、发起流程实例、在人工节点间流转并完成流程。

**Architecture:** 单一模块引擎 + CLI 交互 + JSON 文件存储。Engine 负责流转逻辑，Store 负责持久化，CLI 提供命令行入口。

**Tech Stack:** Python 3.10+, dataclasses, argparse, json, pathlib, pytest

---

### 任务总览

| 任务 | 内容 | 新增/修改文件 |
|------|------|---------------|
| 1 | 新增实例模型 | `models/instance.py`, `models/__init__.py` |
| 2 | 新增序列化模块 | `models/serialization.py`, `models/process.py` |
| 3 | 新增存储层 | `store.py`, `__init__.py` |
| 4 | 新增引擎核心 | `engine.py` |
| 5 | 新增 CLI | `cli.py`, `__main__.py` |
| 6 | 集成测试 | `tests/integration/test_workflow.py` |
| 7 | 端到端测试 | `tests/e2e/test_cli_flow.py` |

---

## Task 1: 新增实例模型

**Files:**
- Create: `src/bpms/models/instance.py`
- Modify: `src/bpms/models/__init__.py`
- Create: `tests/unit/test_models/test_instance.py`

- [ ] **Step 1: 编写测试 — 流程实例创建**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_models/test_instance.py -v`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 instance.py**

```python
"""流程实例和任务实例数据类型。"""

from dataclasses import dataclass, field


class ProcessStatus(str):
    RUNNING = "running"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class TaskStatus(str):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class ProcessInstance:
    """运行中的流程实例。"""

    id: str
    process_id: str
    version: str
    current_node_id: str = ""
    status: str = ProcessStatus.RUNNING
    created_at: str = ""
    variables: dict = field(default_factory=dict)


@dataclass
class TaskInstance:
    """人工任务实例。"""

    id: str
    process_instance_id: str
    node_id: str
    assignee: str = ""
    status: str = TaskStatus.PENDING
    started_at: str = ""
    completed_at: str | None = None
```

- [ ] **Step 4: 更新 models/__init__.py**

```python
from .instance import ProcessInstance, ProcessStatus, TaskInstance, TaskStatus
from .node import BaseNode, NodeType, UserTaskNode
from .process import ProcessDefinition

__all__ = [
    "BaseNode",
    "NodeType",
    "ProcessDefinition",
    "ProcessInstance",
    "ProcessStatus",
    "TaskInstance",
    "TaskStatus",
    "UserTaskNode",
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_models/test_instance.py -v`
Expected: All tests PASS

- [ ] **Step 6: 提交**

```bash
git add src/bpms/models/instance.py src/bpms/models/__init__.py tests/unit/test_models/test_instance.py
git commit -m "feat: 新增流程实例和任务实例数据模型"
```

---

## Task 2: 新增序列化模块

**Files:**
- Create: `src/bpms/models/serialization.py`
- Modify: `src/bpms/models/__init__.py`
- Modify: `src/bpms/models/process.py`
- Create: `tests/unit/test_models/test_serialization.py`

- [ ] **Step 1: 编写测试 — 流程定义序列化/反序列化**

```python
"""序列化模块单元测试。"""

import json
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_models/test_serialization.py -v`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 serialization.py**

```python
"""流程定义 JSON 序列化/反序列化。"""

from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode


class ProcessDefinitionSerializer:
    """流程定义 JSON 序列化器。"""

    @staticmethod
    def serialize(pd: ProcessDefinition) -> dict:
        nodes = {}
        for node_id, node in pd.nodes.items():
            node_data = {
                "id": node.id,
                "name": node.name,
                "type": node.node_type.value,
                "incoming": node.incoming,
                "outgoing": node.outgoing,
            }
            if isinstance(node, UserTaskNode):
                node_data["assignee"] = node.assignee
                node_data["candidate_groups"] = node.candidate_groups
            nodes[node_id] = node_data
        return {
            "id": pd.id,
            "name": pd.name,
            "version": pd.version,
            "start_node_id": pd.start_node_id,
            "nodes": nodes,
        }

    @staticmethod
    def deserialize(data: dict) -> ProcessDefinition:
        nodes = {}
        for node_id, node_data in data["nodes"].items():
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
            version=data["version"],
            nodes=nodes,
            start_node_id=data.get("start_node_id", ""),
        )
```

- [ ] **Step 4: 更新 models/__init__.py，添加 serialization 导出**

```python
from .instance import ProcessInstance, ProcessStatus, TaskInstance, TaskStatus
from .node import BaseNode, NodeType, UserTaskNode
from .process import ProcessDefinition
from .serialization import ProcessDefinitionSerializer

__all__ = [
    "BaseNode",
    "NodeType",
    "ProcessDefinition",
    "ProcessDefinitionSerializer",
    "ProcessInstance",
    "ProcessStatus",
    "TaskInstance",
    "TaskStatus",
    "UserTaskNode",
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_models/test_serialization.py -v`
Expected: All tests PASS

- [ ] **Step 6: 提交**

```bash
git add src/bpms/models/serialization.py src/bpms/models/__init__.py tests/unit/test_models/test_serialization.py
git commit -m "feat: 新增流程定义 JSON 序列化模块"
```

---

## Task 3: 新增存储层

**Files:**
- Create: `src/bpms/store.py`
- Modify: `src/bpms/__init__.py`
- Create: `tests/unit/test_store.py`

- [ ] **Step 1: 编写测试 — 存储层**

```python
"""存储层单元测试。"""

import json
import pytest
import tempfile
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_store.py -v`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 store.py**

```python
"""JSON 文件存储层。"""

import json
from datetime import datetime, timezone
from pathlib import Path

from bpms.models import ProcessDefinition, ProcessDefinitionSerializer
from bpms.models.instance import ProcessInstance, TaskInstance


class Store:
    """JSON 文件存储。"""

    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self._data_dir = data_dir
        self._processes_dir = self._data_dir / "processes"
        self._instances_dir = self._data_dir / "instances"
        self._processes_dir.mkdir(parents=True, exist_ok=True)
        self._instances_dir.mkdir(parents=True, exist_ok=True)

    def save_process_definition(self, pd: ProcessDefinition) -> None:
        data = ProcessDefinitionSerializer.serialize(pd)
        path = self._processes_dir / f"{pd.id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_process_definition(self, process_id: str) -> ProcessDefinition:
        path = self._processes_dir / f"{process_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"流程定义不存在: {process_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProcessDefinitionSerializer.deserialize(data)

    def list_process_definitions(self) -> list[ProcessDefinition]:
        pds = []
        for path in sorted(self._processes_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            pds.append(ProcessDefinitionSerializer.deserialize(data))
        return pds

    def save_instance(self, instance: ProcessInstance) -> None:
        path = self._instances_dir / f"{instance.id}.json"
        data = {
            "id": instance.id,
            "process_id": instance.process_id,
            "version": instance.version,
            "current_node_id": instance.current_node_id,
            "status": instance.status,
            "created_at": instance.created_at,
            "variables": instance.variables,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_instance(self, instance_id: str) -> ProcessInstance:
        path = self._instances_dir / f"{instance_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"流程实例不存在: {instance_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProcessInstance(
            id=data["id"],
            process_id=data["process_id"],
            version=data["version"],
            current_node_id=data["current_node_id"],
            status=data["status"],
            created_at=data["created_at"],
            variables=data.get("variables", {}),
        )

    def save_task(self, instance_id: str, task: TaskInstance) -> None:
        path = self._instances_dir / f"{instance_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"流程实例不存在: {instance_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks = data.get("tasks", [])
        task_data = {
            "id": task.id,
            "process_instance_id": task.process_instance_id,
            "node_id": task.node_id,
            "assignee": task.assignee,
            "status": task.status,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }
        # 更新已存在任务或追加
        for i, t in enumerate(tasks):
            if t["id"] == task.id:
                tasks[i] = task_data
                break
        else:
            tasks.append(task_data)
        data["tasks"] = tasks
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_tasks_for_instance(self, instance_id: str) -> list[TaskInstance]:
        path = self._instances_dir / f"{instance_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"流程实例不存在: {instance_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks = []
        for t in data.get("tasks", []):
            tasks.append(TaskInstance(
                id=t["id"],
                process_instance_id=t["process_instance_id"],
                node_id=t["node_id"],
                assignee=t.get("assignee", ""),
                status=t["status"],
                started_at=t.get("started_at", ""),
                completed_at=t.get("completed_at"),
            ))
        return tasks
```

- [ ] **Step 4: 更新 `__init__.py`，添加 Store 导出**

```python
"""BPMS Process Engine."""

__version__ = "0.1.0"
```

(保持不变，store 直接从 store.py 导入)

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_store.py -v`
Expected: All tests PASS

- [ ] **Step 6: 提交**

```bash
git add src/bpms/store.py tests/unit/test_store.py
git commit -m "feat: 新增 JSON 文件存储层"
```

---

## Task 4: 新增引擎核心

**Files:**
- Create: `src/bpms/engine.py`
- Create: `tests/unit/test_engine.py`

- [ ] **Step 1: 编写测试 — 引擎核心逻辑**

```python
"""流程引擎核心单元测试。"""

import pytest
from pathlib import Path

from bpms.engine import ProcessEngine
from bpms.models import BaseNode, NodeType, ProcessDefinition, UserTaskNode
from bpms.models.instance import ProcessInstance, ProcessStatus, TaskInstance, TaskStatus
from bpms.store import Store


@pytest.fixture
def engine(tmp_path: Path) -> ProcessEngine:
    return Store(data_dir=tmp_path)


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
    def test_load_process_definition_from_file(self, engine: ProcessEngine, tmp_path: Path):
        pd = _create_sample_process_definition()
        engine.store.save_process_definition(pd)

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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_engine.py -v`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 engine.py**

```python
"""流程引擎核心逻辑。"""

import uuid
from datetime import datetime, timezone

from bpms.models import ProcessDefinition
from bpms.models.instance import ProcessInstance, ProcessStatus, TaskInstance, TaskStatus
from bpms.store import Store


class ProcessEngine:
    """流程引擎。"""

    def __init__(self, store: Store):
        self.store = store

    def load_process_definition(self, process_id: str) -> ProcessDefinition:
        """加载已注册的流程定义。"""
        return self.store.load_process_definition(process_id)

    def start_instance(self, process_id: str) -> ProcessInstance:
        """发起新流程实例。"""
        pd = self.store.load_process_definition(process_id)
        instance_id = uuid.uuid4().hex[:8]
        instance = ProcessInstance(
            id=instance_id,
            process_id=pd.id,
            version=pd.version,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # 从 start 节点流转到第一个 user_task
        self._advance(instance, pd)

        self.store.save_instance(instance)
        return instance

    def complete_task(self, task_id: str) -> ProcessInstance:
        """完成指定任务并流转。"""
        # 找到任务所属的实例
        instance = self._find_instance_by_task(task_id)
        pd = self.store.load_process_definition(instance.process_id)

        # 标记任务完成
        task = self._get_task(instance.id, task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        self.store.save_task(instance.id, task)

        # 流转到下一节点
        self._advance(instance, pd)

        self.store.save_instance(instance)
        return instance

    def get_pending_tasks(self, instance_id: str) -> list[TaskInstance]:
        """获取实例的待办任务。"""
        all_tasks = self.store.get_tasks_for_instance(instance_id)
        return [t for t in all_tasks if t.status == TaskStatus.PENDING]

    def get_instance(self, instance_id: str) -> ProcessInstance:
        """获取实例详情。"""
        return self.store.load_instance(instance_id)

    def _advance(self, instance: ProcessInstance, pd: ProcessDefinition) -> None:
        """从当前节点流转到下一节点。"""
        if instance.current_node_id == "":
            # 首次启动，从 start 节点开始
            current = pd.nodes[pd.start_node_id]
        else:
            current = pd.nodes[instance.current_node_id]

        # 沿 outgoing 找到下一节点
        if not current.outgoing:
            # 没有下一节点，保持当前状态
            return

        next_node_id = current.outgoing[0]
        next_node = pd.nodes[next_node_id]
        instance.current_node_id = next_node_id

        if next_node.node_type.value == "user_task":
            # 创建新任务
            task = TaskInstance(
                id=uuid.uuid4().hex[:8],
                process_instance_id=instance.id,
                node_id=next_node_id,
                assignee=next_node.assignee or "",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            self.store.save_task(instance.id, task)
        elif next_node.node_type.value == "end":
            # 流程结束
            instance.status = ProcessStatus.COMPLETED

    def _find_instance_by_task(self, task_id: str) -> ProcessInstance:
        """通过任务 ID 找到所属实例。"""
        for path in self.store._instances_dir.glob("*.json"):
            instance = self.store.load_instance(path.stem)
            tasks = self.store.get_tasks_for_instance(instance.id)
            if any(t.id == task_id for t in tasks):
                return instance
        raise ValueError(f"任务不存在: {task_id}")

    def _get_task(self, instance_id: str, task_id: str) -> TaskInstance:
        """获取指定任务。"""
        tasks = self.store.get_tasks_for_instance(instance_id)
        for t in tasks:
            if t.id == task_id:
                return t
        raise ValueError(f"任务不存在: {task_id}")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/test_engine.py -v`
Expected: All tests PASS

- [ ] **Step 5: 提交**

```bash
git add src/bpms/engine.py tests/unit/test_engine.py
git commit -m "feat: 新增流程引擎核心逻辑"
```

---

## Task 5: 新增 CLI

**Files:**
- Create: `src/bpms/cli.py`
- Modify: `src/bpms/__main__.py`
- Create: `tests/unit/test_cli.py`

- [ ] **Step 1: 编写测试 — CLI 基本功能**

```python
"""CLI 模块单元测试。"""

import argparse
import pytest
from io import StringIO
from unittest.mock import patch

from bpms.cli import create_parser


@pytest.mark.unit
class TestCLIParser:
    def test_create_parser_has_all_subcommands(self):
        parser = create_parser()
        actions = {a.dest for a in parser._subparsers._actions if hasattr(a, "_group_actions")}
        # 扁平化所有子命令
        subcommands = set()
        for action in parser._subparsers._actions:
            if hasattr(action, "choices"):
                subcommands.update(action.choices.keys())

        assert "list-processes" in subcommands
        assert "start" in subcommands
        assert "tasks" in subcommands
        assert "complete" in subcommands
        assert "show" in subcommands
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/test_cli.py -v`
Expected: FAIL — 模块不存在

- [ ] **Step 3: 实现 cli.py**

```python
"""BPMS 命令行界面。"""

import argparse
from pathlib import Path

from bpms.engine import ProcessEngine
from bpms.store import Store


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bpms", description="BPMS 流程引擎")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-processes", help="列出所有流程定义")

    start_p = subparsers.add_parser("start", help="发起新流程")
    start_p.add_argument("process_id", help="流程定义 ID")

    tasks_p = subparsers.add_parser("tasks", help="查看待办任务")
    tasks_p.add_argument("instance_id", nargs="?", help="流程实例 ID（可选）")

    complete_p = subparsers.add_parser("complete", help="完成任务")
    complete_p.add_argument("task_id", help="任务 ID")

    show_p = subparsers.add_parser("show", help="查看实例状态")
    show_p.add_argument("instance_id", help="流程实例 ID")

    return parser


def run(args: list[str] | None = None) -> None:
    parser = create_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return

    store = Store()
    engine = ProcessEngine(store)

    if parsed.command == "list-processes":
        cmd_list_processes(engine)
    elif parsed.command == "start":
        cmd_start(engine, parsed.process_id)
    elif parsed.command == "tasks":
        cmd_tasks(engine, parsed.instance_id)
    elif parsed.command == "complete":
        cmd_complete(engine, parsed.task_id)
    elif parsed.command == "show":
        cmd_show(engine, parsed.instance_id)


def cmd_list_processes(engine: ProcessEngine) -> None:
    pds = engine.store.list_process_definitions()
    if not pds:
        print("暂无流程定义")
        return
    for pd in pds:
        print(f"{pd.id} ({pd.name}) v{pd.version}")


def cmd_start(engine: ProcessEngine, process_id: str) -> None:
    instance = engine.start_instance(process_id)
    print(f"流程实例已创建: {instance.id}")
    pending = engine.get_pending_tasks(instance.id)
    if pending:
        task = pending[0]
        print(f"当前任务: [{task.id}] {task.node_id} (assignee: {task.assignee})")
    else:
        print("流程已直接结束")


def cmd_tasks(engine: ProcessEngine, instance_id: str | None) -> None:
    if instance_id:
        instances = [engine.get_instance(instance_id)]
    else:
        import glob
        instances = []
        for path in sorted(engine.store._instances_dir.glob("*.json")):
            instances.append(engine.load_instance(path.stem))

    found = False
    for inst in instances:
        pending = engine.get_pending_tasks(inst.id)
        if pending:
            found = True
            task_ids = ", ".join(f"[{t.id}] {t.node_id} (assignee: {t.assignee})" for t in pending)
            print(f"实例 {inst.id} 待办: {task_ids}")

    if not found:
        print("暂无待办任务")


def cmd_complete(engine: ProcessEngine, task_id: str) -> None:
    instance = engine.complete_task(task_id)
    print(f"任务完成")

    if instance.status == "completed":
        print(f"流程实例 {instance.id} 已完成")
    else:
        pending = engine.get_pending_tasks(instance.id)
        if pending:
            task = pending[0]
            print(f"当前任务: [{task.id}] {task.node_id} (assignee: {task.assignee})")


def cmd_show(engine: ProcessEngine, instance_id: str) -> None:
    instance = engine.get_instance(instance_id)
    print(f"实例 ID: {instance.id}")
    print(f"流程定义: {instance.process_id} v{instance.version}")
    print(f"状态: {instance.status}")
    print(f"当前节点: {instance.current_node_id}")
    tasks = engine.store.get_tasks_for_instance(instance_id)
    if tasks:
        print(f"任务:")
        for t in tasks:
            print(f"  [{t.id}] {t.node_id} - {t.status} (assignee: {t.assignee})")
```

- [ ] **Step 4: 更新 __main__.py**

```python
"""BPMS Process Engine entry point."""

from bpms import __version__
from bpms.cli import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/unit/test_cli.py -v`
Expected: All tests PASS

- [ ] **Step 6: 运行全部 unit 测试**

Run: `pytest tests/unit/ -v`
Expected: All tests PASS

- [ ] **Step 7: 提交**

```bash
git add src/bpms/cli.py src/bpms/__main__.py tests/unit/test_cli.py
git commit -m "feat: 新增命令行界面"
```

---

## Task 6: 集成测试

**Files:**
- Create: `tests/integration/test_workflow.py`

- [ ] **Step 1: 编写集成测试 — 完整流程流转**

```python
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
```

- [ ] **Step 2: 运行测试**

Run: `pytest tests/integration/ -v -m integration`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_workflow.py
git commit -m "test: 添加完整流程流转集成测试"
```

---

## Task 7: 端到端测试

**Files:**
- Create: `tests/e2e/test_cli_flow.py`

- [ ] **Step 1: 编写端到端测试 — CLI 完整流程**

```python
"""CLI 完整流程端到端测试。"""

import json
import pytest
from pathlib import Path

from bpms.cli import run
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
    from unittest.mock import patch

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
        # 提取任务 ID（格式为 "[task-id] node_id (assignee: xxx)"）
        import re
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
```

- [ ] **Step 2: 运行测试**

Run: `pytest tests/e2e/ -v -m e2e`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_cli_flow.py
git commit -m "test: 添加 CLI 完整流程端到端测试"
```

---

## 附录：数据目录

需要创建 `.gitignore` 条目以忽略运行时数据：

- [ ] **Step 1: 更新 .gitignore**

在 `.gitignore` 中添加：

```
# BPMS 运行时数据
src/bpms/data/instances/
src/bpms/data/processes/*.json
```

（保留目录结构，仅忽略具体 JSON 文件）

- [ ] **Step 2: 创建 data 目录占位**

```bash
mkdir -p src/bpms/data/processes src/bpms/data/instances
touch src/bpms/data/processes/.gitkeep
touch src/bpms/data/instances/.gitkeep
```

- [ ] **Step 3: 提交**

```bash
git add .gitignore src/bpms/data/processes/.gitkeep src/bpms/data/instances/.gitkeep
git commit -m "chore: 添加运行时数据目录"
```
