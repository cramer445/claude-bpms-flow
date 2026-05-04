import { type Node, type Edge, type XYPosition, MarkerType } from "@xyflow/react";
import type { ProcessDefinition, NodeData, SaveProcessPayload } from "./types";

/** React Flow 节点 data 的扩展类型。 */
export interface EditorNodeData extends Record<string, unknown> {
  label: string;
  nodeType: "start" | "end" | "user_task";
  assignee?: string;
  originalId: string;
}

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

/** 为新建流程生成默认的 start -> end 初始节点。 */
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
