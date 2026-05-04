"""JSON 文件存储层。"""

import json
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
        # 保留已有任务数据
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            data["tasks"] = existing.get("tasks", [])
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

    def list_instances(self) -> list[ProcessInstance]:
        """列出所有流程实例。"""
        instances = []
        for path in sorted(self._instances_dir.glob("*.json")):
            instances.append(self.load_instance(path.stem))
        return instances
