import { ArrowRight } from "lucide-react";
import { formatarPctBR } from "../../lib/format";
import { CLASSES_NIVEL, MINIMO_AMOSTRA, NIVEIS, nivelTriagem, type NivelTriagem } from "../../lib/triagem";
import type { AreaDesempenho } from "../../lib/types";

interface Props {
  areas: AreaDesempenho[];
  onAbrir: (areaId: number) => void;
  onPraticar: (areaId: number) => void;
}

// Vírgula em vez de "e" final: nomes de área já têm "e" ("Ginecologia e Obstetrícia").
function listaNatural(itens: string[]): string {
  return itens.join(", ");
}

function CartaoArea({
  area,
  nivel,
  destaque,
  onAbrir,
  onPraticar,
}: {
  area: AreaDesempenho;
  nivel: NivelTriagem;
  destaque: boolean;
  onAbrir: (areaId: number) => void;
  onPraticar: (areaId: number) => void;
}) {
  return (
    <div className="group relative flex flex-col gap-1.5 rounded-card border border-line bg-surface p-3.5 transition duration-hover ease-brand hover:border-muted">
      {/* Botão que cobre o cartão inteiro: evita botão dentro de botão com o "Praticar 10". */}
      <button
        type="button"
        onClick={() => onAbrir(area.area_id)}
        className="absolute inset-0 rounded-card"
        aria-label={`Configurar sessão de ${area.area}`}
      />
      <span className="text-[15px] font-semibold leading-snug">{area.area}</span>
      <div className="flex items-baseline justify-between gap-2">
        <span className="num-md">{formatarPctBR(area.pct_acerto)}%</span>
        <span className={`text-[13px] tabular-nums text-muted ${destaque ? "" : "group-focus-within:hidden group-hover:hidden"}`}>
          {area.acertos}/{area.total}
        </span>
        {!destaque && (
          // Troca a fração pelo atalho no hover, na mesma linha: o cartão não
          // cresce e a coluna não pula.
          <button
            type="button"
            onClick={() => onPraticar(area.area_id)}
            className="relative z-10 hidden items-center gap-1 text-[13px] font-semibold text-ink underline-offset-2 hover:underline group-focus-within:flex group-hover:flex"
          >
            Praticar 10
            <ArrowRight size={14} strokeWidth={2} />
          </button>
        )}
      </div>
      <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
        <div className={`h-1 ${CLASSES_NIVEL[nivel].cheio}`} style={{ width: `${area.pct_acerto}%` }} />
      </div>
      {destaque && (
        <button
          type="button"
          onClick={() => onPraticar(area.area_id)}
          className="relative z-10 mt-2 flex h-9 items-center justify-center gap-1.5 rounded-btn bg-ink text-[14px] font-semibold text-onink transition duration-hover hover:opacity-90"
        >
          Praticar 10
          <ArrowRight size={15} strokeWidth={2} />
        </button>
      )}
    </div>
  );
}

// DESIGN_TRIAGEM.md §6, Painel item 2: uma coluna por nível, áreas do pior
// para o melhor aproveitamento.
export function QuadroTriagem({ areas, onAbrir, onPraticar }: Props) {
  const suficientes = areas.filter((a) => a.total >= MINIMO_AMOSTRA).sort((a, b) => a.pct_acerto - b.pct_acerto);
  const insuficientes = areas.filter((a) => a.total < MINIMO_AMOSTRA);
  const colunas = NIVEIS.map((n) => ({
    ...n,
    areas: suficientes.filter((a) => nivelTriagem(a.pct_acerto) === n.nivel),
  }));
  // A pior área do quadro inteiro, que é sempre o primeiro cartão da coluna mais grave.
  const idDestaque = suficientes[0]?.area_id;

  return (
    <section aria-label="Quadro de triagem" className="flex flex-col gap-3">
      <div className="grid grid-cols-1 items-start gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {colunas.map((col) => (
          <div key={col.nivel} className="flex flex-col gap-2.5">
            <div
              className={`flex h-10 items-center justify-between rounded-col px-3 ${CLASSES_NIVEL[col.nivel].cheio} ${CLASSES_NIVEL[col.nivel].texto}`}
            >
              <span className="rotulo text-[14px]">{col.nome}</span>
              <span className="text-[15px] font-bold tabular-nums">{col.areas.length}</span>
            </div>
            {col.areas.length === 0 ? (
              // Só na tela larga (5 colunas lado a lado); empilhado, o cabeçalho com 0 já basta.
              <div className="hidden rounded-card border border-dashed border-line px-3.5 py-4 text-apoio text-muted xl:block">
                {col.nivel === 5 ? "Nenhuma área acima de 85% ainda." : "Nenhuma área nesta faixa."}
              </div>
            ) : (
              col.areas.map((a) => (
                <CartaoArea
                  key={a.area_id}
                  area={a}
                  nivel={col.nivel}
                  destaque={a.area_id === idDestaque}
                  onAbrir={onAbrir}
                  onPraticar={onPraticar}
                />
              ))
            )}
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-apoio text-muted">
        <span>Classificação pelo aproveitamento:</span>
        {NIVEIS.map((n) => (
          <span key={n.nivel} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-[2px] ${CLASSES_NIVEL[n.nivel].cheio}`} aria-hidden="true" />
            {n.faixa}
          </span>
        ))}
        {insuficientes.length > 0 && (
          <span className="xl:ml-auto">
            Amostra insuficiente: {listaNatural(insuficientes.map((a) => a.area))}
          </span>
        )}
      </div>
    </section>
  );
}
