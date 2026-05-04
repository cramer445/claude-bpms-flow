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
