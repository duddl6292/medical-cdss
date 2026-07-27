import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppLayout from "../layouts/applayout";
import ProgressBar from "../components/progressbar";
import StatusBadge from "../components/statusbadge";
import StepList from "../components/steplist";
import {
  startAnalysis,
  type AnalysisStatus,
} from "../api/analysis";
import { getAnalysisStatus } from "../api/status";

function ProgressPage() {
  const params = useParams();

  const ctId = params.ctId ?? params.ct_id ?? "";
  const caseId = Number(ctId);
  const isValidCaseId =
    Number.isInteger(caseId) && caseId > 0;

  const [progress, setProgress] = useState(0);
  const [status, setStatus] =
    useState<AnalysisStatus>(
      isValidCaseId ? "waiting" : "failed",
    );
  const [errorMessage, setErrorMessage] =
    useState<string | null>(
      isValidCaseId ? null : "유효하지 않은 CT ID입니다.",
    );

  const applyStatus = useCallback(
    (next: {
      progress: number;
      status: AnalysisStatus;
      error_message?: string | null;
    }) => {
      setProgress(next.progress);
      setStatus(next.status);
      setErrorMessage(next.error_message ?? null);
    },
    [],
  );

  const handleRefresh = useCallback(async () => {
    if (!isValidCaseId) {
      setStatus("failed");
      setErrorMessage("유효하지 않은 CT ID입니다.");
      return;
    }

    try {
      applyStatus(await getAnalysisStatus(caseId));
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "분석 상태 조회에 실패했습니다.",
      );
    }
  }, [applyStatus, caseId, isValidCaseId]);

  useEffect(() => {
    if (!isValidCaseId) {
      return;
    }

    let active = true;

    startAnalysis(caseId)
      .then((response) => {
        if (active) {
          applyStatus(response);
        }
      })
      .catch(() => {
        if (active) {
          void handleRefresh();
        }
      });

    const timer = window.setInterval(() => {
      void handleRefresh();
    }, 3000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [applyStatus, caseId, handleRefresh, isValidCaseId]);

  const isCompleted = progress >= 100;
  const isFailed = status === "failed";

  return (
    <AppLayout>
      <div className="mx-auto max-w-6xl">
        {/* 페이지 제목 */}
        <section className="mb-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                AI CT 분석 진행
              </h1>

              <p className="mt-2 text-slate-500">
                업로드한 뇌 CT 영상의 분석 진행 상태를 확인합니다.
              </p>
            </div>

            <StatusBadge status={status} />
          </div>
        </section>


        {/* 전체 분석 흐름 */}
        <section className="mb-6 rounded-2xl border border-slate-200 bg-white px-8 py-5 shadow-sm">
          <div className="grid grid-cols-3 items-start">
            <AnalysisFlowStep
              number="✓"
              label="CT 업로드"
              state="completed"
            />

            <AnalysisFlowStep
              number="2"
              label="분석 진행"
              state="active"
            />

            <AnalysisFlowStep
              number="3"
              label="결과 확인"
              state="waiting"
            />
          </div>
        </section>


        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* 왼쪽 분석 진행 영역 */}
          <section className="space-y-6 lg:col-span-2">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-slate-800">
                  분석 진행률
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  AI 모델이 CT 영상을 분석하고 있습니다.
                </p>
              </div>

              <ProgressBar progress={progress} />

              <div className="mt-5 rounded-xl bg-blue-50 px-4 py-3">
                <p className="text-sm font-medium text-blue-800">
                  {isCompleted
                    ? "분석이 완료되었습니다. 결과 페이지에서 분석 결과를 확인하세요."
                    : isFailed
                      ? errorMessage ??
                        "분석 중 오류가 발생했습니다."
                      : "현재 AI 모델이 뇌 CT 영상의 병변 영역을 분석하고 있습니다."}
                </p>
              </div>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-5">
                <h2 className="text-lg font-semibold text-slate-800">
                  분석 단계
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  영상 업로드부터 결과 생성까지의 처리 단계입니다.
                </p>
              </div>

              <StepList progress={progress} status={status} />
            </article>
          </section>

          {/* 오른쪽 분석 정보 영역 */}
          <aside className="space-y-6">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-800">
                분석 정보
              </h2>

              <dl className="mt-5 divide-y divide-slate-200">
                <InfoRow label="CT ID" value={ctId} />
                <InfoRow label="환자 ID" value="P001" />
                <InfoRow
                  label="분석 상태"
                  value={isCompleted ? "분석 완료" : "분석 중"}
                />
                <InfoRow label="시작 시간" value="2026-07-26 00:15" />
                <InfoRow label="경과 시간" value="00:42" />
                <InfoRow
                  label="예상 남은 시간"
                  value={isCompleted ? "완료" : "약 15초"}
                />
              </dl>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="font-semibold text-slate-800">
                작업 관리
              </h2>

              <div className="mt-4 space-y-3">
                {!isCompleted && (
                  <button
                    type="button"
                    onClick={handleRefresh}
                    className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                  >
                    진행 상태 새로고침
                  </button>
                )}

                {isCompleted && (
                  <Link
                    to={`/result/${ctId}`}
                    className="block w-full rounded-lg bg-emerald-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-emerald-700"
                  >
                    분석 결과 보기
                  </Link>
                )}

                <Link
                  to="/history"
                  className="block w-full rounded-lg border border-slate-300 px-4 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  분석 기록으로 이동
                </Link>
              </div>
            </article>

            <article className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <p className="text-sm font-semibold text-amber-800">
                분석 안내
              </p>

              <p className="mt-2 text-sm leading-6 text-amber-700">
                분석이 완료되면 결과 페이지에서 원본 영상과 AI 분석
                결과를 확인할 수 있습니다.
              </p>
            </article>
          </aside>
        </div>
      </div>
    </AppLayout>
  );
}

type InfoRowProps = {
  label: string;
  value: string;
};

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0">
      <dt className="text-sm text-slate-500">
        {label}
      </dt>

      <dd className="break-all text-right text-sm font-semibold text-slate-800">
        {value}
      </dd>
    </div>
  );
}

type AnalysisFlowStepProps = {
  number: string;
  label: string;
  state: "completed" | "active" | "waiting";
};

function AnalysisFlowStep({
  number,
  label,
  state,
}: AnalysisFlowStepProps) {
  const circleClass =
    state === "active"
      ? "bg-blue-600 text-white"
      : state === "completed"
        ? "bg-emerald-100 text-emerald-700"
        : "bg-slate-200 text-slate-500";

  const labelClass =
    state === "active"
      ? "text-blue-600"
      : state === "completed"
        ? "text-emerald-700"
        : "text-slate-500";

  return (
    <div className="flex flex-col items-center text-center">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold ${circleClass}`}
      >
        {number}
      </div>

      <span className={`mt-2 text-sm font-semibold ${labelClass}`}>
        {label}
      </span>
    </div>
  );
}


export default ProgressPage;
