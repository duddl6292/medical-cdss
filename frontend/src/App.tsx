import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useAuth } from "./contexts/authcontext";
import HistoryPage from "./pages/historypage";
import LoginPage from "./pages/loginpage";
import MainPage from "./pages/mainpage";
import ProgressPage from "./pages/progresspage";
import ResultPage from "./pages/resultpage";
import UploadPage from "./pages/uploadpage";

function ProtectedRoutes() {
  const { loading, user } = useAuth();
  if (loading) return <div className="flex min-h-screen items-center justify-center">사용자 정보를 확인하는 중입니다.</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoutes />}>
        <Route path="/" element={<MainPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/progress/:ctId" element={<ProgressPage />} />
        <Route path="/result/:ctId" element={<ResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
