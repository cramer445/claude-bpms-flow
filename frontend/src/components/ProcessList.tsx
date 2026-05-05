import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProcesses } from "../api";
import type { ProcessSummary } from "../types";
import ProcessCard from "./ProcessCard";

export default function ProcessList() {
  const [processes, setProcesses] = useState<ProcessSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadProcesses = async () => {
    setLoading(true);
    try {
      const data = await listProcesses();
      setProcesses(data);
    } catch (e) {
      alert(`加载失败: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProcesses();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">BPMS 流程编辑器</h1>
        <Link
          to="/editor/new"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          新建流程
        </Link>
      </header>

      <main className="max-w-3xl mx-auto p-6">
        {loading ? (
          <p className="text-gray-500">加载中...</p>
        ) : processes.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">暂无流程定义</p>
            <Link
              to="/editor/new"
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              创建第一个流程
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {processes.map((p) => (
              <ProcessCard key={p.id} process={p} onDeleted={loadProcesses} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
