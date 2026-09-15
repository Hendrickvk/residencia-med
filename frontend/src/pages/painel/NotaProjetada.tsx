import { ArrowRight } from "lucide-react";
import { EtiquetaPct } from "../../components/EtiquetaPct";
import { BOTAO_SECUNDARIO } from "../../lib/estilos";
import { formatarPctBR } from "../../lib/format";
import { nomeEdicao } from "../../lib/simulados";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";
import type { NotaProjetada as DadosNota, SimuladoOficialFeito } from "../../lib/types";

interface Props {
  nota: DadosNota;
  simulados: SimuladoOficialFeito[];
  onFazerProva: () => void;
}

// DESIGN_TRIAGEM.md §6, Painel ("Nota projetada", db.nota_projetada): a nota que o
// domínio de hoje dá numa prova do INEP, ao lado das provas oficiais já feitas.
export function NotaProjetada({ nota, simulados, onFazerProva }: Props) {
  const nivel = nivelTriagem(nota.nota);
  return (
    <section className="flex flex-col gap-5 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="rotulo text-muted">Nota projetada na prova</span>
        <span className="text-apoio text-muted">seu domínio em cada tema, com o peso dele no Revalida e no ENAMED</span>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-10">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <span className="num-lg">{formatarPctBR(nota.nota, 0)}%</span>
            <span className={`rotulo rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}>
              {NIVEIS[nivel - 1].nome}
            </span>
          </div>
          <p className="text-corpo text-ink-2">
            Provavelmente entre {formatarPctBR(nota.minimo, 0)}% e {formatarPctBR(nota.maximo, 0)}% numa prova de 100
            questões.
          </p>
          <p className="text-apoio text-muted [text-wrap:pretty]">
            A faixa diminui conforme você responde, até cerca de 10 pontos para cada lado: a variação de uma prova só.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <span className="rotulo text-muted">Provas oficiais feitas</span>
          {simulados.length === 0 ? (
            <>
              <p className="text-corpo text-ink-2">
                Nenhuma ainda. Um caderno inteiro no tempo oficial é a melhor forma de conferir a projeção.
              </p>
              <button type="button" onClick={onFazerProva} className={`group self-start ${BOTAO_SECUNDARIO}`}>
                Fazer uma prova oficial
                <ArrowRight
                  size={16}
                  strokeWidth={2}
                  className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5"
                />
              </button>
            </>
          ) : (
            <ul className="flex flex-col divide-y divide-line-soft">
              {simulados.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-4 py-2.5 first:pt-0 last:pb-0">
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate text-corpo font-semibold">{nomeEdicao(s.banca, s.edicao)}</span>
                    <span className="text-apoio text-muted">
                      {new Date(s.finalizado_em).toLocaleDateString("pt-BR")}
                      {/* O banco é feito dos cadernos: questão já vista mede memória, não preparo. */}
                      {s.ja_vistas > 0 && ` · já tinha visto ${s.ja_vistas} das ${s.num_questoes}`}
                    </span>
                  </span>
                  <EtiquetaPct pct={s.pct_acerto} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
