import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppLayout from "../layouts/applayout";
import NiivueViewer from "../components/niivueviewer";

/**
 * AI 분석 결과 페이지
 *
 * 화면 구성
 * 1. 페이지 제목과 이동 버튼
 * 2. 임상 활용 안내
 * 3. 환자 정보
 * 4. Niivue 의료영상 뷰어
 * 5. 분석 결과
 * 6. AI 판독 요약(XAI)
 */
function ResultPage() {
  /**
   * 주소의 분석 ID를 가져옵니다.
   *
   * 예:
   * /result/CT-001
   * → analysisId = "CT-001"
   */
  const { analysisId } = useParams();

  const [viewerMode, setViewerMode] =
    useState<
      "axial" |
      "coronal" |
      "sagittal" |
      "multiplanar"
    >("axial");


  /**
   * 병변 마스크를 화면에 표시할지 결정합니다.
   */
  const [overlayVisible, setOverlayVisible] = useState(true);

  /**
   * 병변 마스크 투명도입니다.
   *
   * 화면에서는 0~100으로 표시하고,
   * Niivue에는 0~1로 변환하여 전달합니다.
   */
  const [overlayOpacity, setOverlayOpacity] = useState(60);

  /**
   * 현재는 화면 테스트를 위한 임시 데이터입니다.
   *
   * 나중에 Django API를 연결하면
   * 이 객체를 API 응답 데이터로 교체하면 됩니다.
   */
  const resultData = {
    // 분석 기본 정보
    analysisId: analysisId ?? "CT-1784986552442",
    status: "completed",

    // 환자 정보
    patientId: "P001",
    patientName: "홍길동",
    gender: "M",
    age: 67,
    examinationDate: "2026-07-26",
    examinationType: "Brain CT",

    // 모델 분석 결과
    prediction: "뇌출혈",
    diceScore: 0.92,
    lesionVolume: 12.8,
    confidence: 89,
    analysisTime: 12,
    detected: true,

    /**
     * AI 판독 요약
     *
     * 분석 결과 카드에 있는 숫자를 반복해서 나열하기보다는
     * 사용자가 이해하기 쉬운 하나의 설명 문장으로 제공합니다.
     *
     * 나중에는 API 응답의 xai_summary 등의 값으로 교체합니다.
     */
    aiSummary:
      "우측 기저핵 부위에서 출혈성 병변이 탐지되었습니다. 병변은 8번부터 25번 슬라이스 범위에서 관찰되며, 16번 슬라이스에서 가장 크게 확인됩니다. 의료진의 추가 판독을 권장합니다.",

    /**
     * NIfTI 파일 경로
     *
     * 테스트 파일을 사용할 경우:
     * frontend/public/sample/original.nii.gz
     * frontend/public/sample/mask.nii.gz
     */
    originalNiftiUrl: "/sample/ID_0b10cbee_ID_f91d6a7cd2.nii.gz",
    // 아직 실제 마스크 파일이 없으므로 undefined
    maskNiftiUrl: undefined,
  };

  return (
    <AppLayout>
      <main className="mx-auto w-full max-w-[1500px]">
        {/* =====================================================
            1. 페이지 상단 제목과 이동 버튼
        ====================================================== */}
        <section className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                AI 분석 결과
              </h1>

              {/* 분석 완료 상태 */}
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                완료
              </span>
            </div>

            <p className="mt-2 text-sm text-slate-500">
              CT ID: {resultData.analysisId}
            </p>
          </div>

          {/* 페이지 이동 버튼 */}
          <div className="flex flex-wrap gap-3">
            <Link
              to="/history"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              분석 기록으로 이동
            </Link>

            <Link
              to="/upload"
              className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              새 CT 분석
            </Link>
          </div>
        </section>

        {/* =====================================================
            2. 임상 활용 안내
            페이지 상단에서 한 번만 표시합니다.
        ====================================================== */}
        <section className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <div className="flex items-start gap-3">
            {/* 경고 아이콘 */}
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-100 text-lg">
              ⚠
            </div>

            <div>
              <h2 className="text-sm font-bold text-amber-900">
                임상 활용 안내
              </h2>

              <p className="mt-1 text-sm leading-6 text-amber-800">
                본 결과는 의료진의 임상 판단을 지원하기 위한 참고
                정보이며 최종 진단을 대체하지 않습니다.
              </p>
            </div>
          </div>
        </section>

        {/* =====================================================
            3. 환자 정보
        ====================================================== */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">
            환자 정보
          </h2>

          <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
            <PatientInfo
              label="환자 ID"
              value={resultData.patientId}
            />

            <PatientInfo
              label="이름"
              value={resultData.patientName}
            />

            <PatientInfo
              label="성별 / 나이"
              value={`${resultData.gender} / ${resultData.age}`}
            />

            <PatientInfo
              label="검사일"
              value={resultData.examinationDate}
            />

            <PatientInfo
              label="검사 종류"
              value={resultData.examinationType}
            />
          </dl>
        </section>

        {/* =====================================================
            4. 메인 영역

            왼쪽: Niivue Viewer
            오른쪽: 분석 결과 + AI 판독 요약
        ====================================================== */}
        <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          {/* ---------------------------------------------------
              왼쪽: CT Viewer
          ---------------------------------------------------- */}
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            {/* 뷰어 제목 */}
            <div className="flex flex-col gap-4 px-6 pt-5 lg:flex-row lg:items-center lg:justify-between">
              <h2 className="text-lg font-bold text-slate-900">
                CT Viewer
              </h2>

              <div className="flex flex-wrap gap-2">
                <ViewerModeButton
                  label="Axial"
                  active={viewerMode === "axial"}
                  onClick={() => setViewerMode("axial")}
                />

                <ViewerModeButton
                  label="Coronal"
                  active={viewerMode === "coronal"}
                  onClick={() => setViewerMode("coronal")}
                />

                <ViewerModeButton
                  label="Sagittal"
                  active={viewerMode === "sagittal"}
                  onClick={() => setViewerMode("sagittal")}
                />

                <ViewerModeButton
                  label="Multi View"
                  active={viewerMode === "multiplanar"}
                  onClick={() => setViewerMode("multiplanar")}
                />
              </div>
            </div>

            {/* Niivue 실제 뷰어 영역 */}
            <div className="px-6 pb-3 pt-3">
              <NiivueViewer
                originalUrl={resultData.originalNiftiUrl}
                maskUrl={resultData.maskNiftiUrl}
                overlayVisible={overlayVisible}
                overlayOpacity={overlayOpacity / 100}
                viewerMode={viewerMode}
              />

            <p className="mt-2 text-xs text-slate-500">
              {viewerMode === "multiplanar"
                ? "Axial, Coronal, Sagittal 및 3D 영상을 동시에 확인할 수 있습니다."
                : `${viewerMode} 영상을 크게 확인할 수 있습니다.`}
            </p>
            </div>

            {/* -------------------------------------------------
                Niivue 조작 영역
            -------------------------------------------------- */}
            <div className="grid grid-cols-1 gap-5 border-t border-slate-200 bg-slate-50/60 px-6 py-5 md:grid-cols-2">
              {/* 오버레이 투명도 조절 */}
              <div>
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="overlay-opacity"
                    className="text-sm font-semibold text-slate-700"
                  >
                    오버레이 투명도
                  </label>

                  <span className="text-sm font-bold text-blue-600">
                    {overlayOpacity}%
                  </span>
                </div>

                <input
                  id="overlay-opacity"
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={overlayOpacity}
                  disabled={!overlayVisible}
                  onChange={(event) =>
                    setOverlayOpacity(
                      Number(event.target.value),
                    )
                  }
                  className="mt-4 w-full cursor-pointer accent-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
                />
              </div>

              {/* 병변 마스크 표시 스위치 */}
              <div className="flex items-center justify-between rounded-xl bg-white px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-700">
                    병변 오버레이
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    AI가 탐지한 병변 마스크를 표시합니다.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    setOverlayVisible((previous) => !previous)
                  }
                  aria-label="병변 오버레이 표시 전환"
                  aria-pressed={overlayVisible}
                  className={`relative h-7 w-12 shrink-0 rounded-full transition ${
                    overlayVisible
                      ? "bg-blue-600"
                      : "bg-slate-300"
                  }`}
                >
                  <span
                    className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition ${
                      overlayVisible
                        ? "left-6"
                        : "left-1"
                    }`}
                  />
                </button>
              </div>
            </div>
          </section>

          {/* ---------------------------------------------------
              오른쪽: 분석 결과와 AI 요약
          ---------------------------------------------------- */}
          <aside className="space-y-5">
            {/* 분석 결과 카드 */}
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">
                분석 결과
              </h2>

              <dl className="mt-4 divide-y divide-slate-200">
                <ResultRow
                  label="예측 결과"
                  value={resultData.prediction}
                  danger
                />

                <ResultRow
                  label="Dice Score"
                  value={resultData.diceScore.toFixed(2)}
                />

                <ResultRow
                  label="병변 부피"
                  value={`${resultData.lesionVolume} mL`}
                />

                <ResultRow
                  label="신뢰도"
                  value={`${resultData.confidence}%`}
                />

                <ResultRow
                  label="분석 시간"
                  value={`${resultData.analysisTime}초`}
                />

                <ResultRow
                  label="탐지 여부"
                  value={
                    resultData.detected
                      ? "탐지됨"
                      : "탐지되지 않음"
                  }
                  danger={resultData.detected}
                />
              </dl>
            </section>

            {/* =================================================
                AI 판독 요약 카드

                위 분석 결과의 숫자를 그대로 반복하지 않고,
                모델 결과를 이해하기 쉬운 문장으로 제공합니다.
            ================================================== */}
            <section className="rounded-2xl border border-violet-200 bg-gradient-to-br from-white to-violet-50 p-6 shadow-sm">
              {/* 카드 제목 */}
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-bold text-indigo-900">
                  AI 판독 요약
                </h2>

                <span className="rounded-full bg-violet-200 px-3 py-1 text-xs font-bold text-violet-700">
                  XAI
                </span>
              </div>

              {/* 요약 아이콘과 문장 */}
              <div className="mt-5 flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-200 bg-white text-xl">
                  💬
                </div>

                <p className="text-sm leading-7 text-slate-700">
                  {resultData.aiSummary}
                </p>
              </div>
            </section>
          </aside>
        </div>
      </main>
    </AppLayout>
  );
}

/* ============================================================
   환자 정보 항목 컴포넌트

   같은 디자인을 여러 번 반복하지 않도록 분리했습니다.
============================================================ */

type PatientInfoProps = {
  label: string;
  value: string;
};

function PatientInfo({
  label,
  value,
}: PatientInfoProps) {
  return (
    <div>
      <dt className="text-sm text-slate-500">
        {label}
      </dt>

      <dd className="mt-2 font-bold text-slate-900">
        {value}
      </dd>
    </div>
  );
}

/* ============================================================
   분석 결과 한 줄 컴포넌트

   danger가 true이면 결과를 빨간색으로 표시합니다.
============================================================ */

type ResultRowProps = {
  label: string;
  value: string;
  danger?: boolean;
};

function ResultRow({
  label,
  value,
  danger = false,
}: ResultRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0">
      <dt className="text-sm font-medium text-slate-600">
        {label}
      </dt>

      <dd
        className={`text-sm font-bold ${
          danger
            ? "text-red-600"
            : "text-slate-900"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
//-----------버튼 컴포넌트 ----------//
type ViewerModeButtonProps = {
  label: string;
  active: boolean;
  onClick: () => void;
};

function ViewerModeButton({
  label,
  active,
  onClick,
}: ViewerModeButtonProps) {
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