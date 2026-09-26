// O que mudou na plataforma, para a aluna — não para quem escreve o código.
//
// **Como acrescentar uma entrega:** ponha uma entrada nova no TOPO da lista,
// com `id` na data do deploy (`AAAA-MM-DD`; se sair duas no mesmo dia, um
// sufixo: `2026-09-23b`). O id é o que fica guardado em
// `usuarios.novidades_vistas`, então **id de entrada publicada nunca muda** —
// mudar faz a caixa reaparecer para todo mundo.
//
// **Como escrever:** cada linha diz o que ela ganha, não o que foi
// implementado. "Sair da conta encerra a sessão em todos os aparelhos" e não
// "token_version no JWT". Três a quatro linhas por entrega; o que não couber
// não era novidade para ela, era detalhe nosso. Nada de mudança invisível
// (índice de banco, refatoração) e nada que ela não possa ver na tela.
//
// A caixa aparece sozinha uma vez por entrada, no Painel, e continua
// acessível pelo menu da conta.

export type TipoNovidade = "novo" | "corrigido";

export interface ItemNovidade {
  tipo: TipoNovidade;
  texto: string;
}

export interface Novidade {
  id: string;
  // Já formatada, porque é rótulo e não data para calcular nada em cima.
  data: string;
  titulo: string;
  itens: ItemNovidade[];
}

export const ROTULO_TIPO: Record<TipoNovidade, string> = {
  novo: "Novo",
  corrigido: "Corrigido",
};

export const NOVIDADES: Novidade[] = [
  {
    id: "2026-09-26",
    data: "26 de setembro de 2026",
    titulo: "Lembrete das revisões",
    itens: [
      {
        tipo: "novo",
        texto: "Se quiser, a plataforma avisa por e-mail nos dias em que há revisão vencida. É só ligar em Perfil → Lembretes.",
      },
    ],
  },
  {
    id: "2026-09-25f",
    data: "25 de setembro de 2026",
    titulo: "Ofensiva",
    itens: [
      { tipo: "corrigido", texto: "A ofensiva agora conta os dias em que você só revisou casos ou estudou cartões." },
      { tipo: "novo", texto: "Apagar uma pasta ou um baralho pede confirmação dizendo o que vai junto." },
    ],
  },
  {
    id: "2026-09-25e",
    data: "25 de setembro de 2026",
    titulo: "Resumo da sessão",
    itens: [{ tipo: "corrigido", texto: "No celular, o resumo da sessão mostra de novo o nome de cada especialidade." }],
  },
  {
    id: "2026-09-25d",
    data: "25 de setembro de 2026",
    titulo: "Painel mais direto",
    itens: [
      { tipo: "novo", texto: "O Painel agora mostra logo no começo o que fazer hoje: as revisões, os cartões e o tema que mais rende pontos." },
      { tipo: "novo", texto: "Os gráficos de evolução ficam numa seção que você abre quando quiser, e ela lembra da sua escolha." },
    ],
  },
  {
    id: "2026-09-25c",
    data: "25 de setembro de 2026",
    titulo: "Chute antes de responder",
    itens: [
      {
        tipo: "novo",
        texto: "Em dúvida? Marque \"Estou chutando\" antes de confirmar. Quem sabe a resposta agora só confirma e segue, sem um toque a mais.",
      },
    ],
  },
  {
    id: "2026-09-25b",
    data: "25 de setembro de 2026",
    titulo: "Mais fácil no celular",
    itens: [
      { tipo: "novo", texto: "As abas foram para o pé da tela, ao alcance do polegar, com as revisões e os cartões de hoje à vista." },
      { tipo: "novo", texto: "Numa sessão, confirmar e seguir para o próximo caso ficam sempre no pé da tela, sem rolar a discussão inteira." },
      { tipo: "corrigido", texto: "Cartão com verso comprido não cobre mais os botões, e o baralho não fica cortado dentro da pasta." },
    ],
  },
  {
    id: "2026-09-25",
    data: "25 de setembro de 2026",
    titulo: "Mais cores",
    itens: [
      { tipo: "novo", texto: "Dez cores para o avatar e as pastas, e cada uma abre oito tons quando você toca nela." },
      { tipo: "corrigido", texto: "No celular, a alternativa respondida não fica mais uma palavra por linha." },
      { tipo: "corrigido", texto: "Sumiu do filtro de áreas uma área que não era de verdade." },
    ],
  },
  {
    id: "2026-09-23c",
    data: "23 de setembro de 2026",
    titulo: "Baralhos de cartões",
    itens: [
      { tipo: "novo", texto: "Agora dá para escrever seus próprios flashcards, em pastas e baralhos." },
      { tipo: "novo", texto: "Os cartões voltam nos intervalos certos, com a mesma repetição espaçada dos casos." },
      { tipo: "novo", texto: "Na discussão de um caso, \"Virar cartão\" já traz a conduta correta no verso." },
      { tipo: "novo", texto: "Dá para estudar todos os baralhos de uma vez, corrigir o cartão no meio do estudo e desfazer a última nota." },
    ],
  },
  {
    id: "2026-09-23b",
    data: "23 de setembro de 2026",
    titulo: "Seu perfil",
    itens: [
      { tipo: "novo", texto: "Dá para pôr uma foto, um nome e escolher a cor do seu avatar." },
      { tipo: "novo", texto: "As questões que você marca agora têm onde aparecer, e dá para praticar só elas." },
      { tipo: "novo", texto: "A data da prova virou sua: dá para mudar quando quiser." },
    ],
  },
  {
    id: "2026-09-23",
    data: "23 de setembro de 2026",
    titulo: "Conta e sessão",
    itens: [
      { tipo: "novo", texto: "Conta nova confirma o e-mail antes de começar." },
      { tipo: "novo", texto: "Sair da conta encerra a sessão em todos os aparelhos." },
      {
        tipo: "corrigido",
        texto: "Sessão expirada leva pro login, em vez de dar erro no meio do estudo.",
      },
    ],
  },
];

// A entrada mais recente é a régua: quem já a viu não tem nada pendente.
export const NOVIDADE_ATUAL = NOVIDADES[0]?.id ?? "";

/** As entradas que esta conta ainda não viu, da mais nova para a mais antiga.
 *
 * `visto` nulo é conta que nunca abriu a caixa: mostra só a mais recente, e
 * não o histórico inteiro — a primeira vez não pode ser um muro de texto. */
export function novidadesNaoVistas(visto: string | null | undefined): Novidade[] {
  if (!visto) return NOVIDADES.slice(0, 1);
  const indice = NOVIDADES.findIndex((n) => n.id === visto);
  // Id que não existe mais na lista (entrada removida, ou conta que viu uma
  // versão anterior do arquivo): trata como nunca vista, que é o lado seguro —
  // o outro lado esconderia uma novidade para sempre.
  return indice === -1 ? NOVIDADES.slice(0, 1) : NOVIDADES.slice(0, indice);
}
