import type { PrevisaoDia } from "../../lib/types";

const DIAS_CURTOS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
const DIAS_LONGOS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];
// Altura da área das barras; a do dia mais carregado (ou a meta) ocupa tudo.
const ALTURA = 64;

function rotuloCurto(iso: string, indice: number) {
  return indice === 0 ? "hoje" : DIAS_CURTOS[new Date(`${iso}T00:00:00`).getDay()];
}

function descricao(d: PrevisaoDia, indice: number) {
  const total = d.dentro_meta + d.acima_meta;
  const dia = indice === 0 ? "Hoje" : DIAS_LONGOS[new Date(`${d.dia}T00:00:00`).getDay()];
  const base = `${dia}: ${total} caso${total !== 1 ? "s" : ""}`;
  return d.acima_meta > 0 ? `${base}, ${d.acima_meta} acima da meta (esperam o dia seguinte)` : base;
}

// Carga de revisão dos próximos 7 dias contra a meta (repeticao_espacada.previsao_revisoes).
// Parte dentro da meta em tinta; o que passa dela em t2, a cor de atenção
// (DESIGN_TRIAGEM.md §2); linha tracejada na altura da meta.
export function PrevisaoSemana({ dias, meta }: { dias: PrevisaoDia[]; meta: number }) {
  const maior = Math.max(meta, ...dias.map((d) => d.dentro_meta + d.acima_meta), 1);
  const escala = (n: number) => (n / maior) * ALTURA;
  // Um dia com 1 caso numa semana de 35 daria menos de 2px e pareceria um traço solto.
  const alturaBarra = (n: number) => Math.max(escala(n), 4);
  const temAcima = dias.some((d) => d.acima_meta > 0);

  return (
    <figure className="flex flex-col gap-2">
      <figcaption className="flex items-baseline justify-between gap-3">
        <span className="rotulo text-muted">Próximos 7 dias</span>
        <span className="text-apoio text-muted">meta de {meta} por dia</span>
      </figcaption>

      <div className="relative grid grid-cols-7 gap-1.5" style={{ height: ALTURA + 20 }}>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 border-t border-dashed border-faint"
          style={{ bottom: escala(meta) }}
        />
        {dias.map((d, i) => {
          const total = d.dentro_meta + d.acima_meta;
          return (
            <div
              key={d.dia}
              role="img"
              aria-label={descricao(d, i)}
              tabIndex={0}
              className="group relative flex cursor-default flex-col items-center justify-end gap-1 outline-none"
            >
              {/* No lugar do `title` nativo, que esperava ~1s e não existia no
                  toque; aqui o foco (tabIndex) revela a dica no celular. Nas
                  pontas ela se alinha pela borda, para não sair do cartão. */}
              <span
                className={`pointer-events-none absolute bottom-full z-10 mb-1.5 whitespace-nowrap rounded-etq border border-line bg-surface px-2 py-1 text-[12px] font-semibold text-ink opacity-0 transition-opacity duration-hover ease-brand group-hover:opacity-100 group-focus-within:opacity-100 ${
                  i === 0 ? "left-0" : i === dias.length - 1 ? "right-0" : "left-1/2 -translate-x-1/2"
                }`}
              >
                {descricao(d, i)}
              </span>
              <span className="text-[12px] font-semibold tabular-nums text-ink-2">{total > 0 ? total : ""}</span>
              {total > 0 && (
                <div
                  className="animate-crescer-y flex w-full max-w-[26px] flex-col gap-[2px] overflow-hidden rounded-t-[3px]"
                  style={{ height: alturaBarra(total), animationDelay: `${i * 45}ms` }}
                >
                  {d.acima_meta > 0 && <div className="shrink-0 bg-t2" style={{ height: escala(d.acima_meta) }} />}
                  <div className="flex-1 bg-ink" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-7 gap-1.5 border-t border-line pt-1.5">
        {dias.map((d, i) => (
          <span key={d.dia} className={`text-center text-[12px] ${i === 0 ? "font-semibold text-ink" : "text-muted"}`}>
            {rotuloCurto(d.dia, i)}
          </span>
        ))}
      </div>

      {temAcima && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-apoio text-muted">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-[2px] bg-ink" aria-hidden="true" />
            cabe na meta
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-[2px] bg-t2" aria-hidden="true" />
            passa da meta e espera o dia seguinte
          </span>
        </div>
      )}
    </figure>
  );
}
