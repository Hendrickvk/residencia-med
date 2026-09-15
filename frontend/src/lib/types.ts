export interface Questao {
  id: number;
  area_id: number;
  especialidade_id: number | null;
  subtopico_id: number | null;
  area: string;
  especialidade: string | null;
  subtopico: string | null;
  enunciado: string;
  alternativas: Record<string, string>;
  resposta_correta: string;
  explicacao: string | null;
  banca: string | null;
  ano: number | null;
  marcada: boolean;
  tem_imagem: boolean;
}

export interface FiltrosPratica {
  area_id?: number;
  especialidade_id?: number;
  subtopico_id?: number;
  tipo_pergunta?: string;
  banca?: string;
  ano?: number;
  apenas_erros: boolean;
  excluir_respondidas: boolean;
  quantidade: number;
}

export interface RespostaPayload {
  questao_id: number;
  alternativa: string;
  confianca?: "seguro" | "chute";
  tempo_ms?: number;
}

export interface Area {
  id: number;
  nome: string;
}

// Segundo nível da taxonomia (grande área > especialidade). Os totais servem
// para os filtros esconderem especialidades sem conteúdo.
export interface Especialidade {
  id: number;
  area_id: number;
  nome: string;
  total_questoes: number;
}

// Terceiro nível: o tema da especialidade (db.TEMAS). Na API e no banco se
// chama subtópico (tabela `subtopicos`, campo `subtopico_id` da questão).
export interface Subtopico {
  id: number;
  area_id: number;
  especialidade_id: number | null;
  nome: string;
  total_questoes: number;
}

export interface RespondidaResumo {
  id: number;
  correta: boolean;
  area: string;
  especialidade: string | null;
  tempoMs: number;
}

export interface ResumoSessao {
  respondidas: RespondidaResumo[];
  duracaoTotalMs: number;
}

export interface AreaDesempenho {
  area_id: number;
  area: string;
  total: number;
  acertos: number;
  pct_acerto: number;
}

export interface DiaEvolucao {
  dia: string;
  total: number;
  acertos: number;
  pct_acerto: number;
}

export interface PainelData {
  totais: { respostas: number; acertos: number; pct_acerto_geral: number };
  por_area: AreaDesempenho[];
  evolucao_14_dias: DiaEvolucao[];
  respondidas_hoje: number;
  revisoes_hoje: number;
  revisao: RevisaoHoje & { hoje: number; proximos_dias: PrevisaoDia[] };
  memoria: EvolucaoMemoria;
  prioridades: PrioridadeEstudo[];
  por_tipo: DesempenhoTipo[];
}

// Acerto na primeira resposta por tipo de pergunta (db.desempenho_por_tipo), na
// ordem de db.TIPOS_PERGUNTA, incluindo os tipos ainda sem resposta.
export interface DesempenhoTipo {
  tipo: string;
  total: number;
  acertos: number;
}

// Tema com mais pontos a ganhar (db.prioridades_estudo): fração dos cadernos do
// INEP que ele ocupa × o que falta de domínio. Já vem na ordem de prioridade.
export interface PrioridadeEstudo {
  subtopico_id: number;
  tema: string;
  especialidade_id: number;
  especialidade: string;
  area_id: number;
  area: string;
  questoes_provas: number; // questões de caderno do INEP deste tema
  provas: number; // em quantas provas do INEP ele caiu
  total_provas: number;
  questoes_banco: number;
  respondidas: number; // primeira resposta a questões do tema
  acertos: number;
  dominio_estimado: number; // 0–100; com poucas respostas, puxado para a especialidade
  peso_prova: number; // % das questões de caderno
}

