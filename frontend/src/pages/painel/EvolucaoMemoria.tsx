import { formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import { CLASSES_NIVEL, MINIMO_AMOSTRA, NIVEIS, nivelTriagem } from "../../lib/triagem";
import type { EvolucaoMemoria as Memoria } from "../../lib/types";

const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
// Altura das barras de retenção; 100% ocupa tudo (a escala é sempre 0–100).
const ALTURA = 72;

// Do menos para o mais firme: a tinta ganha força conforme o caso consolida.
// Não são níveis de triagem, então nada das cores t1–t5 (DESIGN_TRIAGEM.md §1).
// `--faint` não serve para o primeiro degrau: fica quase igual a `--muted` nos
// dois temas (e é mais clara que ela no claro, mais escura no escuro).
const ESTAGIOS = [
  { chave: "aprendendo", nome: "Aprendendo", descricao: "errou da última vez", cor: "bg-muted opacity-40" },
  { chave: "consolidando", nome: "Consolidando", descricao: "acertou, volta em menos de 21 dias", cor: "bg-muted" },
  { chave: "consolidado", nome: "Consolidado", descricao: "volta em 21 dias ou mais", cor: "bg-ink" },
] as const;

const pct = (lembrou: number, testes: number) => (100 * lembrou) / testes;

function dataCurta(iso: string) {
  const d = new Date(`${iso}T00:00:00`);
  return `${d.getDate()} ${MESES_CURTOS[d.getMonth()]}`;
}

// DESIGN_TRIAGEM.md §6, Painel item 5 (repeticao_espacada.evolucao_memoria).
export function EvolucaoMemoria({ memoria }: { memoria: Memoria }) {
  const { estagios, semanas, especialidades, ultimos_7_dias } = memoria;
  return (
    <section className="flex flex-col gap-5 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="rotulo text-muted">Evolução da memória</span>
        <span className="text-apoio text-muted">conta os casos que voltaram depois de pelo menos 1 dia</span>
      </div>
      <ResumoSemana
        semana={ultimos_7_dias}
        anterior={semanas[semanas.length - 2]}
        temHistorico={semanas.some((s) => s.testes > 0)}
      />
      <div className="grid grid-cols-1 gap-7 border-t border-line-soft pt-5 lg:grid-cols-3 lg:gap-9">
        <Estagios estagios={estagios} />
        <RetencaoSemanas semanas={semanas} />
        <OndeEsquece especialidades={especialidades} />
      </div>
    </section>
  );
}

function ResumoSemana({
  semana,
  anterior,
  temHistorico,
}: {
  semana: Memoria["ultimos_7_dias"];
  anterior: Memoria["semanas"][number] | undefined;
  temHistorico: boolean;
}) {
  if (semana.testes === 0) {
    return (
      <p className="text-corpo text-ink-2">
        {temHistorico
          ? "Nenhum caso voltou para revisão nos últimos 7 dias."
          : "A retenção aparece quando os casos que você respondeu voltarem para revisão, a partir do dia seguinte."}
      </p>
    );
  }

  const retencao = pct(semana.lembrou, semana.testes);
  // Mesmo limite do quadro de triagem: com menos casos, percentual não é informação.
  const suficiente = semana.testes >= MINIMO_AMOSTRA;
  const nivel = nivelTriagem(retencao);
  const detalhes = [
    suficiente && anterior && anterior.testes >= MINIMO_AMOSTRA
      ? `na semana anterior, ${formatarPctBR(pct(anterior.lembrou, anterior.testes), 0)}%`
      : null,
    semana.recuperados > 0 ? `${semana.recuperados} ${semana.recuperados === 1 ? "caso recuperado" : "casos recuperados"}` : null,
    semana.consolidados > 0
      ? `${semana.consolidados} ${semana.consolidados === 1 ? "caso consolidado" : "casos consolidados"}`
      : null,
    semana.dias_com_revisao > 0 ? `revisou em ${semana.dias_com_revisao} de 7 dias` : null,
  ].filter(Boolean);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <p className="text-bloco text-balance">
          Nos últimos 7 dias, {semana.testes} {semana.testes === 1 ? "caso voltou" : "casos voltaram"} e você lembrou de{" "}
          {semana.lembrou}
          {suficiente ? ` (${formatarPctBR(retencao, 0)}%)` : ""}.
        </p>
        {suficiente && (
          <span className={`rotulo rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}>
            {NIVEIS[nivel - 1].nome}
          </span>
        )}
      </div>
      {detalhes.length > 0 && <p className="text-apoio text-muted">{detalhes.join(" · ")}</p>}
    </div>
  );
}

function Estagios({ estagios }: { estagios: Memoria["estagios"] }) {
  const total = estagios.aprendendo + estagios.consolidando + estagios.consolidado;
  return (
    <div className="flex flex-col gap-3">
      <span className="text-apoio font-semibold text-ink-2">Estágios dos casos</span>
      {total === 0 ? (
        <p className="text-apoio text-muted">Cada caso que você responder entra aqui.</p>
      ) : (
        <>
          <div
            role="img"
            aria-label={ESTAGIOS.map((e) => `${e.nome}: ${estagios[e.chave]}`).join(", ")}
            className="flex h-2.5 origin-left animate-crescer gap-[2px] overflow-hidden rounded-[3px]"
          >
            {ESTAGIOS.map((e) =>
              estagios[e.chave] > 0 ? (
                <div key={e.chave} className={e.cor} style={{ flex: `${estagios[e.chave]} 1 0`, minWidth: 4 }} />
              ) : null,
            )}
          </div>
          <ul className="flex flex-col gap-2">
            {ESTAGIOS.map((e) => (
              <li key={e.chave} className="grid grid-cols-[10px_minmax(0,1fr)_auto] items-center gap-x-2.5">
                <span className={`h-2.5 w-2.5 rounded-[2px] ${e.cor}`} aria-hidden="true" />
                <span className="min-w-0 leading-snug">
                  <span className="text-corpo text-ink">{e.nome}</span>{" "}
                  <span className="text-apoio text-muted">· {e.descricao}</span>
                </span>
                <span className="text-corpo font-semibold tabular-nums text-ink">{estagios[e.chave]}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function RetencaoSemanas({ semanas }: { semanas: Memoria["semanas"] }) {
  const cabecalho = <span className="text-apoio font-semibold text-ink-2">Retenção por semana</span>;

  if (!semanas.some((s) => s.testes >= MINIMO_AMOSTRA)) {
    return (
      <div className="flex flex-col gap-3">
        {cabecalho}
        <p
          className="flex items-center rounded-card border border-dashed border-line px-4 text-apoio text-muted"
          style={{ minHeight: ALTURA + 44 }}
        >
          Uma semana entra no gráfico quando pelo menos {MINIMO_AMOSTRA} casos voltarem nela.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {cabecalho}
      <div className="flex flex-col gap-1.5">
        <div
          className="grid items-end gap-1.5"
          style={{ height: ALTURA + 20, gridTemplateColumns: `repeat(${semanas.length}, minmax(0, 1fr))` }}
        >
          {semanas.map((s, i) => {
            const atual = i === semanas.length - 1;
            const suficiente = s.testes >= MINIMO_AMOSTRA;
            const retencao = suficiente ? pct(s.lembrou, s.testes) : 0;
            const periodo = atual ? "Últimos 7 dias" : `Semana de ${dataCurta(s.inicio)}`;
            const descricao =
              s.testes === 0
                ? `${periodo}: nenhum caso voltou`
                : suficiente
                  ? `${periodo}: ${formatarPctBR(retencao, 0)}% (lembrou de ${s.lembrou} em ${s.testes})`
                  : `${periodo}: ${s.testes} ${s.testes === 1 ? "caso" : "casos"}, poucos para calcular`;
            return (
              <div
                key={s.inicio}
                role="img"
                aria-label={descricao}
                title={descricao}
                className="flex h-full flex-col items-center justify-end gap-1"
              >
                {suficiente ? (
                  <>
                    <span className={`text-[11.5px] tabular-nums ${atual ? "font-bold text-ink" : "text-muted"}`}>
                      {Math.round(retencao)}%
                    </span>
                    <div
                      className={`animate-crescer-y w-full max-w-[22px] rounded-t-[3px] ${atual ? "bg-ink" : "bg-muted"}`}
                      style={{ height: Math.max((retencao / 100) * ALTURA, 3), ...atraso(i, 45) }}
                    />
                  </>
                ) : (
                  // Semana sem amostra: só a marca no chão, sem inventar altura.
                  <div className="h-[3px] w-full max-w-[22px] rounded-[2px] bg-line" />
                )}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between border-t border-line pt-1.5 text-[12px] text-muted">
          <span>{dataCurta(semanas[0].inicio)}</span>
          <span className="font-semibold text-ink">últimos 7 dias</span>
        </div>
      </div>
    </div>
  );
}

function OndeEsquece({ especialidades }: { especialidades: Memoria["especialidades"] }) {
  // Já vêm da menor retenção para a maior.
  const lista = especialidades.filter((e) => e.testes >= MINIMO_AMOSTRA).slice(0, 4);
  return (
    <div className="flex flex-col gap-3">
      <span className="text-apoio font-semibold text-ink-2">Onde você mais esquece</span>
      {lista.length === 0 ? (
        <p className="text-apoio text-muted">
          Uma especialidade aparece aqui quando pelo menos {MINIMO_AMOSTRA} casos dela voltarem para revisão.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {lista.map((e, i) => {
            const retencao = pct(e.lembrou, e.testes);
            const nivel = nivelTriagem(retencao);
            return (
              <li key={`${e.area}|${e.especialidade ?? ""}`} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="min-w-0 truncate text-corpo text-ink" title={e.especialidade ? `${e.especialidade} · ${e.area}` : e.area}>
                    {e.especialidade ?? e.area}
                  </span>
                  <span className="shrink-0 text-apoio tabular-nums">
                    <span className="font-semibold text-ink">{formatarPctBR(retencao, 0)}%</span>{" "}
                    <span className="text-muted">
                      {e.lembrou}/{e.testes}
                    </span>
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                  <div
                    className={`h-1 origin-left animate-crescer ${CLASSES_NIVEL[nivel].cheio}`}
                    style={{ width: `${retencao}%`, ...atraso(i + 2, 60) }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
