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
