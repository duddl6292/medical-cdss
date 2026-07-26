import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";

import Sidebar from "../components/sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

type OpenMenu =
  | "system"
  | "notifications"
  | "user"
  | null;

type NotificationStatus =
  | "completed"
  | "processing"
  | "failed";

type NotificationItem = {
  id: number;
  title: string;
  description: string;
  time: string;
  status: NotificationStatus;
  path: string;
};

const notifications: NotificationItem[] = [
  {
    id: 1,
    title: "CT 분석 완료",
    description:
      "CT-20260724-001 분석이 완료되었습니다.",
    time: "방금 전",
    status: "completed",
    path: "/result/CT-20260724-001",
  },
  {
    id: 2,
    title: "CT 분석 진행 중",
    description:
      "CT-20260724-002 분석이 65% 진행되었습니다.",
    time: "5분 전",
    status: "processing",
    path: "/progress/CT-20260724-002",
  },
  {
    id: 3,
    title: "CT 분석 확인 필요",
    description:
      "CT-20260724-004 분석 중 오류가 발생했습니다.",
    time: "20분 전",
    status: "failed",
    path: "/history",
  },
];

function AppLayout({
  children,
}: AppLayoutProps) {
  const [openMenu, setOpenMenu] =
    useState<OpenMenu>(null);

  const headerMenuRef =
    useRef<HTMLDivElement | null>(null);

  const toggleMenu = (
    menu: Exclude<OpenMenu, null>,
  ) => {
    setOpenMenu((currentMenu) =>
      currentMenu === menu ? null : menu,
    );
  };

  const closeMenu = () => {
    setOpenMenu(null);
  };

  /*
   * 메뉴 바깥쪽을 클릭하거나 Esc를 누르면
   * 열려 있는 드롭다운을 닫습니다.
   */
  useEffect(() => {
    const handleOutsideClick = (
      event: MouseEvent,
    ) => {
      if (
        headerMenuRef.current &&
        !headerMenuRef.current.contains(
          event.target as Node,
        )
      ) {
        closeMenu();
      }
    };

    const handleEscape = (
      event: KeyboardEvent,
    ) => {
      if (event.key === "Escape") {
        closeMenu();
      }
    };

    document.addEventListener(
      "mousedown",
      handleOutsideClick,
    );

    document.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );

      document.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, []);

  const handleLogout = () => {
    closeMenu();

    window.alert(
      "로그아웃 기능은 Django 인증 연결 후 활성화됩니다.",
    );
  };

  return (
    <div className="min-h-screen bg-[#f5f9ff] text-slate-900">
      {/* =====================================================
          상단 헤더
      ====================================================== */}
      <header className="sticky top-0 z-40 flex h-[74px] items-center justify-between border-b border-blue-100 bg-white/95 px-5 backdrop-blur-md lg:px-8">
        {/* 로고 및 서비스명 */}
        <Link
          to="/"
          className="group flex items-center gap-3"
          aria-label="Medical CDSS 대시보드로 이동"
          onClick={closeMenu}
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 transition group-hover:bg-blue-100">
            <BrainLogoIcon />
          </div>

          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900 lg:text-xl">
              Medical CDSS
            </h1>

            <p className="mt-0.5 hidden text-xs font-medium text-slate-500 sm:block">
              AI Brain CT Analysis
            </p>
          </div>
        </Link>

        {/* 오른쪽 사용자 영역 */}
        <div
          ref={headerMenuRef}
          className="flex items-center gap-2 sm:gap-3"
        >
          {/* 시스템 상태 */}
          <div className="relative hidden md:block">
            <button
              type="button"
              onClick={() =>
                toggleMenu("system")
              }
              aria-expanded={
                openMenu === "system"
              }
              className="flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 transition hover:border-emerald-200 hover:bg-emerald-100"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-500" />

              시스템 정상
            </button>

            {openMenu === "system" && (
              <SystemStatusMenu />
            )}
          </div>

          {/* 알림 */}
          <div className="relative">
            <button
              type="button"
              onClick={() =>
                toggleMenu("notifications")
              }
              aria-label="알림 확인"
              aria-expanded={
                openMenu === "notifications"
              }
              className={`relative flex h-10 w-10 items-center justify-center rounded-xl transition ${
                openMenu === "notifications"
                  ? "bg-blue-50 text-blue-600"
                  : "text-slate-500 hover:bg-blue-50 hover:text-blue-600"
              }`}
            >
              <BellIcon />

              <span className="absolute right-0.5 top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white">
                {notifications.length}
              </span>
            </button>

            {openMenu ===
              "notifications" && (
              <NotificationMenu
                onClose={closeMenu}
              />
            )}
          </div>

          {/* 사용자 정보 */}
          <div className="relative">
            <button
              type="button"
              onClick={() =>
                toggleMenu("user")
              }
              aria-expanded={
                openMenu === "user"
              }
              className={`flex items-center gap-3 rounded-xl px-2 py-1.5 text-left transition ${
                openMenu === "user"
                  ? "bg-blue-50"
                  : "hover:bg-blue-50"
              }`}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-blue-100 bg-blue-50 text-blue-600">
                <UserIcon />
              </div>

              <div className="hidden md:block">
                <p className="text-sm font-bold text-slate-800">
                  홍길동
                  <span className="ml-1 font-medium text-slate-500">
                    (의료진)
                  </span>
                </p>

                <p className="mt-0.5 text-xs text-slate-400">
                  신경외과
                </p>
              </div>

              <ChevronDownIcon
                isOpen={openMenu === "user"}
              />
            </button>

            {openMenu === "user" && (
              <UserMenu
                onClose={closeMenu}
                onLogout={handleLogout}
              />
            )}
          </div>
        </div>
      </header>

      {/* =====================================================
          사이드바 + 페이지 본문
      ====================================================== */}
      <div className="flex min-h-[calc(100vh-74px)]">
        <Sidebar />

        <main className="min-w-0 flex-1 overflow-x-hidden">
          <div className="mx-auto w-full max-w-[1680px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

/* ============================================================
   시스템 상태 메뉴
============================================================ */

function SystemStatusMenu() {
  return (
    <section className="absolute right-0 top-12 z-50 w-[290px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-slate-900">
            시스템 상태
          </h2>

          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            정상
          </span>
        </div>

        <p className="mt-1 text-xs text-slate-500">
          주요 서비스의 현재 상태입니다.
        </p>
      </div>

      <div className="space-y-1 p-3">
        <SystemStatusRow
          name="Django API"
          description="백엔드 연동 서버"
          status="연결 준비"
          statusType="waiting"
        />

        <SystemStatusRow
          name="AI 분석 서버"
          description="nnU-Net 추론 서비스"
          status="Online"
          statusType="online"
        />

        <SystemStatusRow
          name="영상 뷰어"
          description="NiiVue 의료영상 뷰어"
          status="Ready"
          statusType="online"
        />
      </div>

      <div className="border-t border-slate-100 bg-slate-50 px-5 py-3 text-xs text-slate-500">
        마지막 확인: 방금 전
      </div>
    </section>
  );
}

type SystemStatusRowProps = {
  name: string;
  description: string;
  status: string;
  statusType: "online" | "waiting";
};

function SystemStatusRow({
  name,
  description,
  status,
  statusType,
}: SystemStatusRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl px-3 py-3 hover:bg-slate-50">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-800">
          {name}
        </p>

        <p className="mt-0.5 text-xs text-slate-400">
          {description}
        </p>
      </div>

      <span
        className={`shrink-0 text-xs font-bold ${
          statusType === "online"
            ? "text-emerald-600"
            : "text-amber-600"
        }`}
      >
        {status}
      </span>
    </div>
  );
}

/* ============================================================
   알림 메뉴
============================================================ */

function NotificationMenu({
  onClose,
}: {
  onClose: () => void;
}) {
  return (
    <section className="absolute right-0 top-12 z-50 w-[350px] max-w-[calc(100vw-32px)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 className="font-bold text-slate-900">
            알림
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            최근 분석 상태를 확인합니다.
          </p>
        </div>

        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600">
          {notifications.length}건
        </span>
      </div>

      <div className="divide-y divide-slate-100">
        {notifications.map(
          (notification) => (
            <Link
              key={notification.id}
              to={notification.path}
              onClick={onClose}
              className="flex gap-3 px-5 py-4 transition hover:bg-blue-50/50"
            >
              <NotificationIcon
                status={
                  notification.status
                }
              />

              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-bold text-slate-800">
                    {notification.title}
                  </p>

                  <span className="shrink-0 text-[11px] text-slate-400">
                    {notification.time}
                  </span>
                </div>

                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {
                    notification.description
                  }
                </p>
              </div>
            </Link>
          ),
        )}
      </div>

      <div className="border-t border-slate-100 p-3">
        <Link
          to="/history"
          onClick={onClose}
          className="block rounded-xl px-4 py-2.5 text-center text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
        >
          모든 분석 기록 보기
        </Link>
      </div>
    </section>
  );
}

function NotificationIcon({
  status,
}: {
  status: NotificationStatus;
}) {
  const style = {
    completed:
      "bg-emerald-50 text-emerald-600",
    processing:
      "bg-blue-50 text-blue-600",
    failed: "bg-red-50 text-red-600",
  };

  return (
    <div
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${style[status]}`}
    >
      {status === "completed" && (
        <CheckIcon />
      )}

      {status === "processing" && (
        <ProgressCircleIcon />
      )}

      {status === "failed" && (
        <WarningIcon />
      )}
    </div>
  );
}

/* ============================================================
   사용자 메뉴
============================================================ */

type UserMenuProps = {
  onClose: () => void;
  onLogout: () => void;
};

function UserMenu({
  onClose,
  onLogout,
}: UserMenuProps) {
  return (
    <section className="absolute right-0 top-14 z-50 w-[250px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-50 text-blue-600">
            <UserIcon />
          </div>

          <div>
            <p className="text-sm font-bold text-slate-900">
              홍길동
            </p>

            <p className="mt-0.5 text-xs text-slate-500">
              신경외과 · 의료진
            </p>
          </div>
        </div>
      </div>

      <nav className="p-2">
        <UserMenuLink
          to="/"
          label="대시보드"
          icon={<DashboardIcon />}
          onClick={onClose}
        />

        <UserMenuLink
          to="/upload"
          label="새 CT 분석"
          icon={<UploadMenuIcon />}
          onClick={onClose}
        />

        <UserMenuLink
          to="/history"
          label="분석 기록"
          icon={<HistoryIcon />}
          onClick={onClose}
        />
      </nav>

      <div className="border-t border-slate-100 p-2">
        <button
          type="button"
          onClick={onLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-red-600 transition hover:bg-red-50"
        >
          <LogoutIcon />
          로그아웃
        </button>
      </div>
    </section>
  );
}

type UserMenuLinkProps = {
  to: string;
  label: string;
  icon: ReactNode;
  onClick: () => void;
};

function UserMenuLink({
  to,
  label,
  icon,
  onClick,
}: UserMenuLinkProps) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-blue-50 hover:text-blue-700"
    >
      <span className="text-slate-400">
        {icon}
      </span>

      {label}
    </Link>
  );
}

/* ============================================================
   헤더 아이콘
============================================================ */

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

function BellIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M10 21h4"
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
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M20 21a8 8 0 0 0-16 0"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />

      <circle
        cx="12"
        cy="7"
        r="4"
        stroke="currentColor"
        strokeWidth="1.7"
      />
    </svg>
  );
}

function ChevronDownIcon({
  isOpen,
}: {
  isOpen: boolean;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={`hidden h-4 w-4 text-slate-400 transition-transform lg:block ${
        isOpen ? "rotate-180" : ""
      }`}
      aria-hidden="true"
    >
      <path
        d="m7 10 5 5 5-5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <circle
        cx="12"
        cy="12"
        r="9"
        stroke="currentColor"
        strokeWidth="1.8"
      />

      <path
        d="m8 12 2.5 2.5L16.5 9"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ProgressCircleIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M12 3a9 9 0 1 0 9 9"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M10.3 4.2 2.8 17.1A2 2 0 0 0 4.5 20h15a2 2 0 0 0 1.7-2.9L13.7 4.2a2 2 0 0 0-3.4 0Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />

      <path
        d="M12 9v4m0 3h.01"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DashboardIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <rect
        x="3"
        y="3"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <rect
        x="14"
        y="3"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <rect
        x="3"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <rect
        x="14"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.7"
      />
    </svg>
  );
}

function UploadMenuIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M12 16V4m0 0L7 9m5-5 5 5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M5 15a4 4 0 0 0 0 8h14a4 4 0 0 0 .4-8"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <rect
        x="5"
        y="4"
        width="14"
        height="16"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />

      <path
        d="M9 9h6M9 13h6M9 17h4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />

      <path
        d="m15 8 4 4-4 4M19 12H9"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default AppLayout;