import { useEffect, useState } from "react";

// Brincadeira de boas-vindas para uma convidada específica, na primeira vez que
// ela abre a plataforma neste navegador. O e-mail não fica escrito aqui: o
// repositório é público e este arquivo vai inteiro para o navegador de qualquer
// usuário, então guardamos só o SHA-256 dele. Para mudar a piada, edite o
// ROTEIRO (e o ROTEIRO_REPRISE, que só troca o prelúdio).
const HASH_CONVIDADA = "1fdfe32f7ab4082eb40d7cc3925d5096adf40add8fa60fc258eb3e244b218759";
const CHAVE = "conduta:brincadeira-boas-vindas";

export async function ehConvidada(email: string | undefined): Promise<boolean> {
  // Em desenvolvimento, `?brincadeira=1` força a sessão. Existe porque testar
  // no celular pela rede local (http://<ip>:5173) não é contexto seguro, e sem
  // `crypto.subtle` a verificação sempre diz não. `import.meta.env.DEV` é
  // eliminado no build, então isto não existe em produção.
  if (import.meta.env.DEV && new URLSearchParams(location.search).has("brincadeira")) return true;
  // `crypto.subtle` só existe em contexto seguro (https ou localhost); sem ele,
  // ninguém vê a brincadeira, o que é o comportamento certo para uma piada —
  // mas falhar calado seria pior, porque a estreia dela acontece uma vez só.
  if (!window.crypto?.subtle) {
    console.warn("[conduta] sem crypto.subtle (contexto não seguro): a brincadeira não roda aqui.");
    return false;
  }
  if (!email) return false;
  const bytes = new TextEncoder().encode(email.trim().toLowerCase());
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  const hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return hex === HASH_CONVIDADA;
}

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
// que ela responde muda o que vem depois. Registro de máquina de propósito —
// minúscula, frase curta, campo e valor. Um log não faz comparação literária,
// e foi isso que tirou o texto do tom de redação.
//
// Regras de tom: nada de explicar referência (o rádio é Silent Hill, os quinze
// rounds são o Rocky), nada de elogio direto, e o flerte fica nas respostas do
// passo do prontuário — que é ela quem escolhe abrir. Este
// arquivo é público e vai inteiro para o navegador de qualquer usuário: nada
// aqui pode virar problema se for lido fora de contexto, por isso não há
// medida do corpo dela nem registro de horário de acesso.

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

