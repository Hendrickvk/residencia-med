import { Navigate, Outlet } from "react-router-dom";
import { useMe } from "../lib/auth";

export function RequireAuth() {
  const { data, isLoading, isError } = useMe();

  if (isLoading) {
    // Skeleton com as dimensões finais do shell (barra superior de 64px +
    // conteúdo), não um spinner de tela cheia — evita o "pisca e troca" na
    // primeira carga.
    return (
      <div className="min-h-screen bg-ground">
        <div className="h-16 border-b border-line bg-surface" />
        <div className="mx-auto flex max-w-[1360px] flex-col gap-7 px-4 py-6 md:px-10 md:py-9">
          <div className="h-[150px] animate-pulse rounded-card bg-line-soft" />
          <div className="h-[300px] animate-pulse rounded-card bg-line-soft" />
        </div>
      </div>
    );
  }

  if (isError || !data) return <Navigate to="/login" replace />;

  return <Outlet />;
}
