import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { downloadResultFile } from "../api/download";
import {
  getAnalysisResult,
  type ResultResponse,
} from "../api/result";
import NiivueViewer, {
  type ViewerMode,
} from "../components/niivueviewer";
import AppLayout from "../layouts/applayout";

function ResultPage() {
  const { ctId } = useParams();
  const caseId = Number(ctId);
  const isValidCaseId =
    Number.isInteger(caseId) && caseId > 0;

  const [result, setResult] =
    useState<ResultResponse | null>(null);
  const [error, setError] = useState<string | null>(
    isValidCaseId ? null : "올바르지 않은 CT ID입니다.",
  );
  const [loading, setLoading] = useState(isValidCaseId);
  const [downloading, setDownloading] = useState(false);
  const [viewerMode, setViewerMode] =
    useState<ViewerMode>("axial");
  const [overlayVisible, setOverlayVisible] =
    useState(true);
  const [overlayOpacity, setOverlayOpacity] =
    useState(0.6);

  useEffect(() => {
    if (!isValidCaseId) {
      return;
    }

    let active = true;

    getAnalysisResult(caseId)
      .then((response) => {
        if (active) {
          if (response.status !== "completed") {
            setError("분석이 아직 완료되지 않았습니다.");
          } else {
            setResult(response);
            setError(null);
          }
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "분석 결과를 불러오지 못했습니다.",
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [caseId, isValidCaseId]);

  async function handleDownload() {
    if (!result) {
      return;
    }

    setDownloading(true);
    setError(null);
    try {
      await downloadResultFile(result.case_id, "mask");
    } catch (downloadError) {
      setError(
        downloadError instanceof Error
          ? downloadError.message
          : "결과 파일을 다운로드하지 못했습니다.",
      );
    } finally {
      setDownloading(false);
    }
  }

  return (
    <AppLayout>
      <main className="mx-auto w-full max-w-[1500px]">
        <section className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                AI 분석 결과
              </h1>
              {result && (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                  완료
                </span>
              )}
            </div>
            <p className="mt-2 text-sm text-slate-500">
              CT ID: {ctId ?? "-"}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              to="/history"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              분석 기록
            </Link>
            <Link
              to="/upload"
              className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              새 CT 분석
            </Link>
          </div>
        </section>

        <section className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
          본 결과는 교육·연구 목적의 비임상 시연용이며 의료진의
          진단을 대체하지 않습니다.
        </section>

        {loading && (
          <Notice message="분석 결과를 불러오는 중입니다." />
        )}

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
            {error}
          </div>
        )}

        {result &&
          result.original_nifti_url &&
          result.mask_nifti_url && (
            <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
              <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-col gap-4 px-6 pt-5 lg:flex-row lg:items-center lg:justify-between">
                  <h2 className="text-lg font-bold text-slate-900">
                    CT Viewer
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {(
                      [
                        ["axial", "Axial"],
                        ["coronal", "Coronal"],
                        ["sagittal", "Sagittal"],
                        ["multiplanar", "Multi View"],
                      ] as const
                    ).map(([mode, label]) => (
                      <ViewerModeButton
                        key={mode}
                        label={label}
                        active={viewerMode === mode}
                        onClick={() => setViewerMode(mode)}
                      />
                    ))}
                  </div>
                </div>

                <div className="px-6 pb-5 pt-3">
                  <NiivueViewer
                    originalUrl={result.original_nifti_url}
                    maskUrl={result.mask_nifti_url}
                    overlayOpacity={overlayOpacity}
                    overlayVisible={overlayVisible}
                    viewerMode={viewerMode}
                    onOverlayOpacityChange={setOverlayOpacity}
                    onOverlayVisibleChange={setOverlayVisible}
                  />
                </div>
              </section>

              <aside className="space-y-5">
                <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-900">
                    분석 정보
                  </h2>
                  <dl className="mt-4 divide-y divide-slate-200">
                    <ResultRow
                      label="병변 부피"
                      value={`${result.lesion_volume_ml ?? 0} mL`}
                    />
                    <ResultRow
                      label="병변 슬라이스"
                      value={`${result.lesion_slice_count}개`}
                    />
                    <ResultRow
                      label="최대 병변 슬라이스"
                      value={
                        result.max_lesion_slice?.toString() ??
                        "-"
                      }
                    />
                    <ResultRow
                      label="추론 시간"
                      value={`${result.inference_time_seconds.toFixed(2)}초`}
                    />
                    <ResultRow
                      label="모델 버전"
                      value={result.model_version ?? "-"}
                    />
                  </dl>

                  <button
                    type="button"
                    disabled={downloading}
                    onClick={() => void handleDownload()}
                    className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {downloading
                      ? "다운로드 중..."
                      : "분할 마스크 다운로드"}
                  </button>
                </section>

                {result.message && (
                  <section className="rounded-2xl border border-violet-200 bg-violet-50 p-6">
                    <h2 className="font-bold text-indigo-900">
                      AI 안내
                    </h2>
                    <p className="mt-3 text-sm leading-7 text-slate-700">
                      {result.message}
                    </p>
                  </section>
                )}
              </aside>
            </div>
          )}
      </main>
    </AppLayout>
  );
}

function Notice({ message }: { message: string }) {
  return (
    <div className="mb-5 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 text-sm font-medium text-blue-700">
      {message}
    </div>
  );
}

function ResultRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0">
      <dt className="text-sm font-medium text-slate-600">
        {label}
      </dt>
      <dd className="text-sm font-bold text-slate-900">
        {value}
      </dd>
    </div>
  );
}

function ViewerModeButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border px-3 py-2 text-xs font-semibold transition ${
        active
          ? "border-blue-600 bg-blue-600 text-white"
          : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
      }`}
    >
      {label}
    </button>
  );
}

export default ResultPage;
