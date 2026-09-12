interface Props {
  quantidade: number;
  onRevisar: () => void;
}

export function RevisoesHoje({ quantidade, onRevisar }: Props) {
  if (quantidade === 0) {
    return <p className="text-corpo text-ink-500">Nenhuma revisão vencida hoje.</p>;
  }

  return (
    <div className="flex items-center justify-between rounded-panel border border-line bg-surface p-4">
      <span className="text-corpo text-ink-700">
        {quantidade} questõe{quantidade !== 1 && "s"} esperando revisão.
      </span>
      <button
        type="button"
        onClick={onRevisar}
        className="h-9 rounded-btn bg-action px-3 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        Revisar {quantidade} itens
      </button>
    </div>
  );
}
