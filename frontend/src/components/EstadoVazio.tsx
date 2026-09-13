import { BOTAO_PRIMARIO } from "../lib/estilos";

interface Props {
  mensagem: string;
  cta?: { label: string; onClick: () => void };
}

// DESIGN_TRIAGEM.md §4: caixa tracejada, uma frase que orienta e no máximo um botão.
export function EstadoVazio({ mensagem, cta }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-card border border-dashed border-line px-6 py-12 text-center">
      <p className="max-w-[52ch] text-corpo text-ink-2">{mensagem}</p>
      {cta && (
        <button type="button" onClick={cta.onClick} className={BOTAO_PRIMARIO}>
          {cta.label}
        </button>
      )}
    </div>
  );
}
