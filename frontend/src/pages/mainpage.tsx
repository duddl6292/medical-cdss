import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboard, type DashboardResponse } from "../api/dashboard";
import AppLayout from "../layouts/applayout";

const statusLabel = { waiting: "대기", processing: "분석 중", completed: "완료", failed: "실패" } as const;

export default function MainPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const refresh = () => getDashboard()
      .then((response) => { if (active) { setData(response); setError(""); } })
      .catch((requestError) => { if (active) setError(requestError instanceof Error ? requestError.message : "대시보드를 불러오지 못했습니다."); });
    void refresh();
    const timer = window.setInterval(refresh, 5_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const summary = data?.summary;
  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl">
        <section className="rounded-3xl bg-gradient-to-r from-blue-700 to-blue-500 p-8 text-white shadow-lg">
          <p className="text-sm font-bold text-blue-100">AI BRAIN CT ANALYSIS</p>
          <h1 className="mt-3 text-3xl font-bold">분석 현황 대시보드</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-blue-50">비식별 NIfTI 영상의 분석 상태를 실시간으로 확인하고, 완료 결과를 의료진이 검토합니다.</p>
          <Link to="/upload" className="mt-6 inline-flex rounded-xl bg-white px-5 py-3 text-sm font-bold text-blue-700">새 CT 분석</Link>
        </section>
        {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
        <section className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[["전체", summary?.total ?? 0], ["완료", summary?.completed ?? 0], ["진행 중", (summary?.waiting ?? 0) + (summary?.processing ?? 0)], ["실패", summary?.failed ?? 0]].map(([label, value]) => (
            <article key={label} className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">
              <p className="text-sm font-semibold text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
            </article>
          ))}
        </section>
        <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b p-5">
            <div><h2 className="font-bold text-slate-900">최근 분석</h2><p className="mt-1 text-xs text-slate-500">5초마다 자동 갱신됩니다.</p></div>
            <Link to="/history" className="text-sm font-bold text-blue-600">전체 기록</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Case</th><th className="p-4">비식별 대상 ID</th><th className="p-4">상태</th><th className="p-4">진행률</th><th className="p-4">생성 시각</th><th className="p-4">작업</th></tr></thead>
              <tbody>{(data?.recent ?? []).map((item) => (
                <tr key={item.case_id} className="border-t">
                  <td className="p-4 font-bold">#{item.case_id}</td><td className="p-4">{item.subject_id}</td>
                  <td className="p-4">{statusLabel[item.status]}</td><td className="p-4">{item.progress}%</td>
                  <td className="p-4">{new Date(item.created_at).toLocaleString("ko-KR")}</td>
                  <td className="p-4"><Link className="font-bold text-blue-600" to={item.status === "completed" ? `/result/${item.case_id}` : `/progress/${item.case_id}`}>확인</Link></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          {!data?.recent.length && <p className="p-8 text-center text-sm text-slate-500">분석 기록이 없습니다.</p>}
        </section>
      </div>
    </AppLayout>
  );
}
