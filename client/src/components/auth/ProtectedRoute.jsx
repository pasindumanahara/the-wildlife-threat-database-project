import {useEffect, useState} from "react";
import {Navigate} from "react-router-dom";
import {currentUser} from "../../services/auth";

export function ProtectedRoute({children}) {
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    let active = true;
    currentUser().then((result) => {
      if (active) setUser(result);
    }).catch(() => {
      if (active) setUser(null);
    });
    return () => { active = false; };
  }, []);

  if (user === undefined) return <p className="p-8">Loading...</p>;
  return user ? children : <Navigate to="/login" replace />;
}
