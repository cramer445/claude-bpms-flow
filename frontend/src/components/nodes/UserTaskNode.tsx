import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { type EditorNodeData } from "../../transformer";

export default function UserTaskNode({ data, selected }: NodeProps<Node<EditorNodeData>>) {
  return (
    <div
      className={`rounded-lg border-2 px-4 py-3 min-w-[160px] bg-white shadow-md ${
        selected ? "border-blue-500" : "border-gray-300"
      }`}
    >
      <Handle type="target" position={Position.Left} />
      <div className="font-semibold text-sm">{data.label}</div>
      {data.assignee && <div className="text-xs text-gray-500 mt-1">处理人: {data.assignee}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
