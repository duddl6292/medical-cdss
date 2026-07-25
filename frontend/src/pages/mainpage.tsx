import { Link } from "react-router-dom";
import AppLayout from "../layouts/applayout";

const recentAnalyses = [
  {
    ctId: "CT-20260724-001",
    patientId: "P001",
    status: "완료",
    progress: 100,
    createdAt: "2026-07-24 14:30",
  },
  {
    ctId: "CT-20260724-002",
    patientId: "P002",
    status: "분석 중",
    progress: 65,
    createdAt: "2026-07-24 15:10",
  },
  {
    ctId: "CT-20260724-003",
    patientId: "P003",
    status: "대기",
    progress: 0,
    createdAt: "2026-07-24 15:40",
  },
];

function MainPage() {
  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl">
        {/* 페이지 제목 */}
        <section className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">
              대시보드
            </h2>

            <p className="mt-1 text-slate-500">
              CT 분석 현황과 최근 분석 내역을 확인합니다.
            </p>
          </div>

          <Link
            to="/upload"
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-3 font-medium text-white transition hover:bg-blue-700"
          >
            새 CT 분석
          </Link>
        </section>

        {/* 분석 현황 요약 */}
        <section className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryCard
            title="전체 분석"
            value="24"
            description="등록된 전체 분석"
          />

          <SummaryCard
            title="분석 완료"
            value="18"
            description="분석이 완료된 작업"
          />

          <SummaryCard
            title="분석 진행 중"
            value="4"
            description="현재 처리 중인 작업"
          />

          <SummaryCard
            title="분석 실패"
            value="2"
            description="확인이 필요한 작업"
          />
        </section>

        {/* 최근 분석 내역 */}
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
            <div>
              <h3 className="text-lg font-semibold text-slate-800">
                최근 분석 내역
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                최근 등록된 CT 분석 작업입니다.
              </p>
            </div>

            <Link
              to="/history"
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              전체 보기
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead className="bg-slate-50 text-sm text-slate-500">
                <tr>
                  <th className="px-6 py-4 font-medium">CT ID</th>
                  <th className="px-6 py-4 font-medium">환자 ID</th>
                  <th className="px-6 py-4 font-medium">상태</th>
                  <th className="px-6 py-4 font-medium">진행률</th>
                  <th className="px-6 py-4 font-medium">등록일</th>
                  <th className="px-6 py-4 font-medium">관리</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-200">
                {recentAnalyses.map((analysis) => {
                  const detailPath =
                    analysis.status === "완료"
                      ? `/result/${analysis.ctId}`
                      : `/progress/${analysis.ctId}`;

                  return (
                    <tr
                      key={analysis.ctId}
                      className="text-sm text-slate-700 transition hover:bg-slate-50"
                    >
                      <td className="px-6 py-4 font-medium text-slate-800">
                        {analysis.ctId}
                      </td>

                      <td className="px-6 py-4">
                        {analysis.patientId}
                      </td>

                      <td className="px-6 py-4">
                        <StatusBadge status={analysis.status} />
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-2 w-28 overflow-hidden rounded-full bg-slate-200">
                            <div
                              className="h-full rounded-full bg-blue-600"
                              style={{
                                width: `${analysis.progress}%`,
                              }}
                            />
                          </div>

                          <span className="min-w-10 text-slate-600">
                            {analysis.progress}%
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        {analysis.createdAt}
                      </td>

                      <td className="px-6 py-4">
                        <Link
                          to={detailPath}
                          className="inline-flex rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
                        >
                          {analysis.status === "완료"
                            ? "결과 보기"
                            : "진행 보기"}
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* 안내 문구 */}
        <section className="mt-6 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4">
          <p className="text-sm leading-6 text-blue-800">
            새로운 CT 영상을 분석하려면 ‘새 CT 분석’ 버튼을 눌러
            NIfTI 파일을 업로드해 주세요.
          </p>
        </section>
      </div>
    </AppLayout>
  );
}

type SummaryCardProps = {
  title: string;
  value: string;
  description: string;
};

function SummaryCard({
  title,
  value,
  description,
}: SummaryCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-slate-500">
        {title}
      </p>

      <p className="mt-3 text-3xl font-bold text-slate-800">
        {value}
      </p>

      <p className="mt-2 text-xs text-slate-400">
        {description}
      </p>
    </article>
  );
}

type StatusBadgeProps = {
  status: string;
};

function StatusBadge({ status }: StatusBadgeProps) {
  const statusStyle: Record<string, string> = {
    완료: "bg-green-100 text-green-700",
    "분석 중": "bg-blue-100 text-blue-700",
    대기: "bg-yellow-100 text-yellow-700",
    실패: "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
        statusStyle[status] ?? "bg-slate-100 text-slate-600"
      }`}
    >
      {status}
    </span>
  );
}

export default MainPage;