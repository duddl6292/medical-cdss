import { BrowserRouter, Route, Routes } from "react-router-dom";

import MainPage from "./pages/mainpage";
import UploadPage from "./pages/uploadpage";
import ProgressPage from "./pages/progresspage";
import ResultPage from "./pages/resultpage";
import HistoryPage from "./pages/historypage";
import LoginPage from "./pages/loginpage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/progress/:ctId" element={<ProgressPage />} />
        <Route path="/result/:ctId" element={<ResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path='/login' element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;