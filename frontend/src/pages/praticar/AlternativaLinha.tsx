type EstadoAlternativa = "normal" | "selecionada" | "correta" | "errada" | "neutra";

interface Props {
  letra: string;
  texto: string;
  estado: EstadoAlternativa;
  percentual?: number;
  onClick?: () => void;
  disabled: boolean;
}

const borda: Record<EstadoAlternativa, string> = {
  normal: "border-line hover:border-action hover:bg-action-soft",
  selecionada: "border-2 border-action",
  correta: "border-correct bg-correct-soft",
  errada: "border-wrong bg-wrong-soft",
  neutra: "border-line opacity-60",
};

const quadrado: Record<EstadoAlternativa, string> = {
  normal: "border-line text-ink-500",
  selecionada: "border-action bg-action text-white",
  correta: "border-correct bg-correct text-white",
  errada: "border-wrong bg-wrong text-white",
  neutra: "border-line text-ink-500",
};

export function AlternativaLinha({ letra, texto, estado, percentual, onClick, disabled }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`relative flex min-h-[52px] w-full items-center gap-3 overflow-hidden rounded-btn border px-3 text-left text-corpo text-ink-700 transition-[background-color,border-color] duration-toggle ease-brand ${borda[estado]} ${
        disabled ? "cursor-default" : "cursor-pointer"
      }`}
    >
      {percentual !== undefined && (
        <span className="absolute inset-y-0 left-0 bg-ink-300/15" style={{ width: `${percentual}%` }} aria-hidden="true" />
      )}
      <span className={`relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-btn border text-apoio font-medium ${quadrado[estado]}`}>
        {letra}
      </span>
      <span className="relative z-10">{texto}</span>
      {percentual !== undefined && (
        <span className="relative z-10 ml-auto font-mono text-apoio tabular-nums text-ink-500">{percentual.toFixed(0)}%</span>
      )}
    </button>
  );
}
