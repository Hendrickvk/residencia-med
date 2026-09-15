import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Area, Especialidade, Subtopico } from "./types";

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

export function useTemas(areaId: number | undefined, especialidadeId: number | undefined) {
  return useQuery({
    queryKey: ["temas", areaId, especialidadeId],
    queryFn: () => api.get<Subtopico[]>(`/areas/${areaId}/temas`, { especialidade_id: especialidadeId }),
    enabled: areaId !== undefined && especialidadeId !== undefined,
    staleTime: 60_000,
  });
}

export function useBancas() {
  return useQuery({ queryKey: ["bancas"], queryFn: () => api.get<string[]>("/questoes/bancas"), staleTime: 60_000 });
}

export function useAnos() {
  return useQuery({ queryKey: ["anos"], queryFn: () => api.get<number[]>("/questoes/anos"), staleTime: 60_000 });
}

// Lista fixa do servidor (db.TIPOS_PERGUNTA), para o front não repetir os nomes.
export function useTiposPergunta() {
  return useQuery({ queryKey: ["tipos-pergunta"], queryFn: () => api.get<string[]>("/questoes/tipos"), staleTime: 60_000 });
}
