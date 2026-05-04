import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  type OnConnect,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { nodeTypes } from "./nodes";
import { type EditorNodeData } from "../transformer";

export interface FlowCanvasRef {
  getNodes: () => Node<EditorNodeData>[];
  getEdges: () => Edge[];
  addNode: (node: Node<EditorNodeData>) => void;
  deleteNode: (nodeId: string) => void;
}

interface FlowCanvasProps {
  initialNodes: Node<EditorNodeData>[];
  initialEdges: Edge[];
  onNodeClick: (node: Node<EditorNodeData>) => void;
}

const FlowCanvas = forwardRef<FlowCanvasRef, FlowCanvasProps>(
  ({ initialNodes, initialEdges, onNodeClick }, ref) => {
    const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);

    useImperativeHandle(ref, () => ({
      getNodes: () => nodes,
      getEdges: () => edges,
      addNode: (node: Node<EditorNodeData>) => setNodes((nds) => [...nds, node]),
      deleteNode: (nodeId: string) => {
        setNodes((nds) => nds.filter((n) => n.id !== nodeId));
        setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      },
    }));

    const loadedId = useRef<string | null>(null);
    useEffect(() => {
      const key = initialNodes.map((n) => n.id).join(",");
      if (key && key !== loadedId.current) {
        setNodes(initialNodes);
        loadedId.current = key;
      }
    }, [initialNodes, setNodes]);

    useEffect(() => {
      const key = initialEdges.map((e) => e.id).join(",");
      if (key) {
        setEdges(initialEdges);
      }
    }, [initialEdges, setEdges]);

    const handleNodesChange: OnNodesChange<Node<EditorNodeData>> = (changes) => {
      onNodesChangeInternal(changes);
    };

    const handleEdgesChange: OnEdgesChange<Edge> = (changes) => {
      onEdgesChangeInternal(changes);
    };

    const onConnect: OnConnect = (connection) => {
      setEdges((eds) => addEdge(connection, eds));
    };

    return (
      <div style={{ width: "100%", height: "100%" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes as Record<string, any>}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => onNodeClick(node as Node<EditorNodeData>)}
          fitView
          deleteKeyCode="Backspace"
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    );
  },
);

export default FlowCanvas;
