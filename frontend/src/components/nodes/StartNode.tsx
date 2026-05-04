import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { type EditorNodeData } from "../../transformer";

export default function StartNode({ data }: NodeProps<Node<EditorNodeData>>) {
  return (
    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500 text-white font-semibold shadow-md">
      <Handle type="source" position={Position.Right} />
      {data.label}
    </div>
  );
}
