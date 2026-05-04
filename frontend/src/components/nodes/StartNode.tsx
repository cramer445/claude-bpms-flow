import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { type EditorNodeData } from "../../transformer";

export default function StartNode({ data }: NodeProps<Node<EditorNodeData>>) {
  const nd = data as EditorNodeData;
  return (
    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500 text-white font-semibold shadow-md">
      <Handle type="source" position={Position.Right} />
      {nd.label}
    </div>
  );
}
