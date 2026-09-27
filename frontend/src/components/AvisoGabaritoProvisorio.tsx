import { Info } from "lucide-react";

// Prova publicada antes do gabarito definitivo do INEP (db.EDICOES_GABARITO_PRELIMINAR).
// Aparece onde a resposta certa aparece — a discussão do caso e o resultado da prova —,
// porque é ali que a aluna toma o gabarito como verdade. Uma frase só, a pedido do
// usuário: direto, sem explicar demais. Dentro do cartão do caso, o fundo é o da página;
// no resultado, que já está sobre a página, é o do cartão.
export function AvisoGabaritoProvisorio({ fundo = "bg-ground" }: { fundo?: "bg-ground" | "bg-surface" }) {
  return (
    <p className={`flex items-start gap-2.5 rounded-card border border-line ${fundo} px-4 py-3 text-apoio text-ink-2`}>
      <Info className="mt-0.5 shrink-0" size={16} strokeWidth={2} aria-hidden="true" />
      <span>
        <strong className="font-semibold text-ink">Gabarito provisório.</strong> O oficial do INEP sai em dezembro.
      </span>
    </p>
  );
}
