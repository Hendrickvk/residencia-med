import { useEffect, useState } from "react";
import { usarRespostasPendentes } from "../lib/respostasQueue";

const ATRASO_PARA_AVISAR_MS = 4000;

// Aviso discreto só quando a fila de respostas NÃO drena rápido (MIGRACAO.md
// §2) — a maioria das gravações termina em milissegundos e nunca deveria
// piscar um toast pra isso.
export function FilaPendenteAviso() {
  const pendentes = usarRespostasPendentes();
  const [mostrar, setMostrar] = useState(false);

  useEffect(() => {
    if (pendentes === 0) {
      setMostrar(false);
      return;
    }
    const timer = setTimeout(() => setMostrar(true), ATRASO_PARA_AVISAR_MS);
    return () => clearTimeout(timer);
  }, [pendentes]);

  if (!mostrar || pendentes === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 rounded-panel border border-line bg-surface px-4 py-3 text-apoio text-ink-500 shadow-sm">
      {pendentes} resposta{pendentes !== 1 && "s"} aguardando envio...
    </div>
  );
}
