import { useEffect } from "react";
import { Link } from "react-router-dom";
import { BarraNivel } from "../../components/BarraNivel";
import { Carimbo } from "../../components/Carimbo";
import { EstadoFalha } from "../../components/EstadoFalha";
import { Moeda } from "../../components/Moeda";
import { BOTAO_SECUNDARIO } from "../../lib/estilos";
import { avisarCarimbos, useCaderneta } from "../../lib/progresso";

// A caderneta: uma ficha de doses, com cada carimbo na sua célula.
export default function PaginaConquistas() {
  const { data, isLoading, isPaused, refetch } = useCaderneta();
  const temNovas = !!data?.novas.length;

  // Abrir a caderneta também carimba: as moedas entraram, e o saldo precisa saber.
  useEffect(() => {
    if (temNovas) avisarCarimbos();
  }, [temNovas]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-7">
        <div className="h-[46px] w-72 animate-pulse rounded-card bg-line-soft" />
        <div className="h-[220px] animate-pulse rounded-caso bg-line-soft" />
        <div className="h-[220px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  if (!data) {
    return (
      <EstadoFalha
        mensagem="Não deu para carregar a caderneta. Pode ser a conexão."
        pausado={isPaused}
        onTentarDeNovo={() => refetch()}
      />
    );
  }

  let ordem = 0;
  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-wrap items-center justify-between gap-3.5">
        <h1 className="text-titulo tabular-nums">
          {data.obtidos} de {data.total} carimbos.
        </h1>
        <Link to="/progresso" className={BOTAO_SECUNDARIO}>
          Ver seu perfil
        </Link>
      </div>

      {data.series.map((serie) => (
        <section key={serie.nome} className="flex flex-col gap-3">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="text-bloco">{serie.nome}</h2>
            <span className="text-apoio tabular-nums text-muted">
              {serie.feitos} de {serie.qtd}
            </span>
          </div>
          <ul className="grid grid-cols-2 overflow-hidden rounded-caso border border-line bg-surface md:grid-cols-3 xl:grid-cols-6">
            {serie.itens.map((item) => (
              <li
                key={item.id}
                className="-mb-px -mr-px flex min-h-[164px] min-w-0 flex-col items-center justify-between gap-3 border-b border-r border-line-soft px-3 pb-3.5 pt-[18px] text-center"
              >
                <Carimbo nome={item.nome} grau={item.grau} obtidaEm={item.obtida_em} ordem={ordem++} />
                <div className="flex w-full flex-col items-center gap-1.5">
                  {item.pct !== null && (
                    <div className="w-[72%]">
                      <BarraNivel pct={item.pct} fina />
                    </div>
                  )}
                  <span className="text-apoio tabular-nums text-muted">{item.obtida_em ? "Carimbado" : item.nota}</span>
                  <span
                    className={`flex items-center gap-1 text-apoio font-semibold tabular-nums ${
                      item.obtida_em ? "text-ink" : "text-muted"
                    }`}
                  >
                    <Moeda tamanho={14} />
                    {item.obtida_em ? "+" : ""}
                    {item.moedas}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
