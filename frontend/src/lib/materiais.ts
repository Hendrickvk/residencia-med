import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Material } from "./types";

export function useMateriais(filtros: {
  area_id?: number;
  subtopico_id?: number;
  tipo?: string;
  q?: string;
  pagina: number;
  limite: number;
}) {
  return useQuery({
    queryKey: ["materiais", filtros],
    queryFn: () => api.get<{ total: number; itens: Material[] }>("/materiais", filtros),
  });
}

export function useTiposMateriais() {
  return useQuery({ queryKey: ["materiais-tipos"], queryFn: () => api.get<string[]>("/materiais/tipos") });
}

export function useStatusSincronizacao() {
  return useQuery({
    queryKey: ["sincronizacao-status"],
    queryFn: () => api.get<{ ultima_sincronizacao: string | null }>("/sincronizacao"),
  });
}
