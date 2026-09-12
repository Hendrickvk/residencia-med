import { Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useBusca } from "../../lib/busca";
import { useDebounced } from "../../lib/useDebounced";

// MIGRACAO.md §5: "a busca global não é opcional: hoje ela é um campo que
// parece funcional e não busca nada, o que é pior que não existir." LIKE
// real em enunciado de questão e título de material, agrupado por tipo —
// atalho "/" foca o campo (REDESIGN.md §3).
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
        size={14}
        strokeWidth={1.5}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-300"
      />
      <input
        ref={inputRef}
        type="search"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        onFocus={() => setAberto(true)}
        placeholder="Buscar... (/)"
        className="h-8 w-48 rounded-btn border border-line bg-canvas pl-8 pr-7 text-apoio text-ink-700 outline-none placeholder:text-ink-300 focus:border-action focus:ring-[3px] focus:ring-action-soft lg:w-64"
      />
      {termo && (
        <button
          type="button"
          onClick={() => {
            setTermo("");
            inputRef.current?.focus();
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-300 hover:text-ink-500"
          aria-label="Limpar busca"
        >
          <X size={14} strokeWidth={1.5} />
        </button>
      )}

      {mostrarPainel && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setAberto(false)} />
          <div className="absolute right-0 top-10 z-50 max-h-96 w-96 overflow-y-auto overflow-x-hidden rounded-panel border border-line bg-surface shadow-sm">
            {isFetching && !data ? (
              <div className="p-4 text-apoio text-ink-500">Buscando...</div>
            ) : !temResultados ? (
              <div className="p-4 text-apoio text-ink-500">Nenhum resultado para "{termo}".</div>
            ) : (
              <div className="divide-y divide-line">
                {questoes.length > 0 && (
                  <div className="p-2">
                    <div className="px-2 py-1 text-apoio font-medium uppercase tracking-wide text-ink-300">
                      Questões ({questoes.length})
                    </div>
                    {questoes.map((q) => (
                      <div key={q.id} className="rounded-btn px-2 py-2">
                        <div className="truncate text-corpo text-ink-700">{q.enunciado}</div>
                        <div className="text-apoio text-ink-500">{q.area}</div>
                      </div>
                    ))}
                  </div>
                )}
                {materiais.length > 0 && (
                  <div className="p-2">
                    <div className="px-2 py-1 text-apoio font-medium uppercase tracking-wide text-ink-300">
                      Materiais ({materiais.length})
                    </div>
                    {materiais.map((m) => (
                      <a
                        key={m.id}
                        href={m.link_mediafire}
                        target="_blank"
                        rel="noreferrer"
                        className="block truncate rounded-btn px-2 py-2 text-corpo text-ink-700 transition-hover hover:bg-canvas"
                      >
                        {m.titulo}
                        <span className="ml-2 text-apoio text-ink-500">{m.tipo}</span>
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
