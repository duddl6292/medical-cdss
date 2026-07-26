import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import AppLayout from "../layouts/applayout";

type AnalysisStatus =
  | "완료"
  | "분석 중"
  | "대기"
  | "실패";

type RecentAnalysis = {
  ctId: string;
  patientId: string;
  patientName: string;
  status: AnalysisStatus;
  progress: number;
  createdAt: string;
};

type SummaryType =
  | "total"
  | "completed"
  | "processing"
  | "failed";

type SummaryItem = {
  title: string;
  value: string;
  description: string;
  percentage?: string;
  type: SummaryType;
};

const recentAnalyses: RecentAnalysis[] = [
  {
    ctId: "CT-20260724-001",
    patientId: "P001",
    patientName: "홍길동",
    status: "완료",
    progress: 100,
    createdAt: "2026-07-24 14:30",
  },
  {
    ctId: "CT-20260724-002",
    patientId: "P002",
    patientName: "김철수",
    status: "분석 중",
    progress: 65,
    createdAt: "2026-07-24 15:10",
  },
  {
    ctId: "CT-20260724-003",
    patientId: "P003",
    patientName: "이영희",
    status: "대기",
    progress: 0,
    createdAt: "2026-07-24 15:40",
  },
];

const summaryItems: SummaryItem[] = [
  {
    title: "전체 분석",
    value: "24",
    description: "등록된 전체 분석 건수",
    type: "total",
  },
  {
    title: "분석 완료",
    value: "18",
    description: "분석이 완료된 작업",
    percentage: "75%",
    type: "completed",
  },
  {
    title: "분석 진행 중",
    value: "4",
    description: "현재 처리 중인 작업",
    percentage: "16.7%",
    type: "processing",
  },
  {
    title: "분석 실패",
    value: "2",
    description: "확인이 필요한 작업",
    percentage: "8.3%",
    type: "failed",
  },
];

function MainPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-[1500px]">
        {/* 메인 소개 배너 */}
        <section className="mb-5 overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-r from-white via-[#f8fbff] to-[#eaf4ff] shadow-sm">
          <div className="flex min-h-[205px] items-center px-7 py-7 sm:px-10 lg:px-12">
            <div className="max-w-2xl">
              <span className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-white px-3 py-1.5 text-xs font-bold text-blue-600 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-blue-500" />
                AI Brain CT Analysis
              </span>

              <h1 className="mt-4 text-2xl font-bold tracking-tight text-[#102a5c] sm:text-3xl">
                AI 기반 뇌 CT 영상 분석 지원 시스템
              </h1>

              <p className="mt-3 max-w-xl text-sm leading-7 text-slate-600">
                정량적이고 신뢰할 수 있는 AI 분석으로 의료진의
                신속하고 정확한 임상 의사결정을 지원합니다.
              </p>

              <Link
                to="/upload"
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-md shadow-blue-200 transition hover:bg-blue-700"
              >
                <UploadIcon />
                CT 분석 시작
                <ArrowRightIcon />
              </Link>
            </div>
          </div>
        </section>

        {/* 분석 현황 */}
        <section className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {summaryItems.map((item) => (
            <SummaryCard
              key={item.title}
              item={item}
            />
          ))}
        </section>

        {/* 최근 분석 + 분석 프로세스 */}
        <section className="grid grid-cols-1 items-stretch gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
          {/* 최근 분석 이력 */}
          <article className="flex min-w-0 flex-col overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  최근 분석 이력
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  최근 등록된 CT 분석 작업을 확인합니다.
                </p>
              </div>

              <Link
                to="/history"
                className="shrink-0 rounded-lg border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100"
              >
                전체 보기
              </Link>
            </div>

            {/* 고정 너비 표 */}
            <div className="min-w-0 flex-1 overflow-hidden">
              <table className="w-full table-fixed text-left">
                <colgroup>
                  <col className="w-[18%]" />
                  <col className="w-[10%]" />
                  <col className="w-[11%]" />
                  <col className="w-[11%]" />
                  <col className="w-[20%]" />
                  <col className="w-[17%]" />
                  <col className="w-[13%]" />
                </colgroup>

                <thead className="bg-[#f8fbff] text-sm text-slate-500">
                  <tr>
                    <th className="px-5 py-4 font-semibold">
                      CT ID
                    </th>

                    <th className="px-3 py-4 font-semibold">
                      환자 ID
                    </th>

                    <th className="px-3 py-4 font-semibold">
                      환자 이름
                    </th>

                    <th className="px-3 py-4 font-semibold">
                      상태
                    </th>

                    <th className="px-3 py-4 font-semibold">
                      진행률
                    </th>

                    <th className="px-3 py-4 font-semibold">
                      등록일
                    </th>

                    <th className="px-3 py-4 text-center font-semibold">
                      결과
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {recentAnalyses.map((analysis) => {
                    const detailPath =
                      analysis.status === "완료"
                        ? `/result/${analysis.ctId}`
                        : `/progress/${analysis.ctId}`;

                    const [date, time] =
                      analysis.createdAt.split(" ");

                    return (
                      <tr
                        key={analysis.ctId}
                        className="text-sm text-slate-700 transition hover:bg-blue-50/40"
                      >
                        <td className="break-words px-5 py-5 font-bold leading-5 text-slate-900">
                          {analysis.ctId}
                        </td>

                        <td className="px-3 py-5">
                          {analysis.patientId}
                        </td>

                        <td className="px-3 py-5 font-medium">
                          {analysis.patientName}
                        </td>

                        <td className="px-3 py-5">
                          <StatusBadge
                            status={analysis.status}
                          />
                        </td>

                        <td className="px-3 py-5">
                          <div className="flex min-w-0 items-center gap-2">
                            <div className="h-2.5 min-w-0 flex-1 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className={`h-full rounded-full ${getProgressColor(
                                  analysis.status,
                                )}`}
                                style={{
                                  width: `${analysis.progress}%`,
                                }}
                              />
                            </div>

                            <span className="w-9 shrink-0 text-right text-xs font-semibold text-slate-500">
                              {analysis.progress}%
                            </span>
                          </div>
                        </td>

                        <td className="px-3 py-5 leading-5 text-slate-600">
                          <span className="block whitespace-nowrap">
                            {date}
                          </span>

                          <span className="block">
                            {time}
                          </span>
                        </td>

                        <td className="px-3 py-5 text-center">
                          <Link
                            to={detailPath}
                            className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-lg border border-blue-100 bg-white px-3 py-2 text-xs font-bold text-blue-700 transition hover:bg-blue-50"
                          >
                            {analysis.status === "완료" ? (
                              <>
                                <EyeIcon />
                                보기
                              </>
                            ) : (
                              <>
                                <ProgressIcon />
                                진행
                              </>
                            )}
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            <div className="mt-auto flex justify-center gap-2 border-t border-slate-100 px-6 py-4">
              <PaginationButton label="‹" />

              <PaginationButton
                label="1"
                active
              />

              <PaginationButton label="2" />
              <PaginationButton label="3" />
              <PaginationButton label="›" />
            </div>
          </article>

          {/* 분석 프로세스 */}
          <aside className="flex h-full flex-col rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                분석 프로세스
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                CT 분석은 세 단계로 진행됩니다.
              </p>
            </div>

            <div className="relative mt-6 flex flex-1 flex-col justify-between gap-4">
              <div className="absolute bottom-[56px] left-[18px] top-[56px] border-l border-dashed border-blue-200" />

              <ProcessStep
                number="1"
                title="CT 업로드"
                description="NIfTI 형식의 뇌 CT 영상을 업로드합니다."
                icon={<UploadIcon />}
              />

              <ProcessStep
                number="2"
                title="AI 분석"
                description="AI 모델이 병변을 탐지하고 분석을 수행합니다."
                icon={<BrainIcon />}
              />

              <ProcessStep
                number="3"
                title="결과 확인"
                description="분석 결과와 병변 위치를 확인합니다."
                icon={<ChartIcon />}
              />
            </div>

            <div className="mt-5 flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-3 text-xs font-semibold text-blue-700">
              <ClockIcon />
              평균 분석 소요 시간: 약 2~5분
            </div>
          </aside>
        </section>
      </div>
    </AppLayout>
  );
}

function SummaryCard({
  item,
}: {
  item: SummaryItem;
}) {
  const style = getSummaryStyle(item.type);

  return (
    <article className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center gap-4">
        <div
          className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${style.background} ${style.color}`}
        >
          {style.icon}
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-slate-700">
            {item.title}
          </p>

          <div className="mt-1 flex items-end justify-between gap-2">
            <p className="text-3xl font-bold text-slate-900">
              {item.value}
            </p>

            {item.percentage && (
              <span
                className={`pb-1 text-sm font-bold ${style.color}`}
              >
                {item.percentage}
              </span>
            )}
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs text-slate-400">
        {item.description}
      </p>
    </article>
  );
}

