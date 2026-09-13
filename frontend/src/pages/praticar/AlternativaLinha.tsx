export type EstadoAlternativa = "normal" | "selecionada" | "correta" | "errada" | "neutra";

interface Props {
  letra: string;
  texto: string;
  estado: EstadoAlternativa;
  // undefined: resposta ainda não confirmada (sem coluna de percentual).
  // null: confirmada, mas a distribuição ainda não chegou — a coluna já fica
  // reservada para nada se deslocar quando o número aparecer (MIGRACAO.md §0).
  percentual?: number | null;
  onClick?: () => void;
  disabled: boolean;
}

// Nos estados com borda de 2px o padding perde 1px, para a linha não crescer
// na hora da revelação (DESIGN_TRIAGEM.md §4).
const caixa: Record<EstadoAlternativa, string> = {
  normal: "border border-line bg-surface py-3 pl-3 pr-3.5 text-ink hover:border-muted",
  selecionada: "border-2 border-ink bg-surface py-[11px] pl-[11px] pr-[13px] text-ink",
  correta: "border-2 border-t4 bg-t4-soft py-[11px] pl-[11px] pr-[13px] text-ink",
  errada: "border-2 border-t1 bg-t1-soft py-[11px] pl-[11px] pr-[13px] text-ink",
  neutra: "border border-line bg-surface py-3 pl-3 pr-3.5 text-muted",
};

const quadrado: Record<EstadoAlternativa, string> = {
  normal: "bg-ground text-muted",
  selecionada: "bg-ink text-onink",
  correta: "bg-t4 text-t4-on",
  errada: "bg-t1 text-t1-on",
  neutra: "bg-ground text-faint",
};

export function AlternativaLinha({ letra, texto, estado, percentual, onClick, disabled }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={estado === "selecionada"}
      className={`grid w-full grid-cols-[32px_minmax(0,1fr)_auto] items-center gap-3.5 rounded-card text-left text-corpo transition-[background-color,border-color] duration-toggle ease-brand ${caixa[estado]} ${
        disabled ? "cursor-default" : "cursor-pointer"
      }`}
    >
      <span
        className={`flex h-8 w-8 items-center justify-center rounded-col text-[15px] font-extrabold transition-colors duration-toggle ease-brand ${quadrado[estado]}`}
      >
        {letra}
      </span>
      <span>{texto}</span>
      {percentual !== undefined ? (
        <span className="flex items-center gap-2.5">
          {estado === "correta" && (
            <span className="rotulo whitespace-nowrap rounded-etq bg-t4 px-2 py-1 text-[12px] text-t4-on">Conduta correta</span>
          )}
          {estado === "errada" && (
            <span className="rotulo whitespace-nowrap rounded-etq bg-t1 px-2 py-1 text-[12px] text-t1-on">Sua conduta</span>
          )}
          <span className="w-9 text-right text-apoio font-semibold tabular-nums text-muted">
            {percentual === null ? "" : `${Math.round(percentual)}%`}
          </span>
        </span>
      ) : (
        <span />
      )}
    </button>
  );
}
