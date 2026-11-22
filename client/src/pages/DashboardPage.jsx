import {useState} from "react";
import {useLocation, useNavigate} from "react-router-dom";
import {logout} from "../services/auth";

export function DashboardPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  async function handleLogout() {
    try {
      await logout();
      navigate("/login", {replace: true});
    } catch (cause) {
      setError(cause.message);
    }
  }

  return (
    <div className="h-screen flex flex-col items-center justify-center gap-3 text-2xl">
      <h1>Dashboard</h1>
      {location.state?.notice && <p className="text-base">{location.state.notice}</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button type="button" onClick={handleLogout} className="rounded-lg bg-twtdbp-crimson px-4 py-2 text-base text-white">Log out</button>
    </div>
  );
}
