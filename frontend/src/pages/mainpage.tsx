import { Link } from "react-router-dom";

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
    <div className="min-h-screen bg-slate-100">
      <header className="flex h-16 items-center justify-between border-b bg-white px-8">
        <div>
          <h1 className="text-xl font-bold text-slate-800">
            Medical CDSS
          </h1>
          <p className="text-sm text-slate-500">
            AI 기반 뇌 CT 영상 분석 지원 시스템
          </p>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">관리자</span>

          <Link
            to="/"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            대시보드
          </Link>
        </div>
      </header>

      <div className="flex">
        <aside className="min-h-[calc(100vh-64px)] w-60 border-r bg-white p-4">
          <nav className="space-y-2">
            <Link
              to="/"
              className="block w-full rounded-lg bg-blue-600 px-4 py-3 text-left font-medium text-white"
            >
              대시보드
            </Link>

            <Link
              to="/upload"
              className="block w-full rounded-lg px-4 py-3 text-left text-slate-600 hover:bg-slate-100"
            >
              CT 분석
            </Link>

            <Link
              to="/history"
              className="block w-full rounded-lg px-4 py-3 text-left text-slate-600 hover:bg-slate-100"
            >
              분석 기록
            </Link>
          </nav>
        </aside>

        <main className="flex-1 p-8">
          <section className="mb-8 flex items-center justify-between">
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
              className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
            >
              새 CT 분석
            </Link>
          </section>

          <section className="mb-8 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
            <SummaryCard title="전체 분석" value="24" />
            <SummaryCard title="분석 완료" value="18" />
            <SummaryCard title="분석 진행 중" value="4" />
            <SummaryCard title="분석 실패" value="2" />
          </section>

          <section className="overflow-hidden rounded-xl border bg-white shadow-sm">
            <div className="flex items-center justify-between border-b px-6 py-5">
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
              <table className="w-full text-left">
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

                <tbody className="divide-y">
                  {recentAnalyses.map((analysis) => (
                    <tr
                      key={analysis.ctId}
                      className="text-sm text-slate-700 hover:bg-slate-50"
                    >
                      <td className="px-6 py-4 font-medium">
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

                          <span>{analysis.progress}%</span>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        {analysis.createdAt}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

type SummaryCardProps = {
  title: string;
  value: string;
};

function SummaryCard({ title, value }: SummaryCardProps) {
  return (
    <article className="rounded-xl border bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-bold text-slate-800">{value}</p>
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