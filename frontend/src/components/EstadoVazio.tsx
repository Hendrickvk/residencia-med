interface Props {
  mensagem: string;
  cta?: { label: string; onClick: () => void };
}

// REDESIGN.md §5: "uma frase que orienta e um único botão de ação. Sem ilustração."
export function EstadoVazio({ mensagem, cta }: Props) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-panel border border-line bg-surface p-10 text-center">
      <p className="text-corpo text-ink-500">{mensagem}</p>
      {cta && (
        <button
          type="button"
          onClick={cta.onClick}
          className="h-10 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
        >
          {cta.label}
        </button>
      )}
    </div>
  );
}
