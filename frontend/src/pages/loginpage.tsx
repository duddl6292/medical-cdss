import {
  useState,
  type FormEvent,
} from "react";
import {
  Navigate,
  useNavigate,
} from "react-router-dom";

type LoginForm = {
  username: string;
  password: string;
  rememberMe: boolean;
};

type FormErrors = {
  username?: string;
  password?: string;
  submit?: string;
};

function LoginPage() {
  const navigate = useNavigate();

  const [form, setForm] =
    useState<LoginForm>({
      username: "",
      password: "",
      rememberMe: false,
    });

  const [errors, setErrors] =
    useState<FormErrors>({});

  const [isLoading, setIsLoading] =
    useState(false);

  const isAuthenticated =
    localStorage.getItem(
      "medical-cdss-auth",
    ) === "true";

  if (isAuthenticated) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const nextErrors: FormErrors = {};

    if (!form.username.trim()) {
      nextErrors.username =
        "아이디를 입력해 주세요.";
    }

    if (!form.password) {
      nextErrors.password =
        "비밀번호를 입력해 주세요.";
    }

    if (
      Object.keys(nextErrors).length > 0
    ) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    setIsLoading(true);

    try {
      /*
       * Django 인증 API가 연결되기 전까지 사용하는
       * 프론트 테스트용 임시 로그인입니다.
       */
      await new Promise((resolve) => {
        window.setTimeout(resolve, 700);
      });

      const mockUser = {
        id: 1,
        username: form.username,
        name: "홍길동",
        role: "의료진",
        department: "신경외과",
      };

      localStorage.setItem(
        "medical-cdss-auth",
        "true",
      );

      localStorage.setItem(
        "medical-cdss-user",
        JSON.stringify(mockUser),
      );

      if (form.rememberMe) {
        localStorage.setItem(
          "medical-cdss-saved-username",
          form.username,
        );
      } else {
        localStorage.removeItem(
          "medical-cdss-saved-username",
        );
      }

      navigate("/", {
        replace: true,
      });
    } catch {
      setErrors({
        submit:
          "로그인 중 오류가 발생했습니다.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f4f8ff]">
      <div className="grid min-h-screen lg:grid-cols-[minmax(0,1.1fr)_minmax(520px,0.9fr)]">
        {/* 왼쪽 서비스 소개 */}
        <section className="relative hidden overflow-hidden bg-gradient-to-br from-[#0f55d9] via-[#1769ec] to-[#52a8ff] px-12 py-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -left-24 top-32 h-80 w-80 rounded-full bg-white/10 blur-2xl" />

          <div className="absolute -bottom-32 right-0 h-96 w-96 rounded-full bg-blue-200/20 blur-3xl" />

          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 shadow-lg backdrop-blur">
                <BrainLogoIcon />
              </div>

              <div>
                <p className="text-xl font-bold">
                  Medical CDSS
                </p>

                <p className="mt-0.5 text-sm text-blue-100">
                  AI Brain CT Analysis
                </p>
              </div>
            </div>
          </div>

          <div className="relative z-10 max-w-xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-emerald-300" />
              AI Clinical Decision Support
            </span>

            <h1 className="mt-7 text-4xl font-bold leading-[1.35] xl:text-5xl">
              더 빠르고 정확한
              <br />
              뇌 CT 영상 분석
            </h1>

            <p className="mt-6 max-w-lg text-base leading-8 text-blue-50/90">
              AI 기반 병변 분석과 의료영상
              시각화를 통해 의료진의 임상
              의사결정을 지원합니다.
            </p>

            <div className="mt-10 grid max-w-lg grid-cols-3 gap-4">
              <FeatureItem
                value="AI"
                label="병변 탐지"
              />

              <FeatureItem
                value="3D"
                label="NIfTI 뷰어"
              />

              <FeatureItem
                value="CDSS"
                label="판독 지원"
              />
            </div>
          </div>

          <p className="relative z-10 text-xs text-blue-100">
            © 2026 Medical CDSS. All
            rights reserved.
          </p>
        </section>

        {/* 오른쪽 로그인 영역 */}
        <section className="flex items-center justify-center px-5 py-10 sm:px-10 lg:bg-white">
          <div className="w-full max-w-[440px]">
            {/* 모바일 로고 */}
            <div className="mb-10 flex items-center gap-3 lg:hidden">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                <BrainLogoIcon />
              </div>

              <div>
                <p className="text-lg font-bold text-slate-900">
                  Medical CDSS
                </p>

                <p className="text-xs text-slate-500">
                  AI Brain CT Analysis
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm font-bold text-blue-600">
                MEDICAL CDSS
              </p>

              <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                로그인
              </h2>

              <p className="mt-3 text-sm leading-6 text-slate-500">
                의료영상 분석 시스템을
                이용하려면 계정으로 로그인해
                주세요.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-9 space-y-5"
            >
              {/* 아이디 */}
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-sm font-bold text-slate-700"
                >
                  아이디
                </label>

                <div
                  className={`flex items-center rounded-xl border bg-white px-4 transition focus-within:ring-4 ${
                    errors.username
                      ? "border-red-300 focus-within:border-red-400 focus-within:ring-red-50"
                      : "border-slate-200 focus-within:border-blue-500 focus-within:ring-blue-50"
                  }`}
                >
                  <UserIcon />

                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    value={form.username}
                    onChange={(event) => {
                      setForm((current) => ({
                        ...current,
                        username:
                          event.target.value,
                      }));

                      setErrors((current) => ({
                        ...current,
                        username: undefined,
                        submit: undefined,
                      }));
                    }}
                    placeholder="아이디를 입력하세요"
                    className="h-14 min-w-0 flex-1 border-0 bg-transparent px-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
                  />
                </div>

                {errors.username && (
                  <p className="mt-2 text-xs font-medium text-red-500">
                    {errors.username}
                  </p>
                )}
              </div>

              {/* 비밀번호 */}
              <div>
                <label
                  htmlFor="password"
                  className="mb-2 block text-sm font-bold text-slate-700"
                >
                  비밀번호
                </label>

                <div
                  className={`flex items-center rounded-xl border bg-white px-4 transition focus-within:ring-4 ${
                    errors.password
                      ? "border-red-300 focus-within:border-red-400 focus-within:ring-red-50"
                      : "border-slate-200 focus-within:border-blue-500 focus-within:ring-blue-50"
                  }`}
                >
                  <LockIcon />

                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    value={form.password}
                    onChange={(event) => {
                      setForm((current) => ({
                        ...current,
                        password:
                          event.target.value,
                      }));

                      setErrors((current) => ({
                        ...current,
                        password: undefined,
                        submit: undefined,
                      }));
                    }}
                    placeholder="비밀번호를 입력하세요"
                    className="h-14 min-w-0 flex-1 border-0 bg-transparent px-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
                  />
                </div>

                {errors.password && (
                  <p className="mt-2 text-xs font-medium text-red-500">
                    {errors.password}
                  </p>
                )}
              </div>

              {/* 로그인 유지 */}
              <div className="flex items-center justify-between gap-4">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={form.rememberMe}
                    onChange={(event) => {
                      setForm((current) => ({
                        ...current,
                        rememberMe:
                          event.target.checked,
                      }));
                    }}
                    className="h-4 w-4 rounded border-slate-300 accent-blue-600"
                  />

                  아이디 저장
                </label>

                <button
                  type="button"
                  onClick={() => {
                    window.alert(
                      "비밀번호 찾기 기능은 추후 연결됩니다.",
                    );
                  }}
                  className="text-sm font-semibold text-blue-600 transition hover:text-blue-700"
                >
                  비밀번호 찾기
                </button>
              </div>

              {errors.submit && (
                <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
                  {errors.submit}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="flex h-14 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 text-sm font-bold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
              >
                {isLoading ? (
                  <>
                    <LoadingIcon />
                    로그인 중...
                  </>
                ) : (
                  <>
                    로그인
                    <ArrowRightIcon />
                  </>
                )}
              </button>
            </form>

            <div className="mt-7 rounded-xl border border-blue-100 bg-blue-50 px-4 py-4">
              <div className="flex items-start gap-3">
                <ShieldIcon />

                <p className="text-xs leading-5 text-slate-500">
                  본 시스템은 승인된 의료진만
                  사용할 수 있습니다. 계정 정보와
                  환자 의료정보를 안전하게 관리해
                  주세요.
                </p>
              </div>
            </div>

            <p className="mt-8 text-center text-xs text-slate-400">
              계정 발급은 시스템 관리자에게
              문의해 주세요.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

function FeatureItem({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  return (
    <div className="rounded-2xl border border-white/15 bg-white/10 px-4 py-4 backdrop-blur">
      <p className="text-lg font-bold">
        {value}
      </p>

      <p className="mt-1 text-xs text-blue-100">
        {label}
      </p>
    </div>
  );
}

function BrainLogoIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-7 w-7"
      aria-hidden="true"
    >
      <path
        d="M9.2 4.2a3 3 0 0 0-5 2.2v.4A3.3 3.3 0 0 0 3 12.9a3.3 3.3 0 0 0 2.1 5.8 3 3 0 0 0 5.1 1.9V4.2Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M14.8 4.2a3 3 0 0 1 5 2.2v.4a3.3 3.3 0 0 1 1.2 6.1 3.3 3.3 0 0 1-2.1 5.8 3 3 0 0 1-5.1 1.9V4.2Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M7.2 8.2c1.2 0 2 .8 2 2M6.2 15.2c1.4 0 2.4-.8 2.4-2M16.8 8.2c-1.2 0-2 .8-2 2M17.8 15.2c-1.4 0-2.4-.8-2.4-2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5 shrink-0 text-slate-400"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="7"
        r="4"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <path
        d="M4 21a8 8 0 0 1 16 0"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5 shrink-0 text-slate-400"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="10"
        width="14"
        height="10"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <path
        d="M8 10V7a4 4 0 0 1 8 0v3"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="mt-0.5 h-5 w-5 shrink-0 text-blue-600"
      aria-hidden="true"
    >
      <path
        d="M12 3 5 6v5c0 4.7 2.8 8.1 7 10 4.2-1.9 7-5.3 7-10V6l-7-3Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />

      <path
        d="m9 12 2 2 4-4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
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

function LoadingIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5 animate-spin"
      aria-hidden="true"
    >
      <path
        d="M12 3a9 9 0 1 0 9 9"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default LoginPage;