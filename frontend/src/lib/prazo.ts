import type { PrazoRevisao } from "./types";

// Texto do prazo de revisão: "10 min", "1 dia", "16 dias", "3 meses".
// Só formata — o prazo vem calculado do servidor (repeticao_espacada.prever_prazos).
export function formatarPrazo(prazo: PrazoRevisao): string {
  if ("minutos" in prazo) return `${prazo.minutos} min`;
  const dias = prazo.dias;
  if (dias < 60) return `${dias} dia${dias !== 1 ? "s" : ""}`;
  const meses = Math.round(dias / 30);
  return `${meses} ${meses === 1 ? "mês" : "meses"}`;
}

// Duração estimada de uma revisão: "~12 min", "~1 h 05 min". O tempo por caso
// vem do servidor (mediana do próprio aluno, repeticao_espacada.segundos_por_caso).
export function estimarDuracao(casos: number, segundosPorCaso: number): string {
  const minutos = Math.max(1, Math.round((casos * segundosPorCaso) / 60));
  if (minutos < 60) return `~${minutos} min`;
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto ? `~${horas} h ${String(resto).padStart(2, "0")} min` : `~${horas} h`;
}
