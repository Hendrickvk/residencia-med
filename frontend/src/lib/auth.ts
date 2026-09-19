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

  // Pedido de redefinição: a resposta é sempre a mesma, exista ou não a
  // conta — a tela não tem o que informar além de "olhe o seu e-mail".
  async function pedirRedefinicao(email: string) {
    await api.post("/auth/senha/esqueci", { email });
  }

  // O endpoint já devolve a sessão no cookie, então quem redefine entra
  // direto em vez de voltar para o login digitar a senha que acabou de criar.
  async function redefinirSenha(token: string, senha: string) {
    await api.post("/auth/senha/redefinir", { token, senha });
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  async function sair() {
    await api.post("/auth/logout");
    queryClient.clear();
  }

  return { entrar, cadastrar, pedirRedefinicao, redefinirSenha, sair };
}
