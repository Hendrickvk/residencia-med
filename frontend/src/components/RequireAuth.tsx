import { Navigate, Outlet } from "react-router-dom";
import { useMe } from "../lib/auth";

export function RequireAuth() {
  const { data, isLoading, isError } = useMe();

  if (isLoading) {
    // Skeleton com as dimensões finais do shell, não um spinner de tela
    // cheia (REDESIGN.md §5) — evita o "pisca e troca" na primeira carga.
    return (
      <div className="flex min-h-screen bg-canvas">
        <div className="hidden h-full w-rail bg-railbg md:block" />
        <div className="flex-1 p-8">
          <div className="mb-6 h-14 animate-pulse rounded-btn bg-line/40" />
          <div className="h-40 animate-pulse rounded-panel bg-line/40" />
        </div>
      </div>
    );
  }

  if (isError || !data) return <Navigate to="/login" replace />;

  return <Outlet />;
}
