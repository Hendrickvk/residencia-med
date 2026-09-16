// Brincadeira de boas-vindas para uma convidada específica, na primeira vez que
// ela abre a plataforma neste navegador. O e-mail não fica escrito aqui: o
// repositório é público e este arquivo vai inteiro para o navegador de qualquer
// usuário, então guardamos só o SHA-256 dele. Para mudar a piada, edite TELAS.
const HASH_CONVIDADA = "1fdfe32f7ab4082eb40d7cc3925d5096adf40add8fa60fc258eb3e244b218759";
const CHAVE = "conduta:brincadeira-boas-vindas";

export async function ehConvidada(email: string | undefined): Promise<boolean> {
  // `crypto.subtle` só existe em contexto seguro (https ou localhost); sem ele,
  // ninguém vê a brincadeira, o que é o comportamento certo para uma piada.
  if (!email || !window.crypto?.subtle) return false;
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

export interface TelaBrincadeira {
  titulo: string;
  texto: string;
  botao: string;
}

// Três atos: o sistema estranha a visita, a plataforma "atende" a paciente e,
// no fim, cobra a assinatura de um contrato absurdo.
export const TELAS: TelaBrincadeira[] = [
  {
    titulo: "Alerta do sistema",
    texto:
      "Uma conta nova acabou de entrar. Executando verificação de rotina… Usuária identificada. " +
      "Nível de ameaça: elevado, mas só para a média da turma.",
    botao: "Prosseguir",
  },
  {
    titulo: "Triagem automática",
    texto:
      "Paciente do sexo feminino, estudante de medicina, comparece ao serviço acordada — o que já merece " +
      "registro. Queixa principal: “só vou deitar cinco minutinhos”. História: o sono chega sem avisar, de " +
      "preferência logo depois da aula. Ao exame, bom estado geral, corada, lutando contra a própria pálpebra.",
    botao: "Continuar o caso",
  },
  {
    titulo: "Resultados dos exames",
    texto:
      "Vitamina D: 12 ng/mL (valor de referência: sair de casa enquanto ainda é dia). " +
      "Tempo médio de resposta a mensagens: 7 a 10 dias úteis. " +
      "Exposição solar acumulada: indetectável. " +
      "Hemograma normal, para decepção de quem esperava uma desculpa melhor.",
    botao: "Isso aqui é perseguição",
  },
  {
    titulo: "Hipótese diagnóstica",
    texto:
      "Síndrome do Sono Irresistível, associada a deficiência importante de vitamina D. O quadro piora no fim " +
      "da tarde e melhora perto da meia-noite, quando a paciente finalmente acorda para viver. Prognóstico " +
      "excelente, desde que a prova não seja às sete da manhã.",
    botao: "Aceito o diagnóstico",
  },
  {
    titulo: "Conduta proposta",
    texto:
      "1. Dormir à noite. " +
      "2. Quinze minutos de sol por dia; ele não morde. " +
      "3. Responder mensagens ainda na semana em que foram enviadas. " +
      "4. Estudar por aqui, que sai mais barato que terapia.",
    botao: "Vou pensar no caso",
  },
  {
    titulo: "Termos de uso, edição especial",
    texto:
      "Cláusula 1: a plataforma não se responsabiliza por sessões interrompidas por sono. " +
      "Cláusula 2: “cinco minutinhos” não é unidade de tempo reconhecida aqui. " +
      "Cláusula 3: estudar deitada é permitido, mas o resultado é previsível. " +
      "Cláusula 4: seus horários de acesso ficam registrados e podem ser usados numa conversa futura.",
    botao: "Aceito sem ler",
  },
  {
    titulo: "Cadastro concluído",
    texto:
      "Bem-vinda, Giovanna. O resto é com você — e, sim, o cronômetro do simulado continua correndo mesmo se " +
      "você cochilar.",
    botao: "Começar",
  },
];
