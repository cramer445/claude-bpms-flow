"""流程实例和任务实例数据类型。"""

from dataclasses import dataclass, field
from datetime import datetime


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
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
