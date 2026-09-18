import { ArrowRight } from "lucide-react";
import { EtiquetaPct } from "../../components/EtiquetaPct";
import { formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import type { ProgressoSemana as Dados, TemaDaSemana } from "../../lib/types";

// Mesma quantidade das prioridades, o outro atalho de tema do Painel.
const QUANTIDADE = 10;

interface Props {
  semana: Dados;
  onPraticar: (tema: TemaDaSemana, quantidade: number) => void;
}

function dataCurta(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

// DESIGN_TRIAGEM.md §6, Painel ("O que mudou nesta semana", db.progresso_semana):
// o fim do ciclo que começa nas prioridades e passa pela prática.
export function ProgressoSemana({ semana, onPraticar }: Props) {
  const pct = semana.novas ? (100 * semana.acertos) / semana.novas : 0;
  return (
    <section className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="rotulo text-muted">O que mudou nesta semana</span>
        <span className="text-apoio text-muted">
          desde segunda, {dataCurta(semana.inicio)}: questões novas e o domínio estimado antes e agora
        </span>
      </div>
      <p className="text-corpo text-ink-2">
        <strong className="font-semibold text-ink">
          {semana.novas} {semana.novas === 1 ? "questão nova" : "questões novas"}
        </strong>
        , {semana.acertos.toLocaleString("pt-BR")} {semana.acertos === 1 ? "certa" : "certas"} (
        {formatarPctBR(pct, 0)}%).
      </p>
      <ul className="flex flex-col divide-y divide-line-soft">
        {semana.temas.map((t, i) => (
          <li
            key={t.subtopico_id}
            className="grid animate-entrar grid-cols-[minmax(0,1fr)_auto] items-center gap-4 py-3 first:pt-0 last:pb-0"
            style={atraso(i + 1, 60)}
          >
            <div className="min-w-0">
              {/* O bloco fechava o ciclo das prioridades sem dar como continuá-lo:
                  o tema agora abre a sessão dele, como em "Onde você ganha mais pontos". */}
              <button
                type="button"
                onClick={() => onPraticar(t, QUANTIDADE)}
                aria-label={`Praticar ${QUANTIDADE} casos de ${t.tema}`}
                className="group/tema flex w-full min-w-0 items-center gap-1.5 text-left"
              >
                <span className="truncate text-corpo font-semibold underline-offset-2 group-hover/tema:underline">
                  {t.tema}
                </span>
                <ArrowRight
                  size={14}
                  strokeWidth={2}
                  aria-hidden="true"
                  className="shrink-0 text-muted transition-transform duration-toggle ease-suave group-hover/tema:translate-x-0.5"
                />
              </button>
              <div className="truncate text-apoio text-muted">
                {t.especialidade} · {t.novas} {t.novas === 1 ? "nova" : "novas"},{" "}
                {t.acertos.toLocaleString("pt-BR")} {t.acertos === 1 ? "certa" : "certas"}
                {t.testes > 0 && ` · na Revisão, lembrou de ${t.lembrou} de ${t.testes}`}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Sem o "antes" na primeira semana do aluno: não há de onde partir. */}
              {t.dominio_antes !== null && (
                <>
                  <span className="text-apoio tabular-nums text-muted">{formatarPctBR(t.dominio_antes, 0)}%</span>
                  <span className="sr-only">passou para</span>
                  <ArrowRight size={14} strokeWidth={2} className="text-muted" aria-hidden="true" />
                </>
              )}
              <EtiquetaPct pct={t.dominio_agora} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
