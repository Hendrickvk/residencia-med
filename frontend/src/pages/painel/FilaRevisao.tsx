import { BOTAO_PRIMARIO } from "../../lib/estilos";

interface Props {
  quantidade: number;
  onRevisar: () => void;
}

export function FilaRevisao({ quantidade, onRevisar }: Props) {
  return (
    <div className="flex flex-col gap-3.5 rounded-card border border-line bg-surface p-6">
      <span className="rotulo text-muted">Fila de revisão</span>
      {quantidade === 0 ? (
        <p className="text-corpo text-ink-2">Nenhuma questão vencida hoje. As que você errar voltam para cá.</p>
      ) : (
        <div className="flex items-baseline gap-3.5">
          <span className="num-lg">{quantidade}</span>
          <span className="max-w-[22ch] text-corpo leading-snug text-ink-2">
            {quantidade === 1 ? "questão aguardando reavaliação hoje" : "questões aguardando reavaliação hoje"}
          </span>
        </div>
      )}
      {/* Sempre habilitado: a fila da Revisão também traz marcadas e nunca revisadas. */}
      <button type="button" onClick={onRevisar} className={`${BOTAO_PRIMARIO} mt-auto w-full`}>
        Revisar agora
      </button>
    </div>
  );
}
