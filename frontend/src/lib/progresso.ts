import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { queryClient } from "./queryClient";
import type { Caderneta, CarimboNovo, Loja, Progresso } from "./types";

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

export function useCaderneta() {
  return useQuery({
    queryKey: ["caderneta"],
    queryFn: () => api.get<Caderneta>("/progresso/conquistas"),
  });
}

// Carimbo novo é moeda nova: saldo, loja e vitrine precisam saber.
export function avisarCarimbos() {
  void queryClient.invalidateQueries({ queryKey: ["me"] });
  void queryClient.invalidateQueries({ queryKey: ["loja"] });
  void queryClient.invalidateQueries({ queryKey: ["progresso"] });
}

export async function verificarCarimbos() {
  const { novas } = await api.post<{ novas: CarimboNovo[] }>("/progresso/verificar");
  if (novas.length) {
    avisarCarimbos();
    void queryClient.invalidateQueries({ queryKey: ["caderneta"] });
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