// Acompanhamento da memória (repeticao_espacada.evolucao_memoria). "Teste" é um
// caso que voltou depois de pelo menos 1 dia sem ser visto; retenção = lembrou/testes.
export interface EvolucaoMemoria {
  estagios: { aprendendo: number; consolidando: number; consolidado: number };
  // Blocos de 7 dias terminando hoje, do mais antigo para o atual.
  semanas: { inicio: string; testes: number; lembrou: number }[];
  // Da menor retenção para a maior, nas mesmas semanas.
  especialidades: { area: string; especialidade: string | null; testes: number; lembrou: number }[];
  ultimos_7_dias: { testes: number; lembrou: number; recuperados: number; consolidados: number; dias_com_revisao: number };
}

// Carga do dia sob a meta diária (repeticao_espacada.plano_revisao / resumo_revisao_hoje).
export interface RevisaoHoje {
  meta: number;
  feitas_hoje: number;
  excedente: number; // venceram, mas passam da meta: esperam, por prioridade
  segundos_por_caso: number; // mediana do próprio aluno, para estimar a duração
}

// Um dia da previsão de carga (repeticao_espacada.previsao_revisoes).
export interface PrevisaoDia {
  dia: string;
  vencem: number;
  dentro_meta: number;
  acima_meta: number;
}

export interface ProximaLeva {
  dia: string;
  total: number;
}

// Prazo que uma nota agenda (repeticao_espacada.prever_prazos): minutos só no erro.
export type PrazoRevisao = { minutos: number } | { dias: number };
export type PrazosRevisao = Record<"1" | "3" | "4" | "5", PrazoRevisao>;

export interface QuestaoRevisao extends Questao {
  prazos: PrazosRevisao;
}

export interface LevaRevisao {
  fila: QuestaoRevisao[];
  proxima_leva: ProximaLeva | null;
  hoje: RevisaoHoje;
}

export interface AvaliacaoRevisao {
  ok: boolean;
  correta: boolean | null;
  qualidade: number;
  proxima_revisao: string;
  // Previstos a partir do novo estado: o caso errado reaparece na sessão com eles.
  prazos: PrazosRevisao;
  recuperado: boolean; // tinha errado e lembrou depois de pelo menos 1 dia
  consolidou: boolean; // o intervalo passou a 21 dias ou mais
}

export interface Simulado {
  id: number;
  area_id: number | null;
  banca: string | null;
  edicao: string | null; // preenchida só no simulado por edição oficial, ex. "2025/1"
  num_questoes: number;
  tempo_limite_min: number;
  iniciado_em: string;
  finalizado_em: string | null;
  acertos: number | null;
  total_respondidas: number | null;
}

export interface SimuladoEmAndamento extends Simulado {
  respondidas: number;
}

export interface EdicaoOficial {
  banca: string;
  edicao: string;
  ano: number;
  total: number;
  tempo_limite_min: number;
}

export interface HistoricoSimulado extends Simulado {
  area: string | null;
  pct_acerto: number | null;
}

export interface ItemSimulado extends Omit<Questao, "resposta_correta" | "explicacao"> {
  item_id: number;
  ordem: number;
  resposta_dada: string | null;
  correta: number | null; // 0/1/null — coluna INTEGER, não convertida pra bool
  tempo_ms: number | null; // tempo de tela somado das passagens; null se nunca vista ou simulado antigo
  resposta_correta?: string; // só vem preenchido depois de finalizado
  explicacao?: string | null;
  edicao: string | null;
  numero_prova: number | null; // número da questão no caderno oficial
}

export interface DesempenhoAreaSimulado {
  area: string;
  total: number;
  acertos: number;
  pct_acerto: number;
}

export interface ResultadoBuscaQuestao {
  id: number;
  enunciado: string;
  area: string;
  especialidade: string | null;
}

export interface Me {
  id: number;
  email: string;
  is_admin: boolean;
  tema: "light" | "dark";
  prova_alvo: string | null;
  ofensiva_dias: number;
  respondeu_hoje: boolean;
  respondidas_hoje: number;
  total_questoes: number;
  meta_revisao_diaria: number;
}
