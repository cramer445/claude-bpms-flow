import { useCallback } from "react";
import { type Node, Panel, useReactFlow } from "@xyflow/react";
import { type EditorNodeData } from "../transformer";

interface NodeToolbarProps {
  onAddNode: (node: Node<EditorNodeData>) => void;
}

let newNodeId = 1;

export default function NodeToolbar({ onAddNode }: NodeToolbarProps) {
  const { screenToFlowPosition } = useReactFlow();

  const addUserTask = useCallback(() => {
    const position = screenToFlowPosition({ x: 300, y: 200 });
    const id = `node_${newNodeId++}`;
    onAddNode({
      id,
      type: "userTask",
      position,
      data: { label: "新任务", nodeType: "user_task", assignee: "", originalId: id },
    });
  }, [screenToFlowPosition, onAddNode]);

  return (
    <Panel position="top-left">
      <div className="flex gap-2 p-2 bg-white rounded-lg shadow-md border border-gray-200">
        <button
          onClick={addUserTask}
          className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + 任务节点
        </button>
      </div>
    </Panel>
  );
}
