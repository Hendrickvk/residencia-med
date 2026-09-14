import { useQuery } from "@tanstack/react-query";
import { ArrowRight, RotateCcw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { api } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";
import type { LevaRevisao } from "../../lib/types";

export interface AvaliacaoSessao {
  id: number;
  correta: boolean;
  qualidade: number;
  // Primeira vez que o caso aparece na sessão (erro o reinsere adiante).
  primeira: boolean;
  // Do servidor (repeticao_espacada.classificar_eventos); false se a gravação falhou.
  recuperado: boolean;
  consolidou: boolean;
}

const NOME_DIA_SEMANA = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

function quandoVence(dia: string): string {
  const alvo = new Date(`${dia}T00:00:00`);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const dias = Math.round((alvo.getTime() - hoje.getTime()) / 86_400_000);
  if (dias <= 0) return "ainda hoje";
  if (dias === 1) return "amanhã";
  if (dias < 7) return NOME_DIA_SEMANA[alvo.getDay()];
  return `em ${dias} dias`;
}

interface Props {
  avaliacoes: AvaliacaoSessao[];
  onRecomecar: () => void;
  onRevisarMais: () => void;
}

// DESIGN_TRIAGEM.md §6, Revisão espaçada: fim da fila com casos avaliados.
export default function ResumoRevisao({ avaliacoes, onRecomecar, onRevisarMais }: Props) {
  const navigate = useNavigate();
  // Consulta própria (sem `extra`), não a da sessão: a fila que o aluno acabou
  // de percorrer não pode mudar por baixo do resumo.
  const { data } = useQuery({
    queryKey: ["revisao-resumo", avaliacoes.length],
    queryFn: () => api.get<LevaRevisao>("/revisao/leva"),
    gcTime: 0,
  });

  // Retenção = acerto na primeira vez que o caso apareceu nesta sessão.
  const primeiras = avaliacoes.filter((a) => a.primeira);
  const casos = primeiras.length;
  const lembrou = primeiras.filter((a) => a.correta).length;
  const pct = casos ? Math.round((100 * lembrou) / casos) : 0;
  const nivel = nivelTriagem(pct);

  // Última avaliação de cada caso: os que terminaram errados voltam em 10 min.
  const ultima = new Map<number, AvaliacaoSessao>();
  for (const a of avaliacoes) ultima.set(a.id, a);
  const voltamLogo = [...ultima.values()].filter((a) => !a.correta).length;

  const recuperados = avaliacoes.filter((a) => a.recuperado).length;
  const consolidados = avaliacoes.filter((a) => a.consolidou).length;
  const marcos = [
    recuperados > 0
      ? `${recuperados === 1 ? "1 caso recuperado" : `${recuperados} casos recuperados`}: você tinha errado e lembrou pelo menos um dia depois`
      : null,
    consolidados > 0
      ? `${consolidados === 1 ? "1 caso consolidado: agora volta" : `${consolidados} casos consolidados: agora voltam`} em 21 dias ou mais`
      : null,
  ].filter(Boolean);

  const cabemNaMeta = data?.fila.length ?? 0;
  const excedente = data?.hoje.excedente ?? 0;
  const proxima = data?.proxima_leva ?? null;

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Resumo da revisão</span>
        <h1 className="text-titulo">
          Lembrou {lembrou} de {casos} caso{casos !== 1 ? "s" : ""}.
        </h1>
        {data && (
          <p className="animate-desvanecer text-corpo tabular-nums text-ink-2">
            {data.hoje.feitas_hoje >= data.hoje.meta
              ? `Meta de hoje cumprida: ${data.hoje.feitas_hoje} de ${data.hoje.meta} casos.`
              : `Meta de hoje: ${data.hoje.feitas_hoje} de ${data.hoje.meta} casos.`}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 divide-y divide-line-soft rounded-caso border border-line bg-surface sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Lembrou de primeira</span>
          <NumeroAnimado className="num-lg self-start" valor={pct} formatar={(v) => `${Math.round(v)}%`} />
          <span
            className={`rotulo animate-surgir self-start rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
            style={{ animationDelay: "750ms" }}
          >
            {NIVEIS[nivel - 1].nome}
          </span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Voltam em 10 min</span>
          <span className="num-lg">{voltamLogo}</span>
          <span className="text-apoio text-muted">{voltamLogo === 0 ? "nenhum ficou para depois" : "os que terminaram errados"}</span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Próxima leva</span>
          {data === undefined ? (
            <div className="h-[51px] w-20 animate-pulse rounded-card bg-line-soft" />
          ) : proxima ? (
            <>
              <span className="num-lg animate-desvanecer">{proxima.total}</span>
              <span className="text-apoio text-muted">
                caso{proxima.total !== 1 ? "s" : ""} {quandoVence(proxima.dia)}
              </span>
            </>
          ) : (
            <>
              <span className="num-lg">—</span>
              <span className="text-apoio text-muted">nada agendado</span>
            </>
          )}
        </div>
      </div>

      {marcos.length > 0 && (
        <p className="animate-desvanecer text-corpo text-ink-2" style={{ animationDelay: "500ms" }}>
          {marcos.join(". ")}.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {cabemNaMeta > 0 ? (
          <button type="button" onClick={onRecomecar} className={`group ${BOTAO_PRIMARIO}`}>
            <RotateCcw size={16} strokeWidth={2} className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]" />
            Revisar {cabemNaMeta} que já {cabemNaMeta === 1 ? "venceu" : "venceram"}
          </button>
        ) : excedente > 0 ? (
          // Meta cumprida: mais casos só se o aluno pedir, e em lotes pequenos.
          <button type="button" onClick={onRevisarMais} className={`group ${BOTAO_SECUNDARIO}`}>
            <RotateCcw size={16} strokeWidth={2} className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]" />
            Revisar mais {Math.min(10, excedente)}
          </button>
        ) : (
          <button type="button" onClick={() => navigate("/praticar")} className={`group ${BOTAO_PRIMARIO}`}>
            Praticar casos novos
            <ArrowRight size={18} strokeWidth={2} className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5" />
          </button>
        )}
        <button type="button" onClick={() => navigate("/painel")} className={cabemNaMeta === 0 && excedente > 0 ? BOTAO_PRIMARIO : BOTAO_SECUNDARIO}>
          Voltar ao Painel
        </button>
      </div>
    </div>
  );
}
