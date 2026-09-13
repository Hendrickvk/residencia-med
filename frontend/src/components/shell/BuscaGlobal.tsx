import { Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useBusca } from "../../lib/busca";
import { useDebounced } from "../../lib/useDebounced";

// MIGRACAO.md §5: "a busca global não é opcional: hoje ela é um campo que
// parece funcional e não busca nada, o que é pior que não existir." ILIKE
// real em enunciado de questão e título de material, agrupado por tipo —
// atalho "/" foca o campo (DESIGN_TRIAGEM.md §5).
export function BuscaGlobal() {
  const [termo, setTermo] = useState("");
  const [aberto, setAberto] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const termoDebounced = useDebounced(termo, 250);
  const { data, isFetching } = useBusca(termoDebounced);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "/") {
        const alvo = e.target as HTMLElement | null;
        if (alvo && ["INPUT", "TEXTAREA", "SELECT"].includes(alvo.tagName)) return;
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === "Escape") {
        setAberto(false);
        inputRef.current?.blur();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  const questoes = data?.questoes ?? [];
  const materiais = data?.materiais ?? [];
  const temResultados = questoes.length > 0 || materiais.length > 0;
  const mostrarPainel = aberto && termo.trim().length >= 2;

  return (
    <div className="relative hidden sm:block">
      <Search
        size={16}
        strokeWidth={2}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
      />
      <input
        ref={inputRef}
        type="search"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        onFocus={() => setAberto(true)}
        placeholder="Buscar"
        aria-label="Buscar questões e materiais (atalho /)"
        className="h-9 w-44 rounded-btn border border-line bg-surface pl-9 pr-8 text-apoio text-ink outline-none transition duration-hover placeholder:text-faint focus:border-ink xl:w-64"
      />
      {termo ? (
        <button
          type="button"
          onClick={() => {
            setTermo("");
            inputRef.current?.focus();
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-faint hover:text-ink"
          aria-label="Limpar busca"
        >
          <X size={14} strokeWidth={2} />
        </button>
      ) : (
        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded-etq border border-line px-1.5 text-[11px] font-semibold text-faint">
          /
        </span>
      )}

      {mostrarPainel && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setAberto(false)} />
          <div className="absolute right-0 top-11 z-50 max-h-96 w-[26rem] overflow-y-auto overflow-x-hidden rounded-card border border-line bg-surface">
            {isFetching && !data ? (
              <div className="p-4 text-apoio text-muted">Buscando…</div>
            ) : !temResultados ? (
              <div className="p-4 text-apoio text-muted">Nenhum resultado para "{termo}".</div>
            ) : (
              <div className="divide-y divide-line-soft">
                {questoes.length > 0 && (
                  <div className="p-2">
                    <div className="rotulo px-2 py-1.5 text-muted">Questões ({questoes.length})</div>
                    {questoes.map((q) => (
                      <div key={q.id} className="rounded-btn px-2 py-2">
                        <div className="truncate text-corpo text-ink">{q.enunciado}</div>
                        <div className="text-apoio text-muted">{q.area}</div>
                      </div>
                    ))}
                  </div>
                )}
                {materiais.length > 0 && (
                  <div className="p-2">
                    <div className="rotulo px-2 py-1.5 text-muted">Materiais ({materiais.length})</div>
                    {materiais.map((m) => (
                      <a
                        key={m.id}
                        href={m.link_mediafire}
                        target="_blank"
                        rel="noreferrer"
                        className="block truncate rounded-btn px-2 py-2 text-corpo text-ink transition duration-hover hover:bg-ground"
                      >
                        {m.titulo}
                        <span className="ml-2 text-apoio text-muted">{m.tipo}</span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
