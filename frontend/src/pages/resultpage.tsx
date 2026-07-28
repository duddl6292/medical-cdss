import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getArtifactObjectUrl } from "../api/artifacts";
import { downloadResultFile } from "../api/download";
import { getAnalysisResult, type ResultResponse } from "../api/result";
import NiivueViewer, { type ViewerMode } from "../components/niivueviewer";
import AppLayout from "../layouts/applayout";

export default function ResultPage() {
  const caseId = Number(useParams().ctId);
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [originalUrl, setOriginalUrl] = useState("");
  const [maskUrl, setMaskUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<ViewerMode>("axial");
  const [opacity, setOpacity] = useState(0.6);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    let active = true;
    let originalObjectUrl = "";
    let maskObjectUrl = "";
    async function load() {
      try {
        if (!Number.isInteger(caseId) || caseId < 1) throw new Error("올바르지 않은 Case ID입니다.");
        const response = await getAnalysisResult(caseId);
        if (response.status !== "completed") throw new Error("아직 분석이 완료되지 않았습니다.");
        if (!response.original_nifti_url || !response.mask_nifti_url) throw new Error("뷰어용 결과 파일이 없습니다.");
        [originalObjectUrl, maskObjectUrl] = await Promise.all([
          getArtifactObjectUrl(response.original_nifti_url),
          getArtifactObjectUrl(response.mask_nifti_url),
        ]);
        if (!active) return;
        setResult(response);
        setOriginalUrl(originalObjectUrl);
        setMaskUrl(maskObjectUrl);
      } catch (requestError) {
        if (active) setError(requestError instanceof Error ? requestError.message : "결과를 불러오지 못했습니다.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
      if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
      if (maskObjectUrl) URL.revokeObjectURL(maskObjectUrl);
    };
  }, [caseId]);

  return (
    <AppLayout>
      <div className="mx-auto max-w-[1500px]">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><h1 className="text-2xl font-bold text-slate-900">AI 분석 결과</h1><p className="mt-2 text-sm text-slate-500">Case #{caseId} · {result?.subject_id ?? "-"}</p></div>
          <div className="flex gap-2"><Link to="/history" className="rounded-xl border bg-white px-4 py-3 text-sm font-bold">분석 기록</Link><Link to="/upload" className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white">새 분석</Link></div>
        </div>
        <p className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">교육·연구용 비임상 결과이며 진단을 대체하지 않습니다. 의료진 검토 전 확정된 판단으로 사용하지 마세요.</p>
        {loading && <p className="mt-5 rounded-xl bg-blue-50 p-4 text-blue-700">결과 파일을 안전하게 불러오는 중입니다.</p>}
        {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
        {result && originalUrl && maskUrl && (
          <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="rounded-2xl border bg-white p-5 shadow-sm">
              <div className="mb-4 flex flex-wrap gap-2">{(["axial", "coronal", "sagittal", "multiplanar"] as ViewerMode[]).map((item) => (
                <button key={item} onClick={() => setMode(item)} className={`rounded-lg px-3 py-2 text-sm font-bold ${mode === item ? "bg-blue-600 text-white" : "bg-slate-100"}`}>{item}</button>
              ))}</div>
              <NiivueViewer originalUrl={originalUrl} maskUrl={maskUrl} viewerMode={mode} overlayOpacity={opacity} overlayVisible={visible}
                onOverlayOpacityChange={setOpacity} onOverlayVisibleChange={setVisible} />
            </section>
            <aside className="space-y-5">
              <section className="rounded-2xl border bg-white p-6 shadow-sm">
                <h2 className="font-bold text-slate-900">분석 정보</h2>
                <dl className="mt-4 space-y-3 text-sm">
                  <Info label="병변 부피" value={`${result.lesion_volume_ml ?? 0} mL`} />
                  <Info label="병변 슬라이스" value={`${result.lesion_slice_count}개`} />
                  <Info label="최대 병변 슬라이스" value={formatViewerSlice(result.max_lesion_slice)} />
                  <Info label="추론 시간" value={`${result.inference_time_seconds.toFixed(2)}초`} />
                  <Info label="모델 버전" value={result.model_version ?? "-"} />
                </dl>
                <button onClick={() => void downloadResultFile(result.case_id, "mask")} className="mt-5 w-full rounded-xl bg-blue-600 p-3 text-sm font-bold text-white">분할 마스크 다운로드</button>
              </section>
              <section className="rounded-2xl border bg-white p-6 shadow-sm">
                <h2 className="font-bold">AI 분석 요약</h2>
                <p className="mt-4 text-sm leading-7 text-slate-600">
                  병변은 {formatViewerSlice(result.lesion_slice_start)}번부터{" "}
                  {formatViewerSlice(result.lesion_slice_end)}번 슬라이스 범위 내 총{" "}
                  {result.lesion_slice_count}개 슬라이스에서 관찰됩니다.
                  가장 큰 병변 면적을 갖는 슬라이스는{" "}
                  {formatViewerSlice(result.max_lesion_slice)}번이며, 총 병변 부피는{" "}
                  {(result.lesion_volume_ml ?? 0).toFixed(2)}mL입니다.
                </p>
              </section>
            </aside>
          </div>
        )}
      </div>
    </AppLayout>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3 border-b pb-3"><dt className="text-slate-500">{label}</dt><dd className="font-bold">{value}</dd></div>;
}

function formatViewerSlice(value: number | null) {
  return value === null ? "-" : String(value + 1);
}
