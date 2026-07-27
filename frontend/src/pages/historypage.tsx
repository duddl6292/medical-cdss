import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getAnalysisHistory, type HistoryItem } from "../api/history";
import AppLayout from "../layouts/applayout";

const statusLabel = { waiting: "대기", processing: "분석 중", completed: "완료", failed: "실패" } as const;

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const response = await getAnalysisHistory({ q: query || undefined, status: status || undefined });
      setItems(response.results);
      setError("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 기록을 불러오지 못했습니다.");
    }
  }, [query, status]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(refresh, 5_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><h1 className="text-2xl font-bold text-slate-900">분석 기록</h1><p className="mt-2 text-sm text-slate-500">비식별 대상 ID와 상태로 검색할 수 있습니다.</p></div>
          <Link to="/upload" className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white">새 분석</Link>
        </div>
        <div className="mt-6 flex flex-wrap gap-3 rounded-2xl border bg-white p-4">
          <input aria-label="검색" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Case 번호 또는 비식별 ID"
            className="h-11 min-w-64 flex-1 rounded-xl border border-slate-300 px-4" />
          <select aria-label="상태" value={status} onChange={(e) => setStatus(e.target.value)} className="h-11 rounded-xl border border-slate-300 px-4">
            <option value="">전체 상태</option><option value="waiting">대기</option><option value="processing">분석 중</option><option value="completed">완료</option><option value="failed">실패</option>
          </select>
          <button onClick={() => void refresh()} className="rounded-xl border px-4 text-sm font-bold">새로고침</button>
        </div>
        {error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
        <section className="mt-4 overflow-x-auto rounded-2xl border bg-white shadow-sm">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Case</th><th className="p-4">비식별 대상 ID</th><th className="p-4">상태</th><th className="p-4">진행률</th><th className="p-4">검토</th><th className="p-4">등록 시각</th><th className="p-4">작업</th></tr></thead>
            <tbody>{items.map((item) => (
              <tr key={item.case_id} className="border-t">
                <td className="p-4 font-bold">#{item.case_id}</td><td className="p-4">{item.subject_id}</td>
                <td className="p-4">{statusLabel[item.status]}</td><td className="p-4">{item.progress}%</td>
                <td className="p-4">{item.review_status === "reviewed" ? "검토 완료" : "미검토"}</td>
                <td className="p-4">{new Date(item.created_at).toLocaleString("ko-KR")}</td>
                <td className="p-4"><Link className="font-bold text-blue-600" to={item.status === "completed" ? `/result/${item.case_id}` : `/progress/${item.case_id}`}>상세</Link></td>
              </tr>
            ))}</tbody>
          </table>
          {!items.length && <p className="p-10 text-center text-slate-500">조건에 맞는 분석 기록이 없습니다.</p>}
        </section>
      </div>
    </AppLayout>
  );
}
