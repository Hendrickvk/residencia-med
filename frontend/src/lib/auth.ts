import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "./api";
import type { Me } from "./types";

// Só 401 significa "sem sessão". Erro 5xx ou de rede é o servidor com
// problema, e não pode tirar o aluno da conta.
export function ehNaoAutenticado(erro: unknown) {
  return erro instanceof ApiError && erro.status === 401;
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<Me>("/me"),
    retry: (falhas, erro) => !ehNaoAutenticado(erro) && falhas < 2,
    staleTime: 30_000,
  });
}

export function useAuthActions() {
  const queryClient = useQueryClient();

  async function entrar(email: string, senha: string) {
    await api.post("/auth/login", { email, senha });
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function cadastrar(email: string, senha: string) {
    await api.post("/auth/signup", { email, senha });
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function sair() {
    await api.post("/auth/logout");
    queryClient.clear();
  }

  return { entrar, cadastrar, sair };
}
