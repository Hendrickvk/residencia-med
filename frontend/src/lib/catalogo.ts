import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Area, Especialidade } from "./types";

export function useAreas() {
  return useQuery({ queryKey: ["areas"], queryFn: () => api.get<Area[]>("/areas"), staleTime: 60_000 });
}

export function useEspecialidades(areaId: number | undefined) {
  return useQuery({
    queryKey: ["especialidades", areaId],
    queryFn: () => api.get<Especialidade[]>(`/areas/${areaId}/especialidades`),
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
