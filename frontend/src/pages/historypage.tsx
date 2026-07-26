import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import AppLayout from "../layouts/applayout";

type AnalysisStatus =
  | "waiting"
  | "processing"
  | "completed"
  | "failed";

interface HistoryItem {
  ctId: string;
  patientId: string;
  status: AnalysisStatus;
  createdAt: string;
  elapsedTime: number;
}

/*
 * 임시 분석 이력 데이터
 *
 * Django API 연결 후
 * GET /api/v1/history/ 응답 데이터로 교체합니다.
 */
const mockHistory: HistoryItem[] = [
  {
    ctId: "CT-1785006939204",
    patientId: "P001",
    status: "completed",
    createdAt: "2026-07-26 00:15",
    elapsedTime: 57,
  },
  {
    ctId: "CT-1785006939205",
    patientId: "P002",
    status: "processing",
    createdAt: "2026-07-26 09:10",
    elapsedTime: 28,
  },
  {
    ctId: "CT-1785006939206",
    patientId: "P003",
    status: "failed",
    createdAt: "2026-07-25 16:32",
    elapsedTime: 14,
  },
];

/*
 * 분석 상태 한글 표시
 */
const statusLabel: Record<AnalysisStatus, string> = {
  waiting: "대기",
  processing: "분석 중",
  completed: "완료",
  failed: "실패",
};

/*
 * 분석 상태별 배지 색상
 */
const statusClass: Record<AnalysisStatus, string> = {
  waiting: "bg-slate-100 text-slate-600",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

/*
 * 초 단위 경과 시간을 MM:SS 형식으로 변환합니다.
 */
function formatElapsedTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(
    remainSeconds,
  ).padStart(2, "0")}`;
}

function HistoryPage() {
  const navigate = useNavigate();

  const [keyword, setKeyword] = useState("");

  const [statusFilter, setStatusFilter] = useState<
    "all" | AnalysisStatus
  >("all");

  /*
   * 검색어와 분석 상태를 기준으로 이력을 필터링합니다.
   */
  const filteredHistory = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return mockHistory.filter((item) => {
      const matchesKeyword =
        item.ctId.toLowerCase().includes(normalizedKeyword) ||
        item.patientId
          .toLowerCase()
          .includes(normalizedKeyword);

      const matchesStatus =
        statusFilter === "all" ||
        item.status === statusFilter;

      return matchesKeyword && matchesStatus;
    });
  }, [keyword, statusFilter]);

  /*
   * 완료된 분석은 결과 페이지로 이동하고,
   * 진행 중 또는 대기 상태는 진행 페이지로 이동합니다.
   */
  const handleOpen = (item: HistoryItem) => {
    if (item.status === "completed") {
      navigate(`/result/${item.ctId}`);
      return;
    }

    if (
      item.status === "processing" ||
      item.status === "waiting"
    ) {
      navigate(`/progress/${item.ctId}`);
    }
  };

  /*
   * 검색어와 상태 필터를 초기화합니다.
   */
  const handleReset = () => {
    setKeyword("");
    setStatusFilter("all");
  };

  const hasFilter =
    keyword.trim() !== "" || statusFilter !== "all";

  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl">
        {/* 페이지 제목 */}
        <section className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            분석 이력
          </h1>

          <p className="mt-2 text-slate-500">
            업로드한 CT 영상의 분석 상태와 결과를 확인합니다.
          </p>
        </section>

        {/* 검색 및 상태 필터 */}
        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row">
            <input
              type="text"
              value={keyword}
              onChange={(event) =>
                setKeyword(event.target.value)
              }
              placeholder="CT ID 또는 환자 ID 검색"
              className="flex-1 rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value as
                    | "all"
                    | AnalysisStatus,
                )
              }
              className="rounded-lg border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="all">전체 상태</option>
              <option value="waiting">대기</option>
              <option value="processing">분석 중</option>
              <option value="completed">완료</option>
              <option value="failed">실패</option>
            </select>

            {hasFilter && (
              <button
                type="button"
                onClick={handleReset}
                className="rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                초기화
              </button>
            )}
          </div>

          <p className="mt-4 text-sm text-slate-500">
            총{" "}
            <span className="font-semibold text-slate-800">
              {filteredHistory.length}
            </span>
            건의 분석 이력이 있습니다.
          </p>
        </section>

        {/* 분석 이력 표 */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead className="bg-slate-50 text-sm text-slate-500">
                <tr>
                  <th className="px-6 py-4 font-semibold">
                    CT ID
                  </th>

                  <th className="px-6 py-4 font-semibold">
                    환자 ID
                  </th>

                  <th className="px-6 py-4 font-semibold">
                    분석 상태
                  </th>

                  <th className="px-6 py-4 font-semibold">
                    분석 일시
                  </th>

                  <th className="px-6 py-4 font-semibold">
                    경과 시간
                  </th>

                  <th className="px-6 py-4 text-center font-semibold">
                    상세 보기
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {filteredHistory.map((item) => (
                  <tr
                    key={item.ctId}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="px-6 py-5 font-semibold text-slate-900">
                      {item.ctId}
                    </td>

                    <td className="px-6 py-5 text-slate-700">
                      {item.patientId}
                    </td>

                    <td className="px-6 py-5">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${statusClass[item.status]}`}
                      >
                        {statusLabel[item.status]}
                      </span>
                    </td>

                    <td className="px-6 py-5 text-slate-600">
                      {item.createdAt}
                    </td>

                    <td className="px-6 py-5 text-slate-600">
                      {formatElapsedTime(
                        item.elapsedTime,
                      )}
                    </td>

                    <td className="px-6 py-5 text-center">
                      {item.status === "failed" ? (
                        <span className="text-sm font-medium text-red-500">
                          분석 실패
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            handleOpen(item)
                          }
                          className="rounded-lg border border-blue-600 px-4 py-2 text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
                        >
                          {item.status === "completed"
                            ? "결과 보기"
                            : "진행 보기"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 검색 결과가 없을 때 */}
          {filteredHistory.length === 0 && (
            <div className="py-20 text-center">
              <p className="font-semibold text-slate-600">
                조건에 맞는 분석 이력이 없습니다.
              </p>

              <button
                type="button"
                onClick={handleReset}
                className="mt-4 text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                검색 조건 초기화
              </button>
            </div>
          )}
        </section>
      </div>
    </AppLayout>
  );
}

export default HistoryPage;