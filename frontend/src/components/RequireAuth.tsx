import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ehNaoAutenticado, useMe } from "../lib/auth";
import { EstadoFalha } from "./EstadoFalha";

export function RequireAuth() {
  const { data, isLoading, isError, error, refetch, isFetching, isPaused } = useMe();
  // Para onde ela ia: o login devolve para lá. É o que faz o link de um
  // e-mail ("Revisar agora", "Desligar o lembrete") funcionar para quem
  // estava com a sessão vencida, em vez de largá-la no Painel.
  const location = useLocation();
  const paraOLogin = (
    <Navigate to="/login" replace state={{ de: location.pathname + location.search + location.hash }} />
  );

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

  // Login só quando o servidor disse que não há sessão. Antes, qualquer erro
  // em /me (ex.: conexão com o banco caída) mandava o aluno para o login.
  if (isError && ehNaoAutenticado(error)) return paraOLogin;

  // Um refetch em segundo plano que falhou mantém os dados de antes: segue a tela.
  if (data) return <Outlet />;

  if (isError || isPaused) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ground px-4">
        <div className="w-full max-w-[520px]">
          <EstadoFalha
            mensagem="Não foi possível falar com o servidor. Sua conta e suas respostas continuam salvas."
            ocupado={isFetching}
            pausado={isPaused}
            onTentarDeNovo={() => void refetch()}
          />
        </div>
      </div>
    );
  }

  return paraOLogin;
}
