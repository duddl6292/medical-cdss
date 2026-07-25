import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../layouts/applayout";

function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // .nii 또는 .nii.gz 파일인지 검사
  const validateFile = (file: File) => {
    const fileName = file.name.toLowerCase();

    const isNiftiFile =
      fileName.endsWith(".nii") || fileName.endsWith(".nii.gz");

    if (!isNiftiFile) {
      setSelectedFile(null);
      setErrorMessage(
        ".nii 또는 .nii.gz 형식의 CT 파일만 업로드할 수 있습니다."
      );
      return;
    }

    setSelectedFile(file);
    setErrorMessage("");
  };

  // 파일 선택 버튼으로 파일을 선택했을 때
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      validateFile(file);
    }
  };

  // 파일을 업로드 영역 위로 가져왔을 때
  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  // 파일이 업로드 영역을 벗어났을 때
  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // 파일을 업로드 영역에 놓았을 때
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      validateFile(file);
    }
  };

  // 선택한 파일 삭제
  const handleRemoveFile = () => {
    setSelectedFile(null);
    setErrorMessage("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // 파일 용량을 MB 단위로 표시
  const formatFileSize = (size: number) => {
    const megabytes = size / (1024 * 1024);

    return `${megabytes.toFixed(2)} MB`;
  };

  // 분석 시작
  const handleStartAnalysis = () => {
    if (!selectedFile) {
      setErrorMessage("분석할 CT 파일을 먼저 선택해 주세요.");
      return;
    }

    // API 연결 전 임시 ct_id
    const temporaryCtId = `CT-${Date.now()}`;

    navigate(`/progress/${temporaryCtId}`);
  };

  return (
    <AppLayout>
      <div className="mx-auto max-w-5xl">
        {/* 페이지 제목 */}
        <section className="mb-7">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-900 text-sm font-bold text-white">
              1
            </span>

            <div>
              <h2 className="text-2xl font-bold text-slate-800">
                CT 업로드
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                분석할 뇌 CT NIfTI 파일을 업로드해 주세요.
              </p>
            </div>
          </div>
        </section>

        {/* 분석 단계 표시 */}
        <section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid grid-cols-3 items-center gap-4 text-center">
            <div>
              <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 font-bold text-white">
                1
              </div>
              <p className="mt-2 text-sm font-semibold text-blue-700">
                CT 업로드
              </p>
            </div>

            <div>
              <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 font-bold text-slate-500">
                2
              </div>
              <p className="mt-2 text-sm text-slate-500">
                분석 진행
              </p>
            </div>

            <div>
              <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 font-bold text-slate-500">
                3
              </div>
              <p className="mt-2 text-sm text-slate-500">
                결과 확인
              </p>
            </div>
          </div>
        </section>

        {/* 업로드 카드 */}
        <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
          {/* 파일 업로드 영역 */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`flex min-h-72 flex-col items-center justify-center rounded-xl border-2 border-dashed px-8 py-10 text-center transition ${
              isDragging
                ? "border-blue-500 bg-blue-50"
                : "border-slate-300 bg-slate-50"
            }`}
          >
            {/* 업로드 아이콘 */}
            <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-full border-2 border-slate-300 bg-white">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-10 w-10 text-slate-500"
              >
                <path d="M12 16V4" />
                <path d="m7 9 5-5 5 5" />
                <path d="M5 20h14" />
              </svg>
            </div>

            <h3 className="text-lg font-semibold text-slate-800">
              CT 파일을 드래그하여 놓으세요
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              또는 아래 버튼을 눌러 파일을 선택하세요.
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".nii,.nii.gz"
              onChange={handleFileChange}
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-6 rounded-lg border border-blue-600 bg-white px-5 py-2.5 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
            >
              NIfTI 파일 업로드
            </button>

            <p className="mt-4 text-xs text-slate-400">
              지원 형식: .nii, .nii.gz
            </p>
          </div>

          {/* 오류 메시지 */}
          {errorMessage && (
            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {errorMessage}
            </div>
          )}

          {/* 선택된 파일 */}
          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold text-slate-700">
              선택된 파일
            </h3>

            {selectedFile ? (
              <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-white text-2xl shadow-sm">
                    📄
                  </div>

                  <div className="min-w-0">
                    <div className="grid gap-1 text-sm sm:grid-cols-[80px_1fr]">
                      <span className="text-slate-500">파일명</span>
                      <span className="truncate font-medium text-slate-800">
                        {selectedFile.name}
                      </span>

                      <span className="text-slate-500">형식</span>
                      <span className="text-slate-700">
                        {selectedFile.name.toLowerCase().endsWith(".nii.gz")
                          ? "NIfTI (.nii.gz)"
                          : "NIfTI (.nii)"}
                      </span>

                      <span className="text-slate-500">크기</span>
                      <span className="text-slate-700">
                        {formatFileSize(selectedFile.size)}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="ml-4 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 transition hover:bg-white hover:text-red-600"
                >
                  삭제
                </button>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-6 text-center text-sm text-slate-400">
                선택된 파일이 없습니다.
              </div>
            )}
          </div>

          {/* 분석 시작 */}
          <div className="mt-7 flex justify-end">
            <button
              type="button"
              onClick={handleStartAnalysis}
              disabled={!selectedFile}
              className="min-w-40 rounded-lg bg-blue-700 px-6 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              분석 시작
            </button>
          </div>
        </section>

        {/* 안내 문구 */}
        <section className="mt-6 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4">
          <p className="text-sm leading-6 text-blue-800">
            CT 파일 업로드 후 병변 분할 분석이 시작됩니다. 분석이 완료되면
            병변 위치, 병변 부피와 분석 결과를 확인할 수 있습니다.
          </p>
        </section>
      </div>
    </AppLayout>
  );
}

export default UploadPage;
