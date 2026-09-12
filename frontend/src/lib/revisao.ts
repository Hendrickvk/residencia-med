import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { LevaRevisao } from "./types";

export function useLevaRevisao() {
  return useQuery({
    queryKey: ["revisao-leva"],
    queryFn: () => api.get<LevaRevisao>("/revisao/leva"),
    staleTime: Infinity,
    gcTime: 0,
  });
}

export function avaliarRevisao(questaoId: number, qualidade: number) {
  return api.post(`/revisao/${questaoId}/avaliar`, { qualidade });
}
