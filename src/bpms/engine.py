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

        # 从 start 节点流转到第一个 user_task，设置 current_node_id
        start_node = pd.nodes[pd.start_node_id]
        next_node_id = start_node.outgoing[0]
        next_node = pd.nodes[next_node_id]
        instance.current_node_id = next_node_id

        # 先保存实例文件（save_task 依赖实例文件已存在）
        self.store.save_instance(instance)

        if next_node.node_type.value == "user_task":
            task = TaskInstance(
                id=uuid.uuid4().hex[:8],
                process_instance_id=instance.id,
                node_id=next_node_id,
                assignee=next_node.assignee or "",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            self.store.save_task(instance.id, task)

        return instance

    def complete_task(self, task_id: str) -> ProcessInstance:
        """完成指定任务并流转。"""
        instance = self._find_instance_by_task(task_id)
        pd = self.store.load_process_definition(instance.process_id)

        # 标记任务完成
        task = self._get_task(instance.id, task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc).isoformat()

        # 流转到下一节点（只更新 current_node_id 和 status）
        self._advance(instance, pd)

        # 先保存实例（避免覆盖任务）
        self.store.save_instance(instance)

        # 再保存已完成的任务（此时实例文件已存在）
        self.store.save_task(instance.id, task)

        # 如果下一节点是 user_task，创建新任务
        if instance.current_node_id and instance.status == ProcessStatus.RUNNING:
            next_node = pd.nodes[instance.current_node_id]
            if next_node.node_type.value == "user_task":
                new_task = TaskInstance(
                    id=uuid.uuid4().hex[:8],
                    process_instance_id=instance.id,
                    node_id=instance.current_node_id,
                    assignee=next_node.assignee or "",
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                self.store.save_task(instance.id, new_task)

        return instance

    def get_pending_tasks(self, instance_id: str) -> list[TaskInstance]:
        """获取实例的待办任务。"""
        all_tasks = self.store.get_tasks_for_instance(instance_id)
        return [t for t in all_tasks if t.status == TaskStatus.PENDING]

    def get_instance(self, instance_id: str) -> ProcessInstance:
        """获取实例详情。"""
        return self.store.load_instance(instance_id)

    def _advance(self, instance: ProcessInstance, pd: ProcessDefinition) -> None:
        """从当前节点流转到下一节点，仅更新 current_node_id 和 status。"""
        if instance.current_node_id == "":
            current = pd.nodes[pd.start_node_id]
        else:
            current = pd.nodes[instance.current_node_id]

        if not current.outgoing:
            return

        next_node_id = current.outgoing[0]
        next_node = pd.nodes[next_node_id]
        instance.current_node_id = next_node_id

        if next_node.node_type.value == "end":
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
