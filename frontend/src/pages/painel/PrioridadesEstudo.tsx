import { ArrowRight } from "lucide-react";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import { CLASSES_NIVEL, MINIMO_AMOSTRA, nivelTriagem } from "../../lib/triagem";
import type { PrioridadeEstudo } from "../../lib/types";

// Sessão aberta daqui: 10 casos, ou o tema inteiro quando ele tem menos.
const QUANTIDADE = 10;

interface Props {
  prioridades: PrioridadeEstudo[];
  onPraticar: (prioridade: PrioridadeEstudo, quantidade: number) => void;
}

// DESIGN_TRIAGEM.md §6, Painel ("Onde você ganha mais pontos", db.prioridades_estudo). A ordem vem do
// servidor; aqui só se mostra o motivo de cada tema estar na lista.
export function PrioridadesEstudo({ prioridades, onPraticar }: Props) {
  return (
    <section className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="rotulo text-muted">Onde você ganha mais pontos</span>
        <span className="text-apoio text-muted">temas que mais caem no Revalida e no ENAMED, cruzados com o seu acerto</span>
      </div>
      <ol className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        {prioridades.map((p, i) => {
          const quantidade = Math.min(QUANTIDADE, p.questoes_banco);
          const pct = p.respondidas > 0 ? (100 * p.acertos) / p.respondidas : 0;
          // Mesmo limite do quadro: com menos respostas, percentual não é informação.
          const suficiente = p.respondidas >= MINIMO_AMOSTRA;
          return (
            <li
              key={p.subtopico_id}
              className="flex animate-entrar flex-col gap-3 rounded-card border border-line p-4"
              style={atraso(i + 1, 60)}
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-[15px] font-semibold leading-snug">{p.tema}</span>
                <span className="text-apoio text-muted">
                  {p.especialidade} · {p.area}
                </span>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-apoio tabular-nums text-ink-2">
                  {p.respondidas === 0
                    ? "Você ainda não praticou este tema"
                    : suficiente
                      ? `${formatarPctBR(pct, 0)}% de acerto · ${p.acertos} de ${p.respondidas}`
                      : `Acertou ${p.acertos} de ${p.respondidas} · pouca evidência`}
                </span>
                {suficiente && (
                  <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                    <div
                      className={`h-1 origin-left animate-crescer ${CLASSES_NIVEL[nivelTriagem(pct)].cheio}`}
                      style={{ width: `${pct}%`, ...atraso(i + 2, 60) }}
                    />
                  </div>
                )}
                <span className="text-apoio text-muted">
                  Caiu em {p.provas} das {p.total_provas} provas do INEP
                </span>
              </div>
              {/* Só o primeiro é primário, como o "Praticar 10" do quadro. */}
              <button
                type="button"
                onClick={() => onPraticar(p, quantidade)}
                className={`group mt-auto ${i === 0 ? BOTAO_PRIMARIO : BOTAO_SECUNDARIO}`}
              >
                Praticar {quantidade}
                <ArrowRight
                  size={16}
                  strokeWidth={2}
                  className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5"
                />
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
