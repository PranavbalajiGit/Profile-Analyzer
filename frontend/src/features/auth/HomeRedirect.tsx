import { Navigate } from "react-router-dom";

import { homePathFor } from "../../lib/roles";
import { useAuth } from "./AuthContext";

export function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={homePathFor(user)} replace />;
}
