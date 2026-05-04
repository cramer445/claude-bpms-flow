"""流程图节点数据类型定义。"""

from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    """节点类型枚举，可扩展。"""

    START = "start"
    END = "end"
    USER_TASK = "user_task"


@dataclass
class BaseNode:
    """流程图节点基类。"""

    id: str
    name: str
    node_type: NodeType
    description: str = ""
    incoming: list[str] = field(default_factory=list)
    outgoing: list[str] = field(default_factory=list)


@dataclass
class UserTaskNode(BaseNode):
    """人工任务节点。"""

    node_type: NodeType = field(default=NodeType.USER_TASK, init=False)
    assignee: str | None = None
    candidate_groups: list[str] = field(default_factory=list)
