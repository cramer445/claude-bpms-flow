"""流程实例和任务实例数据类型。"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ProcessStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
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
    variables: dict[str, object] = field(default_factory=dict)


@dataclass
class TaskInstance:
    """人工任务实例。"""

    id: str
    process_instance_id: str
    node_id: str
    assignee: str = ""
    status: str = TaskStatus.PENDING
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
