import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";

import { requestAnalysis } from "../api/analysis";
import AppLayout from "../layouts/applayout";

const MAX_SIZE = 512 * 1024 * 1024;

export default function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [subjectId, setSubjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function validate(next: File) {
    const name = next.name.toLowerCase();
    if ((!name.endsWith(".nii") && !name.endsWith(".nii.gz")) || next.size > MAX_SIZE) {
      setFile(null);
      setError(".nii 또는 .nii.gz 형식의 512MB 이하 파일만 사용할 수 있습니다.");
      return;
    }
    setFile(next);
    setError("");
  }

  async function start() {
    if (!/^[A-Za-z0-9._-]{3,64}$/.test(subjectId.trim())) {
      setError("비식별 대상 ID는 영문, 숫자, 점, 밑줄, 하이픈으로 3~64자 입력하세요.");
      return;
    }
    if (!file) { setError("분석할 NIfTI 파일을 선택하세요."); return; }
    setSubmitting(true);
    setError("");
    try {
      const created = await requestAnalysis(file, subjectId.trim());
      navigate(`/progress/${created.case_id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "업로드에 실패했습니다.");
      setSubmitting(false);
    }
  }

  function drop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const next = event.dataTransfer.files[0];
    if (next) validate(next);
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl">
        <h1 className="text-2xl font-bold text-slate-900">새 CT 분석</h1>
        <p className="mt-2 text-sm text-slate-500">비식별 NIfTI 영상만 등록할 수 있습니다.</p>
        <section className="mt-6 space-y-6 rounded-2xl border bg-white p-7 shadow-sm">
          <label className="block text-sm font-bold text-slate-700">비식별 대상 ID
            <input value={subjectId} onChange={(e) => setSubjectId(e.target.value)} placeholder="예: DEMO-2026-001"
              className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4" />
            <span className="mt-2 block text-xs font-normal text-slate-500">이름, 등록번호, 생년월일 등 실제 식별정보는 입력하지 마세요.</span>
          </label>
          <div onDragOver={(e) => e.preventDefault()} onDrop={drop}
            className="flex min-h-64 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-blue-200 bg-blue-50/40 p-8 text-center">
            <p className="font-bold text-slate-800">{file ? file.name : "NIfTI 파일을 놓거나 선택하세요"}</p>
            {file && <p className="mt-2 text-sm text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>}
            <input ref={inputRef} type="file" accept=".nii,.gz" className="hidden"
              onChange={(e: ChangeEvent<HTMLInputElement>) => { const next = e.target.files?.[0]; if (next) validate(next); }} />
            <button type="button" onClick={() => inputRef.current?.click()} className="mt-5 rounded-xl border border-blue-200 bg-white px-5 py-3 text-sm font-bold text-blue-700">파일 선택</button>
          </div>
          {error && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end"><button onClick={start} disabled={submitting}
            className="rounded-xl bg-blue-600 px-6 py-3 font-bold text-white disabled:bg-blue-300">{submitting ? "업로드 중..." : "분석 시작"}</button></div>
        </section>
      </div>
    </AppLayout>
  );
}
