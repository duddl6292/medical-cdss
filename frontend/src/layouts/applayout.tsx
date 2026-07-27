import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { getNotifications, getSystemHealth } from "../api/dashboard";
import Sidebar from "../components/sidebar";
import { useAuth } from "../contexts/authcontext";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [notificationCount, setNotificationCount] = useState(0);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      const [notifications, health] = await Promise.allSettled([
        getNotifications(),
        getSystemHealth(),
      ]);
      if (!active) return;
      if (notifications.status === "fulfilled") setNotificationCount(notifications.value.count);
      if (health.status === "fulfilled") setHealthy(health.value.status === "healthy");
      else setHealthy(false);
    };
    void refresh();
    const timer = window.setInterval(refresh, 10_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-[#f5f8fc]">
      <Sidebar />
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white px-5 lg:px-8">
          <div>
            <p className="text-xs font-bold text-blue-600">MEDICAL CDSS · 비임상 PoC</p>
            <p className="mt-1 text-sm text-slate-500">
              <span className={`mr-2 inline-block h-2 w-2 rounded-full ${healthy ? "bg-emerald-500" : "bg-amber-400"}`} />
              {healthy === null ? "상태 확인 중" : healthy ? "API 및 데이터베이스 정상" : "시스템 확인 필요"}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">알림 {notificationCount}</span>
            <div className="hidden text-right sm:block">
              <p className="text-sm font-bold text-slate-800">{user?.name}</p>
              <p className="text-xs text-slate-500">{user?.department || user?.role}</p>
            </div>
            <button onClick={handleLogout} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              로그아웃
            </button>
          </div>
        </header>
        <main className="p-5 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
