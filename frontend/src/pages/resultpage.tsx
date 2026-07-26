import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppLayout from "../layouts/applayout";
import NiivueViewer, {
  type ViewerMode,
} from "../components/niivueviewer";

function ResultPage() {
  const { analysisId } = useParams();

  const [viewerMode, setViewerMode] =
    useState<ViewerMode>("axial");

  /*
   * 병변 마스크 표시 여부
   */
  const [overlayVisible, setOverlayVisible] =
    useState(true);

  /*
   * Niivue의 opacity는 0~1 범위를 사용합니다.
   *
   * 0.6 = 60%
   */
  const [overlayOpacity, setOverlayOpacity] =
    useState(0.6);

  /*
   * 현재는 화면 테스트용 임시 데이터입니다.
   *
   * Django API 연결 후 API 응답 데이터로
   * 교체하면 됩니다.
   */
  const resultData = {
    analysisId:
      analysisId ?? "CT-1784986552442",

    status: "completed",

    patientId: "P001",
    patientName: "홍길동",
    gender: "M",
    age: 67,
    examinationDate: "2026-07-26",
    examinationType: "Brain CT",

    prediction: "뇌출혈",
    diceScore: 0.92,
    lesionVolume: 12.8,
    confidence: 89,
    analysisTime: 12,
    detected: true,

    aiSummary:
      "병변은 8번부터 25번 슬라이스 범위에서 관찰되며, 16번 슬라이스에서 가장 크게 확인됩니다. 의료진의 추가 판독을 권장합니다.",

    /*
     * 테스트 NIfTI 파일 경로
     *
     * public 폴더를 기준으로 작성합니다.
     */
    originalNiftiUrl:
      "/sample/ID_0b10cbee_ID_f91d6a7cd2.nii.gz",

    /*
     * 실제 마스크 파일이 준비되면 아래처럼 넣습니다.
     *
     * maskNiftiUrl: "/sample/mask.nii.gz",
     */
    maskNiftiUrl: undefined as
      | string
      | undefined,
  };

  return (
    <AppLayout>
      <main className="mx-auto w-full max-w-[1500px]">
        {/* 페이지 상단 */}
        <section className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                AI 분석 결과
              </h1>

              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                완료
              </span>
            </div>

            <p className="mt-2 text-sm text-slate-500">
              CT ID: {resultData.analysisId}
            </p>
          </div>

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

        {/* 분석 단계 표시 */}
        <section className="mb-5 rounded-2xl border border-slate-200 bg-white px-6 py-6 shadow-sm">
          <div className="grid grid-cols-3 items-center">
            {/* 1단계 */}
            <div className="flex flex-col items-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-100 text-lg font-bold text-emerald-700">
                ✓
              </div>

              <p className="mt-3 text-sm font-bold text-emerald-700">
                CT 업로드
              </p>
            </div>

            {/* 2단계 */}
            <div className="flex flex-col items-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-100 text-lg font-bold text-emerald-700">
                ✓
              </div>

              <p className="mt-3 text-sm font-bold text-emerald-700">
                분석 진행
              </p>
            </div>

            {/* 3단계 */}
            <div className="flex flex-col items-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-600 text-lg font-bold text-white">
                3
              </div>

              <p className="mt-3 text-sm font-bold text-blue-600">
                결과 확인
              </p>
            </div>
          </div>
        </section>


        {/* 임상 활용 안내 */}
        <section className="mb-5 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-100 text-lg">
              ⚠
            </div>

            <div>
              <h2 className="text-sm font-bold text-amber-900">
                임상 활용 안내
              </h2>

              <p className="mt-1 text-sm leading-6 text-amber-800">
                본 결과는 의료진의 임상 판단을 지원하기
                위한 참고 정보이며 최종 진단을 대체하지
                않습니다.
              </p>
            </div>
          </div>
        </section>

        {/* 환자 정보 */}
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

        {/* 메인 영역 */}
        <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          {/* CT Viewer */}
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            {/* 뷰어 제목 및 방향 선택 */}
            <div className="flex flex-col gap-4 px-6 pt-5 lg:flex-row lg:items-center lg:justify-between">
              <h2 className="text-lg font-bold text-slate-900">
                CT Viewer
              </h2>

              <div className="flex flex-wrap gap-2">
                <ViewerModeButton
                  label="Axial"
                  active={viewerMode === "axial"}
                  onClick={() =>
                    setViewerMode("axial")
                  }
                />

                <ViewerModeButton
                  label="Coronal"
                  active={
                    viewerMode === "coronal"
                  }
                  onClick={() =>
                    setViewerMode("coronal")
                  }
                />

                <ViewerModeButton
                  label="Sagittal"
                  active={
                    viewerMode === "sagittal"
                  }
                  onClick={() =>
                    setViewerMode("sagittal")
                  }
                />

                <ViewerModeButton
                  label="Multi View"
                  active={
                    viewerMode ===
                    "multiplanar"
                  }
                  onClick={() =>
                    setViewerMode(
                      "multiplanar",
                    )
                  }
                />
              </div>
            </div>

            {/* Niivue 실제 뷰어 */}
            <div className="px-6 pb-5 pt-3">
              <NiivueViewer
                originalUrl={
                  resultData.originalNiftiUrl
                }
                maskUrl={
                  resultData.maskNiftiUrl
                }
                overlayOpacity={
                  overlayOpacity
                }
                overlayVisible={
                  overlayVisible
                }
                viewerMode={viewerMode}
                onOverlayOpacityChange={
                  setOverlayOpacity
                }
                onOverlayVisibleChange={
                  setOverlayVisible
                }
              />

              {/* 안내 문구만 하단에 유지 */}
              <p className="mt-3 rounded-lg bg-blue-50 px-4 py-3 text-sm font-medium text-blue-700">
                🔍{" "}
                {viewerMode ===
                "multiplanar"
                  ? "Axial, Coronal, Sagittal 세 단면을 동시에 확인할 수 있습니다."
                  : `${getViewerLabel(
                      viewerMode,
                    )} 단면을 크게 확인하고, Slice 슬라이더로 원하는 단면을 선택할 수 있습니다.`}
              </p>
            </div>
          </section>

          {/* 오른쪽 분석 결과 영역 */}
          <aside className="space-y-5">
            {/* 분석 결과 */}
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">
                분석 결과
              </h2>

              <dl className="mt-4 divide-y divide-slate-200">
                <ResultRow
                  label="예측 결과"
                  value={
                    resultData.prediction
                  }
                  danger
                />

                <ResultRow
                  label="Dice Score"
                  value={resultData.diceScore.toFixed(
                    2,
                  )}
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
                  danger={
                    resultData.detected
                  }
                />
              </dl>
            </section>

            {/* AI 판독 요약 */}
            <section className="rounded-2xl border border-violet-200 bg-gradient-to-br from-white to-violet-50 p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-lg font-bold text-indigo-900">
                  AI 판독 요약
                </h2>

                <span className="rounded-full bg-violet-200 px-3 py-1 text-xs font-bold text-violet-700">
                  XAI
                </span>
              </div>

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

function getViewerLabel(
  viewerMode: ViewerMode,
) {
  switch (viewerMode) {
    case "coronal":
      return "Coronal";

    case "sagittal":
      return "Sagittal";

    case "multiplanar":
      return "Multi View";

    case "axial":
    default:
      return "Axial";
  }
}

export default ResultPage;