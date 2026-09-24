import { api } from "./api";

// Flashcards escritos pela própria aluna: pasta > baralho > cartão.
//
// As cores são vivas de propósito (pedido do usuário) e mesmo assim **não
// entram na escala de triagem** (DESIGN_TRIAGEM.md §2): t1–t5 significam
// aproveitamento, e uma pasta verde ao lado de uma vermelha seria lida como
// "vou bem nesta, mal naquela". Por isso a paleta fica no arco índigo → ciano,
// mais dois neutros e um marrom: **nenhum verde, nenhum amarelo, nenhum
// laranja, nenhum vermelho puro**, que são justamente os cinco da escala.
//
// As chaves não mudam quando a cor muda (`musgo` virou ciano, `areia` virou
// lavanda): uma pasta já criada continua na mesma vaga.
//
// As classes vão escritas por extenso porque o Tailwind só gera o que acha
// literal no código — `bg-pasta-${cor}` não existiria no CSS.
export const CORES_PASTA = [
  { chave: "carvao", nome: "Carvão", fundo: "bg-pasta-carvao", veu: "bg-pasta-soft-carvao", texto: "text-pasta-on-carvao" },
  { chave: "grafite", nome: "Grafite", fundo: "bg-pasta-grafite", veu: "bg-pasta-soft-grafite", texto: "text-pasta-on-grafite" },
  { chave: "ardosia", nome: "Ardósia", fundo: "bg-pasta-ardosia", veu: "bg-pasta-soft-ardosia", texto: "text-pasta-on-ardosia" },
  { chave: "indigo", nome: "Índigo", fundo: "bg-pasta-indigo", veu: "bg-pasta-soft-indigo", texto: "text-pasta-on-indigo" },
  { chave: "lavanda", nome: "Lavanda", fundo: "bg-pasta-lavanda", veu: "bg-pasta-soft-lavanda", texto: "text-pasta-on-lavanda" },
  { chave: "lilas", nome: "Lilás", fundo: "bg-pasta-lilas", veu: "bg-pasta-soft-lilas", texto: "text-pasta-on-lilas" },
  { chave: "purpura", nome: "Púrpura", fundo: "bg-pasta-purpura", veu: "bg-pasta-soft-purpura", texto: "text-pasta-on-purpura" },
  { chave: "ameixa", nome: "Violeta", fundo: "bg-pasta-ameixa", veu: "bg-pasta-soft-ameixa", texto: "text-pasta-on-ameixa" },
  { chave: "orquidea", nome: "Orquídea", fundo: "bg-pasta-orquidea", veu: "bg-pasta-soft-orquidea", texto: "text-pasta-on-orquidea" },
  { chave: "vinho", nome: "Magenta", fundo: "bg-pasta-vinho", veu: "bg-pasta-soft-vinho", texto: "text-pasta-on-vinho" },
  { chave: "framboesa", nome: "Framboesa", fundo: "bg-pasta-framboesa", veu: "bg-pasta-soft-framboesa", texto: "text-pasta-on-framboesa" },
  { chave: "rosa", nome: "Rosa", fundo: "bg-pasta-rosa", veu: "bg-pasta-soft-rosa", texto: "text-pasta-on-rosa" },
  { chave: "algodao", nome: "Algodão", fundo: "bg-pasta-algodao", veu: "bg-pasta-soft-algodao", texto: "text-pasta-on-algodao" },
  { chave: "ciano", nome: "Ciano", fundo: "bg-pasta-ciano", veu: "bg-pasta-soft-ciano", texto: "text-pasta-on-ciano" },
  { chave: "gelo", nome: "Gelo", fundo: "bg-pasta-gelo", veu: "bg-pasta-soft-gelo", texto: "text-pasta-on-gelo" },
  { chave: "turquesa", nome: "Turquesa", fundo: "bg-pasta-turquesa", veu: "bg-pasta-soft-turquesa", texto: "text-pasta-on-turquesa" },
  { chave: "petroleo", nome: "Petróleo", fundo: "bg-pasta-petroleo", veu: "bg-pasta-soft-petroleo", texto: "text-pasta-on-petroleo" },
  { chave: "oceano", nome: "Oceano", fundo: "bg-pasta-oceano", veu: "bg-pasta-soft-oceano", texto: "text-pasta-on-oceano" },
  { chave: "cafe", nome: "Café", fundo: "bg-pasta-cafe", veu: "bg-pasta-soft-cafe", texto: "text-pasta-on-cafe" },
  { chave: "chocolate", nome: "Chocolate", fundo: "bg-pasta-chocolate", veu: "bg-pasta-soft-chocolate", texto: "text-pasta-on-chocolate" },
] as const;

export const COR_PASTA_PADRAO = "ardosia";

export function fundoDaPasta(chave: string | undefined): string {
  return CORES_PASTA.find((c) => c.chave === chave)?.fundo ?? "bg-pasta-ardosia";
}

/** O tom suave, para o fundo do cartão de baralho. */
export function veuDaPasta(chave: string | undefined): string {
  return CORES_PASTA.find((c) => c.chave === chave)?.veu ?? "bg-pasta-soft-ardosia";
}

/** Texto sobre a cor cheia. Cada cor tem o seu, medido contra 4,5:1 — branco
 *  fixo falharia no ciano, no rosa e nos outros tons claros. */
export function textoDaPasta(chave: string | undefined): string {
  return CORES_PASTA.find((c) => c.chave === chave)?.texto ?? "text-pasta-on-ardosia";
}

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
  api.get<{ pastas: Pasta[]; cores: string[] }>("/cartoes/pastas");

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
