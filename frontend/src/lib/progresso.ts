import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { queryClient } from "./queryClient";
import type { ConquistaNova, Loja, PaginaConquistas, Progresso } from "./types";

export function useProgresso() {
  return useQuery({
    queryKey: ["progresso"],
    queryFn: () => api.get<Progresso>("/progresso"),
  });
}

export function useLoja() {
  return useQuery({
    queryKey: ["loja"],
    queryFn: () => api.get<Loja>("/progresso/loja"),
  });
}

export function usePaginaConquistas() {
  return useQuery({
    queryKey: ["conquistas"],
    queryFn: () => api.get<PaginaConquistas>("/progresso/conquistas"),
  });
}

// Conquista nova é moeda nova: saldo, loja e vitrine precisam saber.
export function avisarConquistas() {
  void queryClient.invalidateQueries({ queryKey: ["me"] });
  void queryClient.invalidateQueries({ queryKey: ["loja"] });
  void queryClient.invalidateQueries({ queryKey: ["progresso"] });
}

export async function verificarConquistas() {
  const { novas } = await api.post<{ novas: ConquistaNova[] }>("/progresso/verificar");
  if (novas.length) {
    avisarConquistas();
    void queryClient.invalidateQueries({ queryKey: ["conquistas"] });
  }
  return novas;
}

// As duas devolvem a loja inteira: o saldo e o estado de todos os itens mudam. O
// `/me` leva a moldura, o título e o saldo para a barra e o crachá.
function aplicar(loja: Loja) {
  queryClient.setQueryData(["loja"], loja);
  void queryClient.invalidateQueries({ queryKey: ["me"] });
  return loja;
}

export function comprarItem(id: string) {
  return api.post<Loja>(`/progresso/loja/${id}/comprar`).then(aplicar);
}

export function equiparItem(tipo: string, item: string | null) {
  return api.put<Loja>("/progresso/equipar", { tipo, item }).then(aplicar);
}