// Compara assinatura sem depender de acento nem de maiúscula.
export function normalizarNome(valor: string): string {
  return valor
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export const ALERTA = {
  selo: "Alerta do sistema",
  veredito: "Ameaça detectada",
  rodape: "Contenção indisponível.",
  fim: "Entrar",
};

// Os detalhes dela (kinder bueno, crocs, preto, altura, rocky) não são enfeite:
// são o recado inteiro — alguém prestou atenção. Por isso cada um entra como
// coisa que o sistema *notou* e tirou conclusão, e nunca como item de lista:
// kinder bueno é prescrição, os crocs são EPI, o preto é o tema da interface se
// ajustando a ela, e o Rocky aparece pelo que ela faz com o filme, não por
// contagem de rounds. Detalhe listado soa encaixado à força; detalhe com
// consequência soa notado.
//
// `{nome}` é trocado pelo que ela assinar.
export const ROTEIRO: PassoBrincadeira[] = [
  {
    tipo: "fala",
    linhas: [
      "conexão nova no sistema.",
      "varredura de rotina em andamento…",
      "assinatura não reconhecida.",
      "cruzando com a base de casos.",
      "correspondência encontrada: giovanna.",
    ],
  },
  { tipo: "veredito" },
  {
    tipo: "escolha",
    linhas: ["> declare sua intenção neste sistema."],
    opcoes: [
      { rotulo: "vim estudar", resposta: ["> improvável.", "> registrado de todo jeito."] },
      { rotulo: "que ameaça?", resposta: ["> você.", "> chegaremos lá."] },
      {
        rotulo: "(não responder)",
        resposta: [
          "> silêncio registrado.",
          "> média histórica: 7 a 10 dias úteis.",
          "> prosseguindo sem a sua colaboração.",
        ],
      },
    ],
  },
  // Passo próprio para a linha do tema: assim a tela escurece no instante em
  // que a frase termina, e não quatro linhas depois. No primeiro acesso dela o
  // app está no tema claro, então a mudança é visível de verdade.
  {
    tipo: "fala",
    linhas: ["> ajustando a interface para preto. suposição segura."],
    efeito: "tema-escuro",
  },
  {
    tipo: "fala",
    linhas: [
      "> abrindo prontuário.",
      "> sono: 14 horas por dia, sob protesto.",
      "> resposta a mensagens: 7 a 10 dias úteis.",
      "> vitamina d: 12. sol: nunca.",
      "> dieta: a parmegiana de berinjela da sua mãe.",
      "> nada que este sistema prescreva compete com isso.",
    ],
  },
  {
    tipo: "escolha",
    linhas: ["> confirme o horário em que você considera manhã."],
    opcoes: [
      { rotulo: "06:00", resposta: ["> mentira detectada.", "> corrigindo para 14:00."] },
      { rotulo: "11:00", resposta: ["> arredondado para 14:00."] },
      { rotulo: "14:00", resposta: ["> obrigado pela honestidade."] },
    ],
  },
  {
    tipo: "fala",
    linhas: [
      "> exame físico dispensado.",
      "> epi: crocs. altura declarada: 1,73 m, com eles.",
      "> temperamento: difícil.",
      "> já sabe o final do rocky e ainda torce.",
      "> psiquiatria pretendida. ironia registrada.",
    ],
  },
  // A pergunta que o próprio conteúdo provoca: ela acabou de ler quatro
  // detalhes que só alguém que presta atenção saberia. Pedir que ela nomeasse
  // "o responsável pelo caso" era enigma armado — sistema nenhum pergunta isso
  // ao paciente. Aqui o sistema só aponta o óbvio e deixa a curiosidade ser
  // dela, que é o que faz a resposta chegar sem forçar.
  {
    tipo: "escolha",
    linhas: ["> este prontuário não foi preenchido pelo sistema.", "> quer saber por quem?"],
    opcoes: [
      { rotulo: "já sei", resposta: ["> imaginei.", "> ele também."] },
      {
        rotulo: "quero",
        resposta: ["> quem fez esse sistema.", "> levou um tempo escolhendo o que anotar."],
      },
      { rotulo: "não muda nada", resposta: ["> muda para quem preencheu."] },
    ],
  },
  {
    tipo: "fala",
    linhas: [
      "> conduta proposta:",
      ">   1. dormir à noite.",
      ">   2. quinze minutos de sol por dia.",
      ">   3. responder na mesma semana.",
      ">   4. estudar por aqui, que sai mais barato que terapia.",
      ">   5. em caso de crise: kinder bueno. dois.",
    ],
  },
  {
    tipo: "escolha",
    linhas: ["> aceita o tratamento?"],
    opcoes: [
      { rotulo: "aceito", resposta: ["> registrado."] },
      { rotulo: "aceito sem ler", resposta: ["> resposta esperada.", "> registrado."] },
      {
        rotulo: "não",
        resposta: ["> resposta inválida.", "> o sistema vai insistir.", "> registrado como aceite."],
      },
    ],
  },
  {
    tipo: "assinatura",
    linhas: ["> falta a assinatura do termo.", "> assine com o seu nome para liberar o acesso."],
    rotulo: "assinatura",
    // Ela vai testar o campo antes de assinar de verdade — é o tipo dela. O
    // apelido vale, e o sistema recusa duas vezes antes de ceder, porque
    // insistir e ser recusada é justamente a brincadeira que ela gosta de
    // fazer. Ceder na terceira evita que alguém fique preso no campo.
    aceitos: ["giovanna", "giovana", "gi", "giovanna romano", "giovana romano", "giovannaromano"],
    confirmacao: ["> assinatura confere."],
    recusas: [
      ["> não confere.", "> assine com o seu nome."],
      ["> ainda não.", "> o sistema soube quem você era antes de você digitar."],
    ],
    // Ela vai testar assinando com o nome dele. O sistema recusa tratando o
    // assunto como coisa já resolvida, que é o jeito de dizer sem dizer.
    especiais: [
      {
        quando: ["hendrick", "hendrik", "hendrickvk"],
        resposta: ["> não.", "> o termo pede a sua assinatura, não a do seu amor."],
      },
      // Aceita, começa a liberar e só então se corrige. A linha com reticências
      // existe para dar o tempo de respiro: sem ela a desistência chega junto
      // com o aceite e a piada não acontece.
      {
        quando: ["sabrina"],
        resposta: [
          "> assinatura confere.",
          "> liberando acesso.",
          "> …",
          "> espere.",
          "> você não é a sabrina.",
          "> anotação corrigida. assine com o seu nome.",
        ],
      },
    ],
    cedendo: ["> teimosia registrada.", "> liberando de todo jeito. ficou anotado."],
    resposta: [
      "> bem-vinda, {nome}.",
      "> lembre-se: se você dormir, o cronômetro do simulado continua rodando.",
    ],
  },
];

// Reprise: ela pode rever a sessão pelo menu da conta, e o sistema não finge
// que é a primeira vez. O prelúdio troca a varredura inicial — reconhecer a
// visita é mais engraçado do que "assinatura não reconhecida" outra vez — e
// daí em diante o roteiro é o mesmo, então ela pode escolher outras respostas.
export const LINHAS_REPRISE = [
  "conexão conhecida.",
  "giovanna. de novo.",
  "oh, alguém gostou, então?",
  "devia ter cobrado.",
  "pelo menos um beijo.",
];

export const ROTEIRO_REPRISE: PassoBrincadeira[] = [
  { tipo: "fala", linhas: LINHAS_REPRISE },
  ...ROTEIRO.slice(1),
];

// A verificação é assíncrona (SHA-256), então quem precisa dela espera um
// `undefined` antes da resposta. Fica aqui para a barra superior e o invólucro
// usarem o mesmo julgamento.
export function useEhConvidada(email: string | undefined): boolean | undefined {
  const [convidada, setConvidada] = useState<boolean | undefined>(undefined);
  useEffect(() => {
    if (!email) return;
    let cancelado = false;
    ehConvidada(email)
      .then((sim) => {
        if (!cancelado) setConvidada(sim);
      })
      .catch(() => {
        if (!cancelado) setConvidada(false);
      });
    return () => {
      cancelado = true;
    };
  }, [email]);
  return convidada;
}
