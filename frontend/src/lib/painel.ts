import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { PainelData } from "./types";

export function usePainel() {
  return useQuery({
    queryKey: ["painel"],
    queryFn: () => api.get<PainelData>("/painel"),
    staleTime: 15_000,
  });
}
