import type { FiltrosPratica, Questao, RespostaPayload, ResumoSessao } from "./types";

// Uma sessão de prática só existia na memória da aba: fechar o navegador no
// meio de 10 casos perdia a fila e o resumo. As respostas já dadas não se
// perdem (vão para o servidor pela `respostasQueue` conforme ela responde) —
// o que se perdia era o lugar onde ela estava.
//
// O lote inteiro vai para o `localStorage` porque `/praticar/sessao` sorteia as
// questões: pedir de novo com os mesmos filtros devolveria outras. São ~4 KB
// por caso, longe do limite de 5 MB até numa sessão de 100.
const CHAVE = "residencia-med:sessao-pratica";

// Depois disso a sessão não é mais "a de agora" — retomar uma prática de
// ontem só confunde. É o mesmo raciocínio da meta diária da revisão.
const VALIDADE_MS = 12 * 60 * 60 * 1000;

export interface SessaoSalva {
  versao: 1;
  salvoEm: number;
  // O navegador é o mesmo para as duas contas que o admin usa (a dele e a de
  // QA): sem o e-mail, a sessão de uma apareceria para a outra.
  email: string;
  filtros: FiltrosPratica;
  questoes: Questao[];
  idx: number;
  respondidas: ResumoSessao["respondidas"];
  resultados: boolean[];
  marcadas: number[];
  // Tempo já gasto, para o cronômetro do resumo não recomeçar do zero.
  duracaoMs: number;
  // Identifica a sessão no `envio` de cada resposta. Sessão salva antes de existir
  // este campo recebe um ao ser lida.
  sessaoId?: string;
  // O caso da vez, como estava. Sem isto a retomada voltava ao caso sem alternativa, sem
  // chute e sem discussão, e o tempo medido recomeçava.
  caso?: CasoEmAndamento;
}

export interface CasoEmAndamento {
  selecionada: string | null;
  confirmado: boolean;
  chutando: boolean;
  decorridoMs: number;
}

const CASO_VAZIO: CasoEmAndamento = { selecionada: null, confirmado: false, chutando: false, decorridoMs: 0 };

/** O mesmo caso da mesma sessão tem sempre o mesmo `envio`: registrá-lo duas vezes (a aba
 * caiu logo depois de ir para a fila) não grava duas (`envios_processados`). */
export function envioDoCaso(sessaoId: string, questaoId: number, idx: number) {
  return `${sessaoId}:${questaoId}:${idx}`;
}

/** A resposta que está na tela e ainda não foi gravada: ela é gravada ao passar para o
 * próximo caso, para o tempo incluir a leitura da discussão. Quem descarta a sessão ou
 * começa outra já viu o gabarito, e essa resposta não pode sumir. */
export function respostaPendente(s: SessaoSalva): { envio: string; payload: RespostaPayload } | null {
  const q = s.questoes[s.idx];
  const c = s.caso;
  if (!q || !c?.confirmado || !c.selecionada || !s.sessaoId) return null;
  const correta = c.selecionada === q.resposta_correta;
  return {
    envio: envioDoCaso(s.sessaoId, q.id, s.idx),
    payload: {
      questao_id: q.id,
      alternativa: c.selecionada,
      confianca: c.chutando ? "chute" : correta ? "seguro" : undefined,
      tempo_ms: c.decorridoMs,
    },
  };
}

export function salvarSessao(dados: Omit<SessaoSalva, "versao" | "salvoEm">) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ ...dados, versao: 1, salvoEm: Date.now() }));
  } catch {
    // Cota cheia ou armazenamento bloqueado (aba privada): a sessão continua
    // funcionando, só não sobrevive ao fechamento.
  }
}

export function lerSessao(): SessaoSalva | null {
  try {
    const bruto = localStorage.getItem(CHAVE);
    if (!bruto) return null;
    const s = JSON.parse(bruto) as SessaoSalva;
    const util =
      s?.versao === 1 &&
      Array.isArray(s.questoes) &&
      s.questoes.length > 0 &&
      s.idx < s.questoes.length &&
      Date.now() - s.salvoEm < VALIDADE_MS;
    if (!util) {
      limparSessao();
      return null;
    }
    return { ...s, sessaoId: s.sessaoId ?? String(s.salvoEm), caso: s.caso ?? CASO_VAZIO };
  } catch {
    limparSessao();
    return null;
  }
}

export function limparSessao() {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    /* idem */
  }
}
