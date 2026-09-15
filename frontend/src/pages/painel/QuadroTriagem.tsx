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

// Cascata do quadro (DESIGN_TRIAGEM.md §3): colunas da mais grave para a mais
// leve, cartões de cima para baixo dentro de cada coluna.
function atrasoCartao(coluna: number, linha: number): number {
  return coluna * 50 + linha * 45;
}

function CartaoArea({
  area,
  nivel,
  destaque,
  atrasoMs,
  onAbrir,
  onPraticar,
}: {
  area: AreaDesempenho;
  nivel: NivelTriagem;
  destaque: boolean;
  atrasoMs: number;
  onAbrir: (areaId: number) => void;
  onPraticar: (areaId: number) => void;
}) {
  const fracao = (
    <span className="text-[13px] tabular-nums text-muted">
      {area.acertos.toLocaleString("pt-BR")}/{area.total}
    </span>
  );

  return (
    <div
      className="group relative flex animate-entrar flex-col gap-1.5 rounded-card border border-line bg-surface p-3.5 transition-colors duration-hover ease-brand hover:border-muted"
      style={{ animationDelay: `${atrasoMs}ms` }}
    >
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
        {destaque ? (
          fracao
        ) : (
          // Fração e atalho empilhados na mesma célula: no hover um sobe e some
          // enquanto o outro sobe e aparece. O cartão não cresce e a coluna não pula.
          <span className="grid justify-items-end">
            <span className="transition duration-toggle ease-brand [grid-area:1/1] group-focus-within:-translate-y-1 group-focus-within:opacity-0 group-hover:-translate-y-1 group-hover:opacity-0">
              {fracao}
            </span>
            <button
              type="button"
              onClick={() => onPraticar(area.area_id)}
              className="pointer-events-none relative z-10 flex translate-y-1 items-center gap-1 whitespace-nowrap text-[13px] font-semibold text-ink opacity-0 underline-offset-2 transition duration-toggle ease-brand [grid-area:1/1] hover:underline group-focus-within:pointer-events-auto group-focus-within:translate-y-0 group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100"
            >
              Praticar 10
              <ArrowRight size={14} strokeWidth={2} />
            </button>
          </span>
        )}
      </div>
      <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
        {/* Enche da esquerda ao entrar; se o valor muda depois, a largura desliza. */}
        <div
          className={`h-1 origin-left animate-crescer transition-[width] duration-cresce ease-suave ${CLASSES_NIVEL[nivel].cheio}`}
          style={{ width: `${area.pct_acerto}%`, animationDelay: `${atrasoMs + 120}ms` }}
        />
      </div>
      {destaque && (
        <button
          type="button"
          onClick={() => onPraticar(area.area_id)}
          className="group/praticar relative z-10 mt-2 flex h-9 items-center justify-center gap-1.5 rounded-btn bg-ink text-[14px] font-semibold text-onink transition duration-hover hover:opacity-90 active:scale-[0.97]"
        >
          Praticar 10
          <ArrowRight
            size={15}
            strokeWidth={2}
            className="transition-transform duration-toggle ease-suave group-hover/praticar:translate-x-0.5"
          />
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
        {colunas.map((col, c) => (
          <div key={col.nivel} className="flex flex-col gap-2.5">
            <div
              className={`flex h-10 animate-entrar items-center justify-between rounded-col px-3 ${CLASSES_NIVEL[col.nivel].cheio} ${CLASSES_NIVEL[col.nivel].texto}`}
              style={{ animationDelay: `${atrasoCartao(c, 0)}ms` }}
            >
              <span className="rotulo text-[14px]">{col.nome}</span>
              <span className="text-[15px] font-bold tabular-nums">{col.areas.length}</span>
            </div>
            {col.areas.length === 0 ? (
              // Só na tela larga (5 colunas lado a lado); empilhado, o cabeçalho com 0 já basta.
              <div
                className="hidden animate-entrar rounded-card border border-dashed border-line px-3.5 py-4 text-apoio text-muted xl:block"
                style={{ animationDelay: `${atrasoCartao(c, 1)}ms` }}
              >
                {col.nivel === 5 ? "Nenhuma área acima de 85% ainda." : "Nenhuma área nesta faixa."}
              </div>
            ) : (
              col.areas.map((a, linha) => (
                <CartaoArea
                  key={a.area_id}
                  area={a}
                  nivel={col.nivel}
                  destaque={a.area_id === idDestaque}
                  atrasoMs={atrasoCartao(c, linha + 1)}
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
        {/* db._PRIMEIRAS_TENTATIVAS: é o que explica um "14,5 acertos". */}
        <span>Acerto no chute vale meio</span>
        {insuficientes.length > 0 && (
          <span className="xl:ml-auto">
            Amostra insuficiente: {listaNatural(insuficientes.map((a) => a.area))}
          </span>
        )}
      </div>
    </section>
  );
}
