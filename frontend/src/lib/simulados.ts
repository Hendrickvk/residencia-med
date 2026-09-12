import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { DesempenhoAreaSimulado, HistoricoSimulado, ItemSimulado, Simulado } from "./types";

export function useHistoricoSimulados() {
  return useQuery({ queryKey: ["simulados-historico"], queryFn: () => api.get<HistoricoSimulado[]>("/simulados") });
}

export function useDisponiveisSimulado(areaId: number | undefined, banca: string | undefined) {
  return useQuery({
    queryKey: ["simulados-disponiveis", areaId, banca],
    queryFn: () => api.get<{ total: number }>("/simulados/disponiveis", { area_id: areaId, banca }),
  });
}

export function useSimulado(id: number | null) {
  return useQuery({
    queryKey: ["simulado", id],
    queryFn: () => api.get<Simulado>(`/simulados/${id}`),
    enabled: id !== null,
  });
}

export function useItensSimulado(id: number | null) {
  // SEM staleTime:Infinity de propósito: este hook é usado tanto durante o
  // simulado (EmAndamento) quanto no resultado (Resultado) com a MESMA
  // queryKey — precisa refetch normal ao montar de novo depois de
  // finalizar, senão o resultado herda o cache de antes de responder
  // qualquer coisa (bug real encontrado testando: item respondido aparecia
  // como "não respondida"). Seguro porque `EmAndamento` deriva seu estado
  // local (`respostasLocais`/`marcadasLocais`) de um `useState` lazy, não
  // de um `useEffect` observando `data` — um refetch em segundo plano não
  // reseta nada em andamento.
  return useQuery({
    queryKey: ["simulado-itens", id],
    queryFn: () => api.get<ItemSimulado[]>(`/simulados/${id}/itens`),
    enabled: id !== null,
  });
}

export function useDesempenhoSimulado(id: number | null) {
  return useQuery({
    queryKey: ["simulado-desempenho", id],
    queryFn: () => api.get<DesempenhoAreaSimulado[]>(`/simulados/${id}/desempenho`),
    enabled: id !== null,
  });
}

export function criarSimulado(dados: {
  area_id?: number;
  banca?: string;
  num_questoes: number;
  tempo_limite_min: number;
}) {
  return api.post<{ id: number }>("/simulados", dados);
}

export function responderSimulado(simuladoId: number, questaoId: number, alternativa: string) {
  return api.post(`/simulados/${simuladoId}/respostas`, { questao_id: questaoId, alternativa });
}

export function finalizarSimulado(simuladoId: number) {
  return api.post(`/simulados/${simuladoId}/finalizar`);
}
