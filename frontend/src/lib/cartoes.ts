import { api } from "./api";

// Flashcards escritos pela própria aluna: pasta > baralho > cartão.
//
// A cor da pasta vem da paleta compartilhada com o avatar (`lib/paleta.ts`,
// contexto "pasta"): cor cheia no banner, véu no cartão de baralho.

export interface BaralhoResumo {
  id: number;
  pasta_id: number;
  nome: string;
  criado_em: string;
  cartoes: number;
  vencidos: number;
  // Estágios, com a mesma definição da Revisão de casos
  // (repeticao_espacada.INTERVALO_CONSOLIDADO_DIAS): novo é o que nunca foi
  // visto, consolidado é intervalo de 21 dias ou mais.
  novos: number;
  aprendendo: number;
  consolidados: number;
}

export interface Pasta {
  id: number;
  nome: string;
  cor: string;
  criada_em: string;
  baralhos: BaralhoResumo[];
}

export interface Cartao {
  id: number;
  frente: string;
  verso: string;
  proxima_revisao: string | null;
  repeticoes: number | null;
}

// Prazo que cada nota agendaria, vindo do servidor: a mesma conta que grava.
export type PrazoCartao = { minutos: number } | { dias: number };
export interface CartaoEstudo {
  id: number;
  frente: string;
  verso: string;
  prazos: Record<string, PrazoCartao>;
  // De qual baralho o cartão veio: numa sessão que atravessa baralhos, é isso
  // que diz onde ela está.
  baralho: string;
  baralho_id: number;
  cor: string;
}

export const listarPastas = () =>
  api.get<{ pastas: Pasta[] }>("/cartoes/pastas");

export const criarPasta = (nome: string, cor: string) =>
  api.post<{ id: number }>("/cartoes/pastas", { nome, cor });

export const atualizarPasta = (id: number, nome: string, cor: string) =>
  api.patch(`/cartoes/pastas/${id}`, { nome, cor });

export const excluirPasta = (id: number) => api.delete(`/cartoes/pastas/${id}`);

export const criarBaralho = (pastaId: number, nome: string) =>
  api.post<{ id: number }>("/cartoes/baralhos", { pasta_id: pastaId, nome });

export const renomearBaralho = (id: number, nome: string) =>
  api.patch(`/cartoes/baralhos/${id}`, { nome });

export const excluirBaralho = (id: number) => api.delete(`/cartoes/baralhos/${id}`);

export const obterBaralho = (id: number) =>
  api.get<{
    baralho: { id: number; pasta_id: number; nome: string; pasta: string; cor: string };
    cartoes: Cartao[];
  }>(`/cartoes/baralhos/${id}`);

export const criarCartao = (baralhoId: number, frente: string, verso: string, questaoId?: number) =>
  api.post<{ id: number }>("/cartoes", {
    baralho_id: baralhoId, frente, verso, questao_id: questaoId ?? null,
  });

export const moverBaralho = (id: number, pastaId: number, nome: string) =>
  api.patch(`/cartoes/baralhos/${id}`, { nome, pasta_id: pastaId });

export const atualizarCartao = (id: number, frente: string, verso: string) =>
  api.patch(`/cartoes/${id}`, { frente, verso });

export const excluirCartao = (id: number) => api.delete(`/cartoes/${id}`);

/** `baralhoId` nulo = fila do dia atravessando todos os baralhos. */
export const cartoesParaEstudar = (baralhoId: number | null) =>
  api.get<{ cartoes: CartaoEstudo[] }>(
    baralhoId === null ? "/cartoes/estudar" : `/cartoes/baralhos/${baralhoId}/estudar`,
  );

export const desfazerCartao = (id: number) => api.post(`/cartoes/${id}/desfazer`);

export const avaliarCartao = (id: number, qualidade: number) =>
  api.post<{ proxima_revisao: string; intervalo_dias: number }>(`/cartoes/${id}/avaliar`, { qualidade });

/** "10 min", "6 dias" — o rótulo embaixo de cada botão de nota. */
export function textoPrazo(prazo: PrazoCartao | undefined): string {
  if (!prazo) return "";
  if ("minutos" in prazo) return `${prazo.minutos} min`;
  return `${prazo.dias} dia${prazo.dias !== 1 ? "s" : ""}`;
}

/** "1 cartão" / "4 cartões". Existe porque o plural de "cartão" não se forma
 *  trocando a última letra, e a interpolação ingênua escrevia "cartãos". */
export function plural(n: number): string {
  return `${n} ${n === 1 ? "cartão" : "cartões"}`;
}
