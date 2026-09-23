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
    id: "2026-09-23",
    data: "23 de setembro de 2026",
    titulo: "Sua conta, mais protegida",
    itens: [
      {
        tipo: "novo",
        texto:
          "Quem cria uma conta agora confirma o e-mail antes de abrir as questões. Quem já estuda aqui não precisa fazer nada.",
      },
      {
        tipo: "novo",
        texto:
          "Sair da conta encerra a sessão em todos os aparelhos, e redefinir a senha derruba quem estiver logado com a antiga.",
      },
      {
        tipo: "corrigido",
        texto:
          "Quando a sessão expira, a plataforma leva você ao login em vez de mostrar um erro de carregamento no meio do estudo.",
      },
    ],
  },
  {
    id: "2026-09-22",
    data: "22 de setembro de 2026",
    titulo: "Endereço próprio",
    itens: [
      {
        tipo: "novo",
        texto:
          "A plataforma passou a morar em qualaconduta.com.br, com conexão segura. Os links antigos continuam funcionando.",
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
