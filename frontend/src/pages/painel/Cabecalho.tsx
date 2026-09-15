import { NumeroAnimado } from "../../components/NumeroAnimado";
import { formatarPctBR } from "../../lib/format";
import { MINIMO_AMOSTRA, VOLUME_CONFIAVEL } from "../../lib/triagem";
import type { AreaDesempenho, PainelData } from "../../lib/types";

const META_DIARIA = 20;

const DIAS_SEMANA = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"];
const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

interface Props {
  totais: PainelData["totais"];
  porArea: AreaDesempenho[];
  respondidasHoje: number;
  provaAlvo: string | null;
}

function diasAteProva(provaAlvo: string | null): number | null {
  if (!provaAlvo) return null;
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const dias = Math.round((new Date(`${provaAlvo}T00:00:00`).getTime() - hoje.getTime()) / 86_400_000);
  return dias >= 0 ? dias : null;
}

// DESIGN_TRIAGEM.md §6, Painel item 1.
export function Cabecalho({ totais, porArea, respondidasHoje, provaAlvo }: Props) {
  const hoje = new Date();
  const dataExtenso = `${DIAS_SEMANA[hoje.getDay()]}, ${hoje.getDate()} de ${MESES[hoje.getMonth()]}`;
  const maiorLacuna = porArea
    .filter((a) => a.total >= MINIMO_AMOSTRA)
    .sort((a, b) => a.pct_acerto - b.pct_acerto)[0];
  const volumeBaixo = totais.respostas < VOLUME_CONFIAVEL;

  let titulo = "Nenhuma área com amostra suficiente ainda.";
  if (volumeBaixo) titulo = "Volume ainda baixo para conclusões.";
  else if (maiorLacuna) titulo = `${maiorLacuna.area} é a sua maior lacuna.`;

  const dias = diasAteProva(provaAlvo);
  const resumo = [
    `${totais.acertos.toLocaleString("pt-BR")} acertos em ${totais.respostas.toLocaleString("pt-BR")} questões`,
    `${respondidasHoje} de ${META_DIARIA} questões hoje`,
    dias !== null ? `prova em ${dias} dia${dias !== 1 ? "s" : ""}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
      <div className="flex max-w-[780px] flex-col gap-2.5">
        <span className="rotulo text-muted">Triagem de hoje · {dataExtenso}</span>
        <h1 className="text-titulo [text-wrap:balance] max-md:text-[34px]">{titulo}</h1>
        <p className="text-corpo text-ink-2">{resumo}</p>
        {volumeBaixo && (
          <p className="text-apoio text-muted">
            Responda mais {VOLUME_CONFIAVEL - totais.respostas} questões para a triagem ficar confiável.
          </p>
        )}
      </div>
      <div className="flex shrink-0 flex-col gap-1.5 md:items-end">
        <span className="rotulo text-muted">Aproveitamento geral</span>
        <NumeroAnimado
          className="num-xl self-start max-md:text-[64px] md:self-auto"
          valor={totais.pct_acerto_geral}
          formatar={(v) => `${formatarPctBR(v)}%`}
          chave="painel-aproveitamento"
        />
      </div>
    </div>
  );
}
