import { dividirEmParagrafos } from "../lib/paragrafos";

// Discussão do caso e comentário do simulado: texto de leitura longa, em
// parágrafos (DESIGN_TRIAGEM.md §3 e §6).
export function TextoDiscussao({ texto }: { texto: string }) {
  return (
    <div className="flex flex-col gap-4">
      {dividirEmParagrafos(texto).map((paragrafo, i) => (
        <p key={i} className="leitura-discussao text-ink-2">
          {paragrafo}
        </p>
      ))}
    </div>
  );
}
