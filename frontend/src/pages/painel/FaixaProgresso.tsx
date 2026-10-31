import { Link } from "react-router-dom";
import { BarraNivel } from "../../components/BarraNivel";
import { Moeda } from "../../components/Moeda";
import { formatarNumeroBR } from "../../lib/format";
import type { Me } from "../../lib/types";

interface Props {
  me: Me;
  bonus?: { feitos: number; total: number };
}

// Abaixo da Conduta de hoje, sem botão primário: o dela é o único da tela
// (DESIGN_TRIAGEM.md §6). A faixa inteira é o caminho para o Progresso. Os acertos em
// dobro somem quando acabam: faltar nada não é motivo para olhar.
export function FaixaProgresso({ me, bonus }: Props) {
  const { progresso } = me;
  const avisos = [
    me.ofensiva_protegida_ontem ? "Uma proteção segurou a sua ofensiva ontem." : null,
    // A hora vem pronta em Brasília, sem fuso: é só recortar.
    me.xp_dobro_ate ? `XP em dobro até as ${me.xp_dobro_ate.slice(11, 16)}.` : null,
  ].filter(Boolean);

  return (
    <Link
      to="/progresso"
      className="flex flex-col gap-2 rounded-card border border-line bg-surface px-5 py-3.5 transition duration-hover ease-brand hover:border-muted sm:px-6"
    >
      <span className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <span className="whitespace-nowrap text-corpo font-semibold text-ink">
          Nível {progresso.nivel} · {progresso.patente}
        </span>
        <span className="min-w-[80px] flex-1">
          <BarraNivel pct={progresso.pct} fina />
        </span>
        <span className="whitespace-nowrap text-apoio tabular-nums text-muted">
          Faltam {formatarNumeroBR(progresso.falta)} XP para o nível {progresso.nivel + 1}
        </span>
        {bonus && bonus.feitos < bonus.total && (
          <span className="flex items-center gap-1.5 whitespace-nowrap text-apoio tabular-nums text-muted sm:border-l sm:border-line-soft sm:pl-5">
            <Moeda tamanho={15} />
            Acertos em dobro hoje: {bonus.feitos} de {bonus.total}
          </span>
        )}
      </span>
      {avisos.length > 0 && <span className="text-apoio text-ink-2">{avisos.join(" ")}</span>}
    </Link>
  );
}
