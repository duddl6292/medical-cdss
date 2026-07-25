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
      <div className="mx-auto max-w-4xl">
        {/* 페이지 제목 */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">
            CT 영상 분석 요청
          </h2>

          <p className="mt-2 text-slate-500">
            분석할 뇌 CT 영상을 NIfTI 형식으로 업로드해 주세요.
          </p>
        </section>

        {/* 업로드 카드 */}
        <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          {/* 드래그 앤 드롭 영역 */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`flex min-h-72 flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition ${
              isDragging
                ? "border-blue-500 bg-blue-50"
                : "border-slate-300 bg-slate-50"
            }`}
          >
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-3xl text-blue-600">
              ↑
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
              className="mt-6 rounded-lg bg-blue-600 px-5 py-3 font-medium text-white transition hover:bg-blue-700"
            >
              파일 선택
            </button>

            <p className="mt-4 text-xs text-slate-400">
              지원 형식: .nii, .nii.gz
            </p>
          </div>

          {/* 오류 메시지 */}
          {errorMessage && (
            <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
              {errorMessage}
            </p>
          )}

          {/* 선택된 파일 정보 */}
          {selectedFile && (
            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">
                    선택된 파일
                  </p>

                  <p className="mt-1 font-semibold text-slate-800">
                    {selectedFile.name}
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    파일 크기: {formatFileSize(selectedFile.size)}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
                >
                  삭제
                </button>
              </div>
            </div>
          )}

          {/* 분석 시작 버튼 */}
          <div className="mt-8 flex justify-end">
            <button
              type="button"
              onClick={handleStartAnalysis}
              disabled={!selectedFile}
              className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              분석 시작
            </button>
          </div>
        </section>

        {/* 안내 */}
        <section className="mt-6 rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h3 className="font-semibold text-blue-900">업로드 안내</h3>

          <p className="mt-2 text-sm leading-6 text-blue-700">
            .nii 또는 .nii.gz 형식의 NIfTI 파일을 업로드할 수 있습니다.
            환자 개인정보가 포함되지 않은 파일을 사용해 주세요.
          </p>
        </section>
      </div>
    </AppLayout>
  );
}

export default UploadPage;