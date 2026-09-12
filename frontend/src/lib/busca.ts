import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { ResultadoBusca } from "./types";

export function useBusca(termo: string) {
  const termoLimpo = termo.trim();
  return useQuery({
    queryKey: ["busca", termoLimpo],
    queryFn: () => api.get<ResultadoBusca>("/busca", { q: termoLimpo }),
    enabled: termoLimpo.length >= 2,
    staleTime: 10_000,
  });
}
