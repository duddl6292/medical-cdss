import { BrowserRouter, Route, Routes } from "react-router-dom";

import MainPage from "./pages/mainpage";
import UploadPage from "./pages/uploadpage";
import ProgressPage from "./pages/progresspage";
import ResultPage from "./pages/resultpage";
import HistoryPage from "./pages/historypage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/progress/:ct_id" element={<ProgressPage />} />
        <Route path="/result/:ct_id" element={<ResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;