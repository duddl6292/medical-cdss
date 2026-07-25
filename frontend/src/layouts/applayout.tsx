import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8">
        <div>
          <h1 className="text-xl font-bold text-slate-800">
            Medical CDSS
          </h1>

          <p className="text-sm text-slate-500">
            AI 기반 뇌 CT 영상 분석 지원 시스템
          </p>
        </div>

        <Link
          to="/"
          className="inline-flex items-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          HOME
        </Link>
      </header>

      <div className="flex">
        <Sidebar />

        <main className="min-w-0 flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;