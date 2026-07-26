import { NavLink } from "react-router-dom";

type MenuItem = {
  label: string;
  to: string;
  icon: React.ReactNode;
};

const menuItems: MenuItem[] = [
  {
    label: "대시보드",
    to: "/",
    icon: <DashboardIcon />,
  },
  {
    label: "CT 분석",
    to: "/upload",
    icon: <UploadIcon />,
  },
  {
    label: "분석 기록",
    to: "/history",
    icon: <HistoryIcon />,
  },
];

function Sidebar() {
  return (
    <aside className="hidden w-[250px] shrink-0 border-r border-blue-100 bg-white lg:flex lg:flex-col">
      {/* 메뉴 영역 */}
      <nav className="flex-1 px-4 py-6">
        <p className="mb-3 px-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
          Main Menu
        </p>

        <div className="space-y-2">
          {menuItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "group flex items-center gap-3 rounded-xl px-4 py-3.5",
                  "text-sm font-semibold transition",
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-blue-600",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={[
                      "flex h-9 w-9 items-center justify-center rounded-xl transition",
                      isActive
                        ? "bg-blue-600 text-white shadow-sm shadow-blue-200"
                        : "bg-slate-50 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600",
                    ].join(" ")}
                  >
                    {item.icon}
                  </span>

                  <span>{item.label}</span>

                  {isActive && (
                    <span className="ml-auto h-2 w-2 rounded-full bg-blue-600" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* 시스템 상태 */}
      <div className="px-4 pb-5">
        <section className="rounded-2xl border border-blue-100 bg-gradient-to-br from-white to-blue-50 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800">
              시스템 상태
            </h2>

            <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              정상
            </span>
          </div>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            모든 시스템이 정상적으로
            <br />
            운영 중입니다.
          </p>

          <div className="mt-4 border-t border-blue-100 pt-4">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">AI 분석 서버</span>

              <span className="font-semibold text-emerald-600">
                Online
              </span>
            </div>

            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-slate-400">영상 뷰어</span>

              <span className="font-semibold text-emerald-600">
                Ready
              </span>
            </div>
          </div>
        </section>

        <footer className="mt-5 px-2 text-xs leading-5 text-slate-400">
          <p>© 2026 Medical CDSS</p>
          <p>All rights reserved.</p>
        </footer>
      </div>
    </aside>
  );
}

/* ============================================================
   메뉴 아이콘
============================================================ */

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
        strokeWidth="1.8"
      />

      <rect
        x="14"
        y="3"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />

      <rect
        x="3"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />

      <rect
        x="14"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        d="M12 16V4"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />

      <path
        d="m7 9 5-5 5 5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M5 14.5a4 4 0 0 0 0 8h14a4 4 0 0 0 .4-8"
        stroke="currentColor"
        strokeWidth="1.8"
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
      <path
        d="M9 5H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M9 3h6v4H9z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />

      <path
        d="M8 12h8M8 16h5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default Sidebar;