import { useQueryClient } from "@tanstack/react-query";
import { Brain, Check, Layers, type LucideIcon, PencilLine } from "lucide-react";
import { useState } from "react";
import { plural } from "../../lib/cartoes";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { atraso } from "../../lib/movimento";
import { estimarDuracao } from "../../lib/prazo";
import { definirMetaRevisao } from "../../lib/revisao";
import type { PainelData, PrioridadeEstudo } from "../../lib/types";

const METAS = [10, 20, 30, 50];
// Sessão aberta daqui: 10 casos, ou o tema inteiro quando ele tem menos (a
// mesma conta de "Onde você ganha mais pontos").
const QUANTIDADE = 10;

interface Props {
  revisao: PainelData["revisao"];
  cartoesHoje: number;
  prioridade?: PrioridadeEstudo;
  onRevisar: () => void;
  onEstudarCartoes: () => void;
  onPraticar: (prioridade: PrioridadeEstudo, quantidade: number) => void;
}

interface Passo {
  chave: string;
  icone: LucideIcon;
  // pendente: é o que falta fazer; feito: ela já fez hoje; livre: não há nada.
  estado: "pendente" | "feito" | "livre";
  titulo: string;
  detalhe: string;
  acao?: { rotulo: string; onClick: () => void };
}

// DESIGN_TRIAGEM.md §6, Painel item 2: o que fazer hoje, logo abaixo do título.
// O Painel era um relatório de oito blocos, e a fila de revisão — a única
// obrigação do dia — era o sétimo. Aqui ficam os três passos do dia, na ordem
// em que valem (a revisão vence, os cartões vencem, o tema novo espera), com
// um botão primário só: o do primeiro passo pendente.
export function CondutaHoje({ revisao, cartoesHoje, prioridade, onRevisar, onEstudarCartoes, onPraticar }: Props) {
  const queryClient = useQueryClient();
  const [salvando, setSalvando] = useState(false);
  const { hoje, meta, feitas_hoje, excedente, segundos_por_caso } = revisao;
  const opcoes = METAS.includes(meta) ? METAS : [...METAS, meta].sort((a, b) => a - b);

  async function mudarMeta(nova: number) {
    setSalvando(true);
    try {
      await definirMetaRevisao(nova);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["painel"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["revisao-leva"] }),
      ]);
    } finally {
      setSalvando(false);
    }
  }

  const casos = (n: number) => `${n} caso${n !== 1 ? "s" : ""}`;
  const esperam = excedente > 0 ? `outros ${excedente} podem esperar até amanhã` : null;
  const passos: Passo[] = [];

  if (hoje > 0) {
    passos.push({
      chave: "revisao",
      icone: Brain,
      estado: "pendente",
      titulo: `${casos(hoje)} para revisar`,
      detalhe: [estimarDuracao(hoje, segundos_por_caso), esperam].filter(Boolean).join(" · "),
      acao: { rotulo: "Revisar", onClick: onRevisar },
    });
  } else if (feitas_hoje > 0) {
    passos.push({
      chave: "revisao",
      icone: Brain,
      estado: "feito",
      titulo: excedente > 0 ? "Meta de revisão cumprida" : "Revisão em dia",
      detalhe: [`${casos(feitas_hoje)} revisado${feitas_hoje !== 1 ? "s" : ""} hoje`, esperam].filter(Boolean).join(" · "),
      // Com a meta cumprida e mais casos vencidos, a Revisão oferece "Revisar mais".
      acao: excedente > 0 ? { rotulo: "Revisar mais", onClick: onRevisar } : undefined,
    });
  } else {
    passos.push({
      chave: "revisao",
      icone: Brain,
      estado: "livre",
      titulo: "Nada para revisar hoje",
      detalhe: "Os casos que você errar voltam para cá.",
    });
  }

  // Só aparece quando há cartão vencido: quem não usa baralhos não é cobrada.
  if (cartoesHoje > 0) {
    passos.push({
      chave: "cartoes",
      icone: Layers,
      estado: "pendente",
      titulo: `${plural(cartoesHoje)} para hoje`,
      detalhe: "dos seus baralhos",
      acao: { rotulo: "Estudar", onClick: onEstudarCartoes },
    });
  }

  if (prioridade) {
    const quantidade = Math.min(QUANTIDADE, prioridade.questoes_banco);
    passos.push({
      chave: "praticar",
      icone: PencilLine,
      estado: "pendente",
      titulo: prioridade.tema,
      detalhe: `${prioridade.especialidade} · caiu em ${prioridade.provas} das ${prioridade.total_provas} provas do INEP`,
      acao: { rotulo: `Praticar ${quantidade}`, onClick: () => onPraticar(prioridade, quantidade) },
    });
  }

  const primario = passos.find((p) => p.estado === "pendente" && p.acao)?.chave;

  return (
    <section className="rounded-card border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-line-soft px-5 py-3.5 sm:px-6">
        <h2 className="rotulo text-muted">Conduta de hoje</h2>
        {/* A meta mora aqui porque é ela que decide quantos casos entram na
            primeira linha. */}
        <label htmlFor="meta-revisao" className="flex items-center gap-2 text-apoio text-muted">
          Meta de revisão
          <select
            id="meta-revisao"
            value={meta}
            disabled={salvando}
            onChange={(e) => void mudarMeta(Number(e.target.value))}
            className="h-8 rounded-btn border border-line bg-surface px-2 text-apoio font-semibold tabular-nums text-ink outline-none transition duration-hover focus:border-ink disabled:opacity-60"
          >
            {opcoes.map((m) => (
              <option key={m} value={m}>
                {m} casos
              </option>
            ))}
          </select>
        </label>
      </div>

      <ol className="divide-y divide-line-soft">
        {passos.map((p, i) => {
          const Icone = p.estado === "feito" ? Check : p.icone;
          return (
            <li
              key={p.chave}
              className="grid animate-entrar grid-cols-[36px_minmax(0,1fr)_auto] items-center gap-x-3.5 px-5 py-4 sm:gap-x-4 sm:px-6"
              style={atraso(i + 1, 60)}
            >
              {/* Feito é o t4-soft da ofensiva cumprida (DESIGN_TRIAGEM.md §2);
                  pendente é tinta; sem nada a fazer, apagado. */}
              <span
                className={`flex h-9 w-9 items-center justify-center rounded-btn ${
                  p.estado === "feito" ? "bg-t4-soft text-ink" : p.estado === "livre" ? "bg-ground text-faint" : "bg-ground text-ink-2"
                }`}
                aria-hidden="true"
              >
                <Icone size={18} strokeWidth={2} />
              </span>
              <div className="flex min-w-0 flex-col gap-0.5">
                <span className={`text-[15.5px] font-semibold leading-snug ${p.estado === "livre" ? "text-ink-2" : "text-ink"}`}>
                  {p.titulo}
                </span>
                <span className="text-apoio text-muted">{p.detalhe}</span>
              </div>
              {p.acao && (
                <button
                  type="button"
                  onClick={p.acao.onClick}
                  className={p.chave === primario ? BOTAO_PRIMARIO : BOTAO_SECUNDARIO}
                >
                  {p.acao.rotulo}
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
