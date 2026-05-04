"""流程图定义数据类型。"""

from dataclasses import dataclass, field

from .node import BaseNode


@dataclass
class ProcessDefinition:
    """流程图定义。"""

    id: str
    name: str
    version: str
    nodes: dict[str, BaseNode] = field(default_factory=dict)
    start_node_id: str = ""
