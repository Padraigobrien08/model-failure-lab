import { Navigate, useLocation } from "react-router-dom";

export function FailureExplorerPage() {
  const location = useLocation();

  return <Navigate replace to={`/lanes${location.search}`} />;
}
