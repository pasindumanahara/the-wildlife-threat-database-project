import {lazy, Suspense, useCallback, useRef, useState} from "react";
import {LoginPage} from "./pages/LoginPage";
import {SignupPage} from "./pages/SignupPage";
import {DashboardPage} from "./pages/DashboardPage";
import {BrowserRouter, Navigate, Route, Routes} from "react-router-dom";


const Notification = lazy(() => import("./components/animation/alert/Notification"));

function App() {
  const [notice, setNotice] = useState(null);
  const sequence = useRef(0);
  const dismiss = useCallback(() => setNotice(null), []);
  function notify(type, message) {
    setNotice({type, message, id: ++sequence.current});
  }
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage notify={notify} dismiss={dismiss} />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
      <Suspense fallback={null}>
        <Notification notice={notice} onDismiss={dismiss} />
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