function getSummaryStyle(type: SummaryType) {
  const styles: Record<
    SummaryType,
    {
      background: string;
      color: string;
      icon: ReactNode;
    }
  > = {
    total: {
      background: "bg-blue-50",
      color: "text-blue-600",
      icon: <DatabaseIcon />,
    },
    completed: {
      background: "bg-emerald-50",
      color: "text-emerald-600",
      icon: <CheckIcon />,
    },
    processing: {
      background: "bg-amber-50",
      color: "text-amber-500",
      icon: <LoadingIcon />,
    },
    failed: {
      background: "bg-red-50",
      color: "text-red-500",
      icon: <WarningIcon />,
    },
  };

  return styles[type];
}

function StatusBadge({
  status,
}: {
  status: AnalysisStatus;
}) {
  const styles: Record<AnalysisStatus, string> = {
    완료: "bg-emerald-100 text-emerald-700",
    "분석 중": "bg-blue-100 text-blue-700",
    대기: "bg-amber-100 text-amber-700",
    실패: "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${styles[status]}`}
    >
      {status}
    </span>
  );
}

function getProgressColor(
  status: AnalysisStatus,
) {
  switch (status) {
    case "완료":
      return "bg-emerald-500";

    case "분석 중":
      return "bg-blue-600";

    case "실패":
      return "bg-red-500";

    case "대기":
    default:
      return "bg-amber-400";
  }
}

type ProcessStepProps = {
  number: string;
  title: string;
  description: string;
  icon: ReactNode;
};

function ProcessStep({
  number,
  title,
  description,
  icon,
}: ProcessStepProps) {
  return (
    <div className="relative flex items-center gap-3">
      <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white shadow-sm shadow-blue-200">
        {number}
      </div>

      <div className="flex min-h-[108px] min-w-0 flex-1 items-center gap-3 rounded-xl border border-blue-100 bg-[#fbfdff] p-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
          {icon}
        </div>

        <div className="min-w-0">
          <h3 className="text-sm font-bold text-slate-800">
            {title}
          </h3>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

function PaginationButton({
  label,
  active = false,
}: {
  label: string;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-semibold transition ${
        active
          ? "bg-blue-600 text-white"
          : "border border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
      }`}
    >
      {label}
    </button>
  );
}

/* 아이콘 */

function UploadIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M12 16V4m0 0L7 9m5-5 5 5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 .4-8"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        d="m9 18 6-6-6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function DatabaseIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <ellipse
        cx="12"
        cy="5"
        rx="7"
        ry="3"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"
        stroke="currentColor"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="m8 12 2.5 2.5L16.5 9"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LoadingIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <path
        d="M12 3a9 9 0 1 0 9 9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <path
        d="M10.3 4.2 2.8 17.1A2 2 0 0 0 4.5 20h15a2 2 0 0 0 1.7-2.9L13.7 4.2a2 2 0 0 0-3.4 0Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M12 9v4m0 3h.01"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M9.5 4.5A3 3 0 0 0 5 7v.4A3.5 3.5 0 0 0 4 14a3.5 3.5 0 0 0 5.5 4.5v-14ZM14.5 4.5A3 3 0 0 1 19 7v.4a3.5 3.5 0 0 1 1 6.6 3.5 3.5 0 0 1-5.5 4.5v-14Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M4 20V4m0 16h16"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="m7 16 4-5 3 3 5-7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-4 w-4 shrink-0"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="M12 7v5l3 2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <circle
        cx="12"
        cy="12"
        r="2.5"
        stroke="currentColor"
        strokeWidth="1.7"
      />
    </svg>
  );
}

function ProgressIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="4"
        width="14"
        height="16"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="M9 9h6M9 13h6"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default MainPage;