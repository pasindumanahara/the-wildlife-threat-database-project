import {useEffect, useRef, useState} from "react";
import {useNavigate} from "react-router-dom";

export function useDashboardTransition() {
  const navigate = useNavigate();
  const [openingDashboard, setOpeningDashboard] = useState(false);
  const navigationOptions = useRef({replace: true});

  useEffect(() => {
    if (!openingDashboard) return;
    const timer = window.setTimeout(() => navigate("/dashboard", navigationOptions.current), 800);
    return () => window.clearTimeout(timer);
  }, [openingDashboard, navigate]);

  return {openingDashboard, openDashboard: (options = {replace: true}) => {
    navigationOptions.current = options;
    setOpeningDashboard(true);
  }};
}
