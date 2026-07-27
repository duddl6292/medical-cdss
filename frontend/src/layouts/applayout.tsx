import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getNotifications, getSystemHealth, type DashboardItem } from "../api/dashboard";
import Sidebar from "../components/sidebar";
import { useAuth } from "../contexts/authcontext";

type OpenMenu = "system" | "notifications" | "user" | null;

export default function AppLayout({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);
  const [openMenu, setOpenMenu] = useState<OpenMenu>(null);
  const [notifications, setNotifications] = useState<DashboardItem[]>([]);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      const [noticeResult, healthResult] = await Promise.allSettled([
        getNotifications(),
        getSystemHealth(),
      ]);
      if (!active) return;
      if (noticeResult.status === "fulfilled") setNotifications(noticeResult.value.results);
      setHealthy(healthResult.status === "fulfilled" && healthResult.value.status === "healthy");
    };
    void refresh();
    const timer = window.setInterval(refresh, 10_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setOpenMenu(null);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpenMenu(null);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", escape);
    };
  }, []);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  const toggle = (menu: Exclude<OpenMenu, null>) =>
    setOpenMenu((current) => current === menu ? null : menu);

  return (
    <div className="min-h-screen bg-[#f5f9ff] text-slate-900">
      <header className="sticky top-0 z-40 flex h-[74px] items-center justify-between border-b border-blue-100 bg-white/95 px-5 backdrop-blur-md lg:px-8">
        <Link to="/" className="group flex items-center gap-3" aria-label="대시보드로 이동">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 transition group-hover:bg-blue-100">
            <BrainIcon />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900 lg:text-xl">Medical CDSS</h1>
            <p className="mt-0.5 hidden text-xs font-medium text-slate-500 sm:block">AI Brain CT Analysis</p>
          </div>
        </Link>

        <div ref={menuRef} className="flex items-center gap-2 sm:gap-3">
          <div className="relative hidden md:block">
            <button onClick={() => toggle("system")}
              className={`flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold transition ${healthy ? "border-emerald-100 bg-emerald-50 text-emerald-700" : "border-amber-100 bg-amber-50 text-amber-700"}`}>
              <span className={`h-2 w-2 rounded-full ${healthy ? "bg-emerald-500" : "bg-amber-400"}`} />
              {healthy === null ? "상태 확인 중" : healthy ? "시스템 정상" : "확인 필요"}
            </button>
            {openMenu === "system" && (
              <DropDown className="w-72">
                <MenuTitle title="시스템 상태" description="10초마다 자동 갱신됩니다." />
                {["Django API", "PostgreSQL", "추론 Gateway"].map((name) => (
                  <div key={name} className="flex items-center justify-between px-4 py-3 text-sm">
                    <span className="text-slate-600">{name}</span>
                    <span className={healthy ? "font-bold text-emerald-600" : "font-bold text-amber-600"}>{healthy ? "정상" : "확인 중"}</span>
                  </div>
                ))}
              </DropDown>
            )}
          </div>

          <div className="relative">
            <button onClick={() => toggle("notifications")} aria-label="알림"
              className="relative flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 transition hover:bg-blue-50 hover:text-blue-600">
              <BellIcon />
              {notifications.length > 0 && <span className="absolute right-0 top-0 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white">{notifications.length}</span>}
            </button>
            {openMenu === "notifications" && (
              <DropDown className="right-0 w-[340px]">
                <MenuTitle title="분석 알림" description="최근 변경된 분석 작업입니다." />
                <div className="max-h-80 overflow-y-auto">
                  {notifications.slice(0, 6).map((item) => (
                    <Link key={item.case_id} onClick={() => setOpenMenu(null)}
                      to={item.status === "completed" ? `/result/${item.case_id}` : `/progress/${item.case_id}`}
                      className="block border-t border-slate-100 px-4 py-3 transition hover:bg-blue-50">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-bold text-slate-800">Case #{item.case_id} · {statusText(item.status)}</p>
                        <span className="text-xs text-blue-600">{item.progress}%</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{item.subject_id}</p>
                    </Link>
                  ))}
                  {!notifications.length && <p className="p-6 text-center text-sm text-slate-500">새 알림이 없습니다.</p>}
                </div>
              </DropDown>
            )}
          </div>

          <div className="relative">
            <button onClick={() => toggle("user")}
              className="flex items-center gap-3 rounded-xl border border-transparent px-2 py-1.5 transition hover:border-blue-100 hover:bg-blue-50">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-600"><UserIcon /></span>
              <span className="hidden text-left sm:block">
                <strong className="block max-w-32 truncate text-sm text-slate-800">{user?.name}</strong>
                <small className="block text-xs text-slate-500">{user?.department || user?.role_label}</small>
              </span>
              <ChevronIcon />
            </button>
            {openMenu === "user" && (
              <DropDown className="right-0 w-64">
                <div className="border-b border-slate-100 px-4 py-4">
                  <p className="font-bold text-slate-900">{user?.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{user?.email || user?.username}</p>
                  <span className="mt-2 inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">{user?.role_label}</span>
                </div>
                <Link to="/" onClick={() => setOpenMenu(null)} className="block px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">대시보드</Link>
                <Link to="/upload" onClick={() => setOpenMenu(null)} className="block px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">새 CT 분석</Link>
                <Link to="/history" onClick={() => setOpenMenu(null)} className="block px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">분석 기록</Link>
                <button onClick={handleLogout} className="w-full border-t border-slate-100 px-4 py-3 text-left text-sm font-bold text-red-600 hover:bg-red-50">로그아웃</button>
              </DropDown>
            )}
          </div>
        </div>
      </header>

      <div className="flex min-h-[calc(100vh-74px)]">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-x-hidden px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}

function DropDown({ children, className }: { children: ReactNode; className: string }) {
  return <div className={`absolute top-[calc(100%+10px)] z-50 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-xl shadow-slate-200/70 ${className}`}>{children}</div>;
}

function MenuTitle({ title, description }: { title: string; description: string }) {
  return <div className="bg-[#f8fbff] px-4 py-4"><p className="font-bold text-slate-900">{title}</p><p className="mt-1 text-xs text-slate-500">{description}</p></div>;
}

function statusText(status: DashboardItem["status"]) {
  return { waiting: "대기", processing: "분석 중", completed: "완료", failed: "실패" }[status];
}

function BrainIcon() {
  return <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6"><path d="M9.5 4.5A3 3 0 0 0 5 7v.5A3.5 3.5 0 0 0 4 14a3.5 3.5 0 0 0 5.5 4.5v-14Zm5 0A3 3 0 0 1 19 7v.5a3.5 3.5 0 0 1 1 6.5 3.5 3.5 0 0 1-5.5 4.5v-14Z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>;
}
function BellIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="M6 9a6 6 0 0 1 12 0c0 7 3 7 3 7H3s3 0 3-7Zm4 10h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>; }
function UserIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5"><circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.7" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" stroke="currentColor" strokeWidth="1.7" /></svg>; }
function ChevronIcon() { return <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-slate-400"><path d="m8 10 4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>; }
