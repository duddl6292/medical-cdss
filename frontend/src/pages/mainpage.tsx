import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { getDashboard, type DashboardItem, type DashboardResponse } from "../api/dashboard";
import AppLayout from "../layouts/applayout";

type SummaryType = "total" | "completed" | "processing" | "failed";

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
  const total = summary?.total ?? 0;
  const items: Array<{ title: string; value: number; description: string; percentage?: string; type: SummaryType }> = [
    { title: "전체 분석", value: total, description: "등록된 전체 분석 건수", type: "total" },
    { title: "분석 완료", value: summary?.completed ?? 0, description: "분석이 완료된 작업", percentage: percent(summary?.completed, total), type: "completed" },
    { title: "분석 진행 중", value: (summary?.processing ?? 0) + (summary?.waiting ?? 0), description: "현재 처리 중인 작업", percentage: percent((summary?.processing ?? 0) + (summary?.waiting ?? 0), total), type: "processing" },
    { title: "분석 실패", value: summary?.failed ?? 0, description: "확인이 필요한 작업", percentage: percent(summary?.failed, total), type: "failed" },
  ];

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-[1500px]">
        <section className="mb-5 overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-r from-white via-[#f8fbff] to-[#eaf4ff] shadow-sm">
          <div className="relative flex min-h-[205px] items-center overflow-hidden px-7 py-7 sm:px-10 lg:px-12">
            <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-blue-200/30 blur-3xl" />
            <div className="relative max-w-2xl">
              <span className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-white px-3 py-1.5 text-xs font-bold text-blue-600 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-blue-500" />AI Brain CT Analysis
              </span>
              <h1 className="mt-4 text-2xl font-bold tracking-tight text-[#102a5c] sm:text-3xl">AI 기반 뇌 CT 영상 분석 지원 시스템</h1>
              <p className="mt-3 max-w-xl text-sm leading-7 text-slate-600">정량적이고 신뢰할 수 있는 AI 분석으로 의료진의 신속하고 정확한 임상 의사결정을 지원합니다.</p>
              <Link to="/upload" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-md shadow-blue-200 transition hover:bg-blue-700">
                <UploadIcon />CT 분석 시작<span aria-hidden="true">›</span>
              </Link>
            </div>
          </div>
        </section>

        {error && <p className="mb-5 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}

        <section className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {items.map((item) => <SummaryCard key={item.title} {...item} />)}
        </section>

        <section className="grid grid-cols-1 items-stretch gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
          <article className="flex min-w-0 flex-col overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <div><h2 className="text-lg font-bold text-slate-900">최근 분석 이력</h2><p className="mt-1 text-sm text-slate-500">최근 등록된 CT 분석 작업을 확인합니다. · 5초 자동 갱신</p></div>
              <Link to="/history" className="shrink-0 rounded-lg border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100">전체 보기</Link>
            </div>
            <div className="min-w-0 flex-1 overflow-x-auto">
              <table className="w-full min-w-[760px] table-fixed text-left">
                <colgroup><col className="w-[14%]" /><col className="w-[20%]" /><col className="w-[13%]" /><col className="w-[22%]" /><col className="w-[19%]" /><col className="w-[12%]" /></colgroup>
                <thead className="bg-[#f8fbff] text-sm text-slate-500">
                  <tr><th className="px-5 py-4 font-semibold">CT ID</th><th className="px-3 py-4 font-semibold">비식별 대상 ID</th><th className="px-3 py-4 font-semibold">상태</th><th className="px-3 py-4 font-semibold">진행률</th><th className="px-3 py-4 font-semibold">등록일</th><th className="px-3 py-4 text-center font-semibold">결과</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(data?.recent ?? []).map((analysis) => <RecentRow key={analysis.case_id} item={analysis} />)}
                </tbody>
              </table>
              {!data?.recent.length && <p className="p-10 text-center text-sm text-slate-500">등록된 분석 작업이 없습니다.</p>}
            </div>
            <div className="mt-auto flex justify-center gap-2 border-t border-slate-100 px-6 py-4">
              <span className="flex h-9 min-w-9 items-center justify-center rounded-lg bg-blue-600 px-3 text-sm font-semibold text-white">1</span>
            </div>
          </article>

          <aside className="flex h-full flex-col rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
            <div><h2 className="text-lg font-bold text-slate-900">분석 프로세스</h2><p className="mt-1 text-sm text-slate-500">CT 분석은 세 단계로 진행됩니다.</p></div>
            <div className="relative mt-6 flex flex-1 flex-col justify-between gap-4">
              <div className="absolute bottom-[56px] left-[18px] top-[56px] border-l border-dashed border-blue-200" />
              <ProcessStep number="1" title="CT 업로드" description="비식별 NIfTI 형식의 뇌 CT 영상을 등록합니다." icon={<UploadIcon />} />
              <ProcessStep number="2" title="AI 분석" description="GPU 추론 서버가 병변 영역을 탐지하고 정량화합니다." icon={<BrainIcon />} />
              <ProcessStep number="3" title="결과 확인" description="분할 영상과 정량 결과를 의료진이 검토합니다." icon={<ChartIcon />} />
            </div>
            <div className="mt-5 flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-3 text-xs font-semibold text-blue-700">
              <ClockIcon />GPU 콜드 스타트 시 추가 시간이 발생할 수 있습니다.
            </div>
          </aside>
        </section>
      </div>
    </AppLayout>
  );
}

