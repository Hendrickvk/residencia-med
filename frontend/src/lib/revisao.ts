import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { AvaliacaoRevisao, LevaRevisao } from "./types";

// `extra`: casos além da meta de hoje ("Revisar mais 10"); a meta não muda.
export function useLevaRevisao(extra = 0) {
  return useQuery({
    queryKey: ["revisao-leva", extra],
    queryFn: () => api.get<LevaRevisao>("/revisao/leva", { extra: extra || undefined }),
    staleTime: Infinity,
    gcTime: 0,
  });
}

// Com `alternativa`, o servidor corrige pelo gabarito: resposta errada vira
// nota 1 seja qual for a `qualidade` enviada (repeticao_espacada.avaliar_revisao).
export function avaliarRevisao(
  questaoId: number,
  dados: { qualidade: number; alternativa?: string; tempo_ms?: number },
) {
  return api.post<AvaliacaoRevisao>(`/revisao/${questaoId}/avaliar`, dados);
}

export function definirMetaRevisao(meta: number) {
  return api.patch<{ meta_revisao_diaria: number }>("/me/meta-revisao", { meta });
}
