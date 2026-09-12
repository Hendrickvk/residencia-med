import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Area, Subtopico } from "./types";

export function useAreas() {
  return useQuery({ queryKey: ["areas"], queryFn: () => api.get<Area[]>("/areas"), staleTime: 60_000 });
}

export function useSubtopicos(areaId: number | undefined) {
  return useQuery({
    queryKey: ["subtopicos", areaId],
    queryFn: () => api.get<Subtopico[]>(`/areas/${areaId}/subtopicos`),
    enabled: areaId !== undefined,
    staleTime: 60_000,
  });
}

export function useBancas() {
  return useQuery({ queryKey: ["bancas"], queryFn: () => api.get<string[]>("/questoes/bancas"), staleTime: 60_000 });
}

export function useAnos() {
  return useQuery({ queryKey: ["anos"], queryFn: () => api.get<number[]>("/questoes/anos"), staleTime: 60_000 });
}
