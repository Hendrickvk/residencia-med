import { RotateCcw } from "lucide-react";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { BOTAO_PRIMARIO } from "../../lib/estilos";
import { formatarMMSS, formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";
import type { ResumoSessao } from "../../lib/types";

interface Props {
  resumo: ResumoSessao;
  onNovaSessao: () => void;
}

export default function Resumo({ resumo, onNovaSessao }: Props) {
  const { respondidas, duracaoTotalMs } = resumo;
  const n = respondidas.length;
  const acertos = respondidas.filter((r) => r.correta).length;
  const erros = n - acertos;
  const pctAcerto = n ? Math.round((100 * acertos) / n) : 0;
  const tempoMedioSeg = n ? Math.round(respondidas.reduce((s, r) => s + r.tempoMs, 0) / n / 1000) : 0;
  const nivel = n ? nivelTriagem(pctAcerto) : null;

  const porEspecialidade = new Map<string, { total: number; acertos: number }>();
  for (const r of respondidas) {
    const chave = r.especialidade ?? r.area;
    const atual = porEspecialidade.get(chave) ?? { total: 0, acertos: 0 };
    atual.total += 1;
    if (r.correta) atual.acertos += 1;
    porEspecialidade.set(chave, atual);
  }
  // Do pior para o melhor, como no quadro de triagem do Painel.
  const assuntos = [...porEspecialidade.entries()]
    .map(([assunto, v]) => ({ assunto, ...v, pct: (100 * v.acertos) / v.total }))
    .sort((a, b) => a.pct - b.pct);

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Resumo da sessão</span>
        <h1 className="text-titulo">{n ? `${acertos} de ${n} casos certos.` : "Nenhum caso respondido."}</h1>
      </div>

      <div className="grid grid-cols-1 divide-y divide-line-soft rounded-caso border border-line bg-surface sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Aproveitamento</span>
          {n ? (
            <NumeroAnimado className="num-lg self-start" valor={pctAcerto} formatar={(v) => `${Math.round(v)}%`} />
          ) : (
            <span className="num-lg">—</span>
          )}
          {nivel && (
            // Carimbada quando a contagem termina.
            <span
              className={`rotulo animate-surgir self-start rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
              style={{ animationDelay: "750ms" }}
            >
              {NIVEIS[nivel - 1].nome}
            </span>
          )}
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Tempo médio por caso</span>
          <span className="num-lg">{n ? `${tempoMedioSeg}s` : "—"}</span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Duração total</span>
          <span className="num-lg">{formatarMMSS(duracaoTotalMs)}</span>
        </div>
      </div>

      {assuntos.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-bloco">Desempenho por especialidade</h2>
          <div className="rounded-caso border border-line bg-surface">
            {assuntos.map((a, i) => {
              const nv = nivelTriagem(a.pct);
              return (
                // No celular o nome ganha a linha de cima: numa linha só, a
                // barra (`minmax` com teto fixo) cresce antes da coluna `1fr`,
                // e a 393px o nome da especialidade sumia inteiro.
                <div
                  key={a.assunto}
                  className="grid animate-entrar grid-cols-[minmax(0,1fr)_52px_48px] items-center gap-x-4 gap-y-1.5 border-b border-line-soft px-5 py-3 last:border-0 sm:grid-cols-[minmax(0,1fr)_minmax(80px,200px)_52px_48px]"
                  style={atraso(i + 2, 50)}
                >
                  <span className="truncate text-corpo max-sm:col-span-3">{a.assunto}</span>
                  <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                    <div
                      className={`h-1 origin-left animate-crescer ${CLASSES_NIVEL[nv].cheio}`}
                      style={{ width: `${a.pct}%`, ...atraso(i + 4, 50) }}
                    />
                  </div>
                  <span className="text-right text-apoio font-semibold tabular-nums">{formatarPctBR(a.pct, 0)}%</span>
                  <span className="text-right text-apoio tabular-nums text-muted">
                    {a.acertos}/{a.total}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {erros > 0 && (
        <p className="text-apoio text-ink-2">
          {erros === 1 ? "O caso que você errou já está" : `Os ${erros} casos que você errou já estão`} na sua revisão
          espaçada e voltam em 10 minutos.
        </p>
      )}

      <div>
        <button type="button" onClick={onNovaSessao} className={`group ${BOTAO_PRIMARIO}`}>
          <RotateCcw
            size={16}
            strokeWidth={2}
            className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]"
          />
          Nova sessão
        </button>
      </div>
    </div>
  );
}
