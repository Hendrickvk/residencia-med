import { useEffect, useState } from "react";
import { Maximize2 } from "lucide-react";
import { API_URL } from "../lib/api";
import { usePresenca } from "../lib/movimento";

// Recortes de caderno variam muito de proporção: a questão 70 da USP 2026 é uma
// tira de 628x1933 (quase 1 800 px renderizados), que empurrava as alternativas
// duas telas e meia para baixo. A imagem entra limitada à altura da janela e
// abre em tela cheia ao clique, onde dá para ler os detalhes.
const ALTURA_MAXIMA = "max-h-[70vh]";

export function ImagemQuestao({ questaoId, alt }: { questaoId: number; alt: string }) {
  const [aberta, setAberta] = useState(false);
  const { montado, saindo } = usePresenca(aberta);

  useEffect(() => {
    if (!aberta) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setAberta(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [aberta]);

  const src = `${API_URL}/questoes/${questaoId}/imagem`;

  return (
    <>
      {/* A caixa é que tem altura limitada, não a imagem: assim um recorte em
          tira continua em largura cheia, legível, e rola por dentro, em vez de
          virar miniatura ao caber inteiro na tela. */}
      <div className={`group relative ${ALTURA_MAXIMA} overflow-auto rounded-card border border-line`}>
        <button
          type="button"
          onClick={() => setAberta(true)}
          aria-label="Ampliar imagem"
          className="block w-full cursor-zoom-in focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus"
        >
          <img src={src} alt={alt} className="w-full" />
        </button>
        <span className="pointer-events-none sticky bottom-2 left-[calc(100%-6.5rem)] flex w-fit items-center gap-1 rounded-btn bg-ink/80 px-2 py-1 text-[12px] font-medium text-onink opacity-0 transition duration-hover ease-brand group-hover:opacity-100">
          <Maximize2 size={12} strokeWidth={2} />
          Ampliar
        </span>
      </div>

      {montado && (
        <div
          className={`fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 ${
            saindo ? "animate-desvanecer-saida" : "animate-desvanecer"
          }`}
          onClick={() => setAberta(false)}
          role="dialog"
          aria-modal="true"
          aria-label={alt}
        >
          {/* A imagem em tela cheia rola sozinha quando é mais alta que a
              janela — é o caso dos recortes em tira. */}
          <div className="max-h-full w-full max-w-4xl overflow-auto" onClick={(e) => e.stopPropagation()}>
            <img src={src} alt={alt} className="mx-auto w-auto max-w-full rounded-card" />
          </div>
          <button
            type="button"
            onClick={() => setAberta(false)}
            className="absolute right-4 top-4 rounded-btn bg-surface px-3 py-1.5 text-[14px] font-medium text-ink"
          >
            Fechar
          </button>
        </div>
      )}
    </>
  );
}
