export interface Questao {
  id: number;
  area_id: number;
  subtopico_id: number | null;
  area: string;
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
  subtopico_id?: number;
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

export interface Subtopico {
  id: number;
  area_id: number;
  nome: string;
}

export interface RespondidaResumo {
  id: number;
  correta: boolean;
  subtopico: string | null;
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
}

export interface ProximaLeva {
  dia: string;
  total: number;
}

export interface LevaRevisao {
  fila: Questao[];
  proxima_leva: ProximaLeva | null;
}

export interface Simulado {
  id: number;
  area_id: number | null;
  banca: string | null;
  num_questoes: number;
  tempo_limite_min: number;
  iniciado_em: string;
  finalizado_em: string | null;
  acertos: number | null;
  total_respondidas: number | null;
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
  resposta_correta?: string; // só vem preenchido depois de finalizado
  explicacao?: string | null;
}

export interface DesempenhoAreaSimulado {
  area: string;
  total: number;
  acertos: number;
  pct_acerto: number;
}

export interface Material {
  id: number;
  area_id: number;
  subtopico_id: number | null;
  subtopico: string | null;
  tipo: string;
  titulo: string;
  link_mediafire: string;
  tamanho_bytes: number | null;
}

export interface ResultadoBuscaQuestao {
  id: number;
  enunciado: string;
  area: string;
}

export interface ResultadoBuscaMaterial {
  id: number;
  titulo: string;
  tipo: string;
  link_mediafire: string;
}

export interface ResultadoBusca {
  questoes: ResultadoBuscaQuestao[];
  materiais: ResultadoBuscaMaterial[];
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
  total_materiais: number;
}
