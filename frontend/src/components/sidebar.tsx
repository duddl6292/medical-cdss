import { NavLink } from "react-router-dom";

const menuItems = [
  { label: "대시보드", to: "/", icon: "▦" },
  { label: "CT 분석", to: "/upload", icon: "↥" },
  { label: "분석 기록", to: "/history", icon: "▤" },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-[250px] shrink-0 border-r border-blue-100 bg-white lg:flex lg:flex-col">
      <nav className="flex-1 px-4 py-6">
        <p className="mb-3 px-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Main Menu</p>
        <div className="space-y-2">
          {menuItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}
              className={({ isActive }) => [
                "group flex items-center gap-3 rounded-xl px-4 py-3.5 text-sm font-semibold transition",
                isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50 hover:text-blue-600",
              ].join(" ")}>
              {({ isActive }) => (
                <>
                  <span className={`flex h-9 w-9 items-center justify-center rounded-xl text-lg transition ${isActive ? "bg-blue-600 text-white shadow-sm shadow-blue-200" : "bg-slate-50 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600"}`}>{item.icon}</span>
                  <span>{item.label}</span>
                  {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-blue-600" />}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
      <div className="px-4 pb-5">
        <section className="rounded-2xl border border-blue-100 bg-gradient-to-br from-white to-blue-50 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800">시스템 상태</h2>
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />정상
            </span>
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-500">핵심 서비스의 상태는 상단에서<br />실시간으로 확인할 수 있습니다.</p>
          <div className="mt-4 space-y-2 border-t border-blue-100 pt-4 text-xs">
            <div className="flex justify-between"><span className="text-slate-400">AI 분석 서버</span><span className="font-semibold text-emerald-600">Online</span></div>
            <div className="flex justify-between"><span className="text-slate-400">영상 뷰어</span><span className="font-semibold text-emerald-600">Ready</span></div>
          </div>
        </section>
        <footer className="mt-5 px-2 text-xs leading-5 text-slate-400"><p>© 2026 Medical CDSS</p><p>비임상 연구용 PoC</p></footer>
      </div>
    </aside>
  );
}