function RecentRow({ item }: { item: DashboardItem }) {
  const completed = item.status === "completed";
  return (
    <tr className="text-sm text-slate-700 transition hover:bg-blue-50/40">
      <td className="px-5 py-5 font-bold text-slate-900">#{item.case_id}</td>
      <td className="break-words px-3 py-5 font-medium">{item.subject_id}</td>
      <td className="px-3 py-5"><StatusBadge status={item.status} /></td>
      <td className="px-3 py-5"><div className="flex items-center gap-2"><div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-200"><div className={`h-full rounded-full ${progressColor(item.status)}`} style={{ width: `${item.progress}%` }} /></div><span className="w-9 text-right text-xs font-semibold text-slate-500">{item.progress}%</span></div></td>
      <td className="px-3 py-5 text-slate-600">{new Date(item.created_at).toLocaleString("ko-KR", { dateStyle: "short", timeStyle: "short" })}</td>
      <td className="px-3 py-5 text-center"><Link to={completed ? `/result/${item.case_id}` : `/progress/${item.case_id}`} className="inline-flex rounded-lg border border-blue-100 bg-white px-3 py-2 text-xs font-bold text-blue-700 hover:bg-blue-50">{completed ? "보기" : "진행"}</Link></td>
    </tr>
  );
}

function SummaryCard({ title, value, description, percentage, type }: { title: string; value: number; description: string; percentage?: string; type: SummaryType }) {
  const styles: Record<SummaryType, { bg: string; color: string; icon: string }> = {
    total: { bg: "bg-blue-50", color: "text-blue-600", icon: "▦" },
    completed: { bg: "bg-emerald-50", color: "text-emerald-600", icon: "✓" },
    processing: { bg: "bg-amber-50", color: "text-amber-500", icon: "◔" },
    failed: { bg: "bg-red-50", color: "text-red-500", icon: "!" },
  };
  const style = styles[type];
  return <article className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-center gap-4"><div className={`flex h-14 w-14 items-center justify-center rounded-full text-2xl font-bold ${style.bg} ${style.color}`}>{style.icon}</div><div className="min-w-0 flex-1"><p className="text-sm font-bold text-slate-700">{title}</p><div className="mt-1 flex items-end justify-between"><p className="text-3xl font-bold text-slate-900">{value}</p>{percentage && <span className={`pb-1 text-sm font-bold ${style.color}`}>{percentage}</span>}</div></div></div><p className="mt-4 text-xs text-slate-400">{description}</p></article>;
}

function StatusBadge({ status }: { status: DashboardItem["status"] }) {
  const map = { waiting: ["대기", "bg-amber-100 text-amber-700"], processing: ["분석 중", "bg-blue-100 text-blue-700"], completed: ["완료", "bg-emerald-100 text-emerald-700"], failed: ["실패", "bg-red-100 text-red-700"] } as const;
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${map[status][1]}`}>{map[status][0]}</span>;
}
function progressColor(status: DashboardItem["status"]) { return { waiting: "bg-amber-400", processing: "bg-blue-600", completed: "bg-emerald-500", failed: "bg-red-500" }[status]; }
function percent(value = 0, total = 0) { return total ? `${((value / total) * 100).toFixed(1)}%` : "0%"; }

function ProcessStep({ number, title, description, icon }: { number: string; title: string; description: string; icon: ReactNode }) {
  return <div className="relative flex items-center gap-3"><div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white shadow-sm shadow-blue-200">{number}</div><div className="flex min-h-[108px] min-w-0 flex-1 items-center gap-3 rounded-xl border border-blue-100 bg-[#fbfdff] p-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">{icon}</div><div><h3 className="text-sm font-bold text-slate-800">{title}</h3><p className="mt-1 text-xs leading-5 text-slate-500">{description}</p></div></div></div>;
}
function UploadIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="M12 16V4m0 0L7 9m5-5 5 5M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>; }
function BrainIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="M9.5 4.5A3 3 0 0 0 5 7v.5A3.5 3.5 0 0 0 4 14a3.5 3.5 0 0 0 5.5 4.5v-14Zm5 0A3 3 0 0 1 19 7v.5a3.5 3.5 0 0 1 1 6.5 3.5 3.5 0 0 1-5.5 4.5v-14Z" stroke="currentColor" strokeWidth="1.7" /></svg>; }
function ChartIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="M4 20V4m0 16h16m-13-4 4-5 3 3 5-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>; }
function ClockIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 shrink-0"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" /><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>; }
