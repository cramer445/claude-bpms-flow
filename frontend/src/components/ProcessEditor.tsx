import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { type Node, type Edge } from "@xyflow/react";
import { getProcess, createProcess, updateProcess } from "../api";
import type { ProcessDefinition, SaveProcessPayload } from "../types";
import { toFlowNodesAndEdges, toPayload, defaultInitialNodes, type EditorNodeData } from "../transformer";
import FlowCanvas, { type FlowCanvasRef } from "./FlowCanvas";
import NodeToolbar from "./NodeToolbar";
import PropertyPanel from "./PropertyPanel";

export default function ProcessEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNew = id === "new";
  const canvasRef = useRef<FlowCanvasRef>(null);

  const [initialNodes, setInitialNodes] = useState<Node<EditorNodeData>[]>([]);
  const [initialEdges, setInitialEdges] = useState<Edge[]>([]);
  const [processName, setProcessName] = useState("");
  const [processId, setProcessId] = useState("");
  const [selectedNode, setSelectedNode] = useState<Node<EditorNodeData> | null>(null);
  const [startNodeId] = useState("start");

  // 加载已有流程
  useEffect(() => {
    if (!isNew && id) {
      getProcess(id).then((pd: ProcessDefinition) => {
        setProcessName(pd.name);
        setProcessId(pd.id);
        const { nodes: n, edges: e } = toFlowNodesAndEdges(pd);
        setInitialNodes(n);
        setInitialEdges(e);
      }).catch((e: Error) => {
        alert(`加载失败: ${e.message}`);
        navigate("/");
      });
    } else {
      const def = defaultInitialNodes();
      setInitialNodes(def.nodes);
      setInitialEdges(def.edges);
      setProcessName("新流程");
    }
  }, [id, isNew, navigate]);

  // 保存
  const handleSave = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const currentNodes = canvas.getNodes();
    const currentEdges = canvas.getEdges();
    // 过滤已删除的节点
    const nodes = currentNodes.filter((n) => !(n.data as any)._deleted);

    const name = prompt("流程名称:", processName);
    if (!name) return;

    let pid = processId;
    if (!pid) {
      pid = prompt("流程 ID（英文数字和连字符）:") || "";
      if (!pid) return;
    }

    const payload = toPayload(pid, name, "1.0", startNodeId, nodes, currentEdges);

    try {
      if (isNew) {
        await createProcess(payload);
        alert("流程已创建");
      } else {
        await updateProcess(pid, payload);
        alert("流程已更新");
      }
      navigate("/");
    } catch (e: any) {
      alert(`保存失败: ${e.message}`);
    }
  };

  const handleNodeClick = useCallback((node: Node<EditorNodeData>) => {
    setSelectedNode(node);
  }, []);

  const handleUpdateNode = useCallback((updated: Node<EditorNodeData>) => {
    // 更新 selectedNode 的引用，实际数据修改通过 canvas 内部状态
    setSelectedNode(updated);
  }, []);

  const handleDeleteNode = useCallback((nodeId: string) => {
    canvasRef.current?.deleteNode(nodeId);
    setSelectedNode(null);
  }, []);

  const handleAddNode = useCallback((node: Node<EditorNodeData>) => {
    canvasRef.current?.addNode(node);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* 顶部栏 */}
      <header className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate("/")} className="text-sm text-gray-500 hover:text-gray-700">
            ← 返回列表
          </button>
          <span className="font-semibold">{processName || "新流程"}</span>
        </div>
        <button
          onClick={handleSave}
          className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          保存
        </button>
      </header>

      {/* 主内容 */}
      <div className="flex-1 flex">
        <div className="flex-1 relative">
          <FlowCanvas
            ref={canvasRef}
            initialNodes={initialNodes}
            initialEdges={initialEdges}
            onNodeClick={handleNodeClick}
          />
          <NodeToolbar onAddNode={handleAddNode} />
        </div>
        <PropertyPanel node={selectedNode} onUpdateNode={handleUpdateNode} onDeleteNode={handleDeleteNode} onClose={() => setSelectedNode(null)} />
      </div>
    </div>
  );
}
