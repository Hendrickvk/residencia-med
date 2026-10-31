import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { queryClient } from "./queryClient";
import type { Loja, Progresso } from "./types";

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
