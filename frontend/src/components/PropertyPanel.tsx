import { useState, useEffect } from "react";
import { type Node } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

interface PropertyPanelProps {
  node: Node<EditorNodeData> | null;
  onUpdateNode: (node: Node<EditorNodeData>) => void;
  onDeleteNode: (nodeId: string) => void;
  onClose: () => void;
}

export default function PropertyPanel({ node, onUpdateNode, onDeleteNode, onClose }: PropertyPanelProps) {
  const [label, setLabel] = useState("");
  const [assignee, setAssignee] = useState("");

  useEffect(() => {
    if (node) {
      setLabel(node.data.label);
      setAssignee(node.data.assignee || "");
    }
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onUpdateNode({
      ...node,
      data: { ...node.data, label, assignee: node.data.nodeType === "user_task" ? assignee : undefined },
    });
  };

  return (
    <div className="w-64 bg-white border-l border-gray-200 p-4 h-full overflow-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">节点属性</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ×
        </button>
      </div>

      <div className="text-xs text-gray-400 mb-3">ID: {node.id}</div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm text-gray-600 mb-1">名称</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
          />
        </div>

        {node.data.nodeType === "user_task" && (
          <div>
            <label className="block text-sm text-gray-600 mb-1">处理人</label>
            <input
              type="text"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              placeholder="例如: manager"
            />
          </div>
        )}

        <button
          onClick={handleSave}
          className="w-full px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          应用
        </button>

        {node.data.nodeType !== "start" && node.data.nodeType !== "end" && (
          <button
            onClick={() => onDeleteNode(node.id)}
            className="w-full px-3 py-1.5 bg-red-500 text-white rounded text-sm hover:bg-red-600"
          >
            删除节点
          </button>
        )}
      </div>
    </div>
  );
}
