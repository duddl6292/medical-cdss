import { NavLink } from "react-router-dom";

function Sidebar() {
  const menuClass = ({ isActive }: { isActive: boolean }) =>
    `block w-full rounded-lg px-4 py-3 text-sm font-medium transition ${
      isActive
        ? "bg-blue-600 text-white"
        : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <aside className="min-h-[calc(100vh-64px)] w-64 border-r border-slate-200 bg-white p-5">
      <nav className="space-y-2">
        <NavLink to="/" end className={menuClass}>
          대시보드
        </NavLink>

        <NavLink to="/upload" className={menuClass}>
          CT 분석
        </NavLink>

        <NavLink to="/history" className={menuClass}>
          분석 기록
        </NavLink>
      </nav>
    </aside>
  );
}

export default Sidebar;