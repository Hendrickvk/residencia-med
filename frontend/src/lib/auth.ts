import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type { Me } from "./types";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<Me>("/me"),
    retry: false,
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
