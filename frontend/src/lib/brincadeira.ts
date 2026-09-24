// Brincadeira de boas-vindas para uma convidada específica, na primeira vez que
// ela abre a plataforma neste navegador. Aqui fica só a mecânica: o roteiro é
// pessoal, e este arquivo vai inteiro para o navegador de qualquer visitante (e
// o repositório é público). O roteiro vem do servidor, no campo `brincadeira`
// do `/me`, que só a conta com um roteiro gravado recebe — as outras recebem
// `null`. Nunca o escreva de volta aqui; para mudar a piada,
// `scripts/gravar_brincadeira.py`.
const CHAVE = "conduta:brincadeira-boas-vindas";

export function jaViu(): boolean {
  try {
    return localStorage.getItem(CHAVE) === "1";
  } catch {
    return false;
  }
}

export function marcarComoVista() {
  try {
    localStorage.setItem(CHAVE, "1");
  } catch {
    // Navegador sem storage: a sequência aparece de novo um dia. Sem problema.
  }
}

// A brincadeira é uma sessão de terminal: o sistema digita, ela responde, e o
// que ela responde muda o que vem depois.

export interface OpcaoBrincadeira {
  rotulo: string;
  resposta: string[];
}

export type PassoBrincadeira =
  // `efeito` é o que o passo faz no app de verdade quando termina de ser
  // digitado. A piada anuncia e cumpre: é isso que a separa de decoração.
  | { tipo: "fala"; linhas: string[]; efeito?: "tema-escuro" }
  | { tipo: "veredito" }
  | { tipo: "escolha"; linhas: string[]; opcoes: OpcaoBrincadeira[] }
  | {
      tipo: "assinatura";
      linhas: string[];
      rotulo: string;
      aceitos: string[];
      confirmacao: string[];
      // Uma recusa por tentativa errada; esgotadas, o sistema cede.
      recusas: string[][];
      // Recusa sob medida para nomes previsíveis, no lugar da recusa da vez.
      especiais?: { quando: string[]; resposta: string[] }[];
      cedendo: string[];
      resposta: string[];
    };

export interface Brincadeira {
  roteiro: PassoBrincadeira[];
  // Prelúdio da reprise, no lugar da varredura inicial.
  reprise: string[];
}

// Reprise: ela pode rever a sessão pelo menu da conta, e o sistema não finge
// que é a primeira vez. Só o prelúdio troca; daí em diante o roteiro é o mesmo,
// então ela pode escolher outras respostas.
export function roteiroDaReprise({ roteiro, reprise }: Brincadeira): PassoBrincadeira[] {
  return [{ tipo: "fala", linhas: reprise }, ...roteiro.slice(1)];
}

// Compara assinatura sem depender de acento nem de maiúscula.
export function normalizarNome(valor: string): string {
  return valor
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

export const ALERTA = {
  selo: "Alerta do sistema",
  veredito: "Ameaça detectada",
  rodape: "Contenção indisponível.",
  fim: "Entrar",
};
