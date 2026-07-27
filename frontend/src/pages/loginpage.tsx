import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/authcontext";

const adminUrl =
  import.meta.env.VITE_ADMIN_URL ??
  "https://medical-cdss-backend-356595725907.asia-southeast1.run.app/admin/";

export default function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(username.trim(), password);
      const target = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(target, { replace: true });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <a
        href={adminUrl}
        className="absolute right-5 top-5 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs font-bold text-slate-600 shadow-sm transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 sm:right-7 sm:top-7"
        aria-label="Django 관리자 로그인 페이지로 이동"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M5.5 20a6.5 6.5 0 0 1 13 0M18.5 5.5l.7.7m0 3.6-.7.7M21 8h-1"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
        관리자 로그인
      </a>
      <section className="w-full max-w-md rounded-3xl border border-blue-100 bg-white p-8 shadow-xl">
        <p className="text-sm font-bold text-blue-600">MEDICAL CDSS</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">의료진 로그인</h1>
        <p className="mt-3 text-sm leading-6 text-slate-500">Django 관리자가 발급한 활성 의료진 계정으로 로그인하세요.</p>
        <form onSubmit={submit} className="mt-8 space-y-5">
          <label className="block text-sm font-semibold text-slate-700">아이디
            <input required autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)}
              className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 outline-none focus:border-blue-500" />
          </label>
          <label className="block text-sm font-semibold text-slate-700">비밀번호
            <input required type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-2 h-12 w-full rounded-xl border border-slate-300 px-4 outline-none focus:border-blue-500" />
          </label>
          {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button disabled={submitting} className="h-12 w-full rounded-xl bg-blue-600 font-bold text-white disabled:bg-blue-300">
            {submitting ? "로그인 중..." : "로그인"}
          </button>
        </form>
        <p className="mt-6 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-800">
          교육·연구용 비임상 PoC입니다. 실제 환자 식별정보를 입력하거나 업로드하지 마세요.
        </p>
      </section>
    </main>
  );
}
