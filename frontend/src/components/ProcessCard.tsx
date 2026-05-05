import { useState } from "react";
import { Link } from "react-router-dom";
import { deleteProcess } from "../api";
import type { ProcessSummary } from "../types";

interface ProcessCardProps {
  process: ProcessSummary;
  onDeleted: () => void;
}

export default function ProcessCard({ process, onDeleted }: ProcessCardProps) {
  const [confirming, setConfirming] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteProcess(process.id);
      onDeleted();
    } catch (e) {
      alert(`删除失败: ${e}`);
    }
  };

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm border border-gray-200">
      <Link to={`/editor/${process.id}`} className="flex-1">
        <div className="font-semibold">{process.name}</div>
        <div className="text-sm text-gray-500">{process.id} · v{process.version}</div>
      </Link>
      {confirming ? (
        <div className="flex gap-2 ml-4">
          <button onClick={handleDelete} className="px-3 py-1 text-sm bg-red-500 text-white rounded">
            确认
          </button>
          <button onClick={() => setConfirming(false)} className="px-3 py-1 text-sm border rounded">
            取消
          </button>
        </div>
      ) : (
        <button
          onClick={() => setConfirming(true)}
          className="ml-4 px-3 py-1 text-sm text-red-500 border border-red-300 rounded hover:bg-red-50"
        >
          删除
        </button>
      )}
    </div>
  );
}
