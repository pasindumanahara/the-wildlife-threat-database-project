import {useEffect, useState} from "react";
import {useNavigate} from "react-router-dom";

export function useDashboardTransition() {
  const navigate = useNavigate();
  const [openingDashboard, setOpeningDashboard] = useState(false);

  useEffect(() => {
    if (!openingDashboard) return;
    const timer = window.setTimeout(() => navigate("/dashboard"), 800);
    return () => window.clearTimeout(timer);
  }, [openingDashboard, navigate]);

  return {openingDashboard, openDashboard: () => setOpeningDashboard(true)};
}
