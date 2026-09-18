import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { RelatoResolvidoAviso } from "../../components/RelatoResolvidoAviso";
import { useMe } from "../../lib/auth";
import { usePainel } from "../../lib/painel";
import { VOLUME_CONFIAVEL } from "../../lib/triagem";
import { Cabecalho } from "./Cabecalho";
import { EvolucaoMemoria } from "./EvolucaoMemoria";
import { EvolucaoTriagem } from "./EvolucaoTriagem";
import { FilaRevisao } from "./FilaRevisao";
import { NotaProjetada } from "./NotaProjetada";
import { PorTipoPergunta } from "./PorTipoPergunta";
import { PrioridadesEstudo } from "./PrioridadesEstudo";
import { ProgressoSemana } from "./ProgressoSemana";
import { QuadroTriagem } from "./QuadroTriagem";

export default function Painel() {
  const { data, isLoading } = usePainel();
  const { data: me } = useMe();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-7">
        <div className="h-[150px] animate-pulse rounded-card bg-line-soft" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="h-[300px] animate-pulse rounded-card bg-line-soft" />
          ))}
        </div>
        <div className="h-[240px] animate-pulse rounded-card bg-line-soft" />
        <div className="h-[280px] animate-pulse rounded-card bg-line-soft" />
      </div>
    );
  }

  if (!data || data.totais.respostas === 0) {
    return (
      <EstadoVazio
        mensagem="Ainda não há respostas para montar a sua triagem. Responda alguns casos e ela aparece aqui."
        cta={{ label: "Praticar agora", onClick: () => navigate("/praticar") }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-7">
      <RelatoResolvidoAviso />
      <Cabecalho
        totais={data.totais}
        porArea={data.por_area}
        respondidasHoje={data.respondidas_hoje}
        provaAlvo={me?.prova_alvo ?? null}
      />
      <QuadroTriagem
        areas={data.por_area}
        onAbrir={(areaId) => navigate("/praticar", { state: { areaId } })}
        onPraticar={(areaId) => navigate("/praticar", { state: { areaId, iniciarImediato: true, quantidade: 10 } })}
      />
      {/* Entram depois do quadro, que chega em cascata. */}
      {data.nota_projetada && data.nota_projetada.respondidas >= VOLUME_CONFIAVEL && (
        <div className="animate-entrar" style={{ animationDelay: "260ms" }}>
          <NotaProjetada
            nota={data.nota_projetada}
            simulados={data.simulados_oficiais}
            onFazerProva={() => navigate("/simulado")}
          />
        </div>
      )}
      {data.prioridades.length > 0 && (
        <div className="animate-entrar" style={{ animationDelay: "300ms" }}>
          <PrioridadesEstudo
            prioridades={data.prioridades}
            onPraticar={(p, quantidade) =>
              navigate("/praticar", {
                state: {
                  areaId: p.area_id,
                  especialidadeId: p.especialidade_id,
                  subtopicoId: p.subtopico_id,
                  iniciarImediato: true,
                  quantidade,
                },
              })
            }
          />
        </div>
      )}
      {data.semana.novas > 0 && (
        <div className="animate-entrar" style={{ animationDelay: "340ms" }}>
          <ProgressoSemana
            semana={data.semana}
            onPraticar={(t, quantidade) =>
              navigate("/praticar", {
                state: {
                  areaId: t.area_id,
                  especialidadeId: t.especialidade_id,
                  subtopicoId: t.subtopico_id,
                  iniciarImediato: true,
                  quantidade,
                },
              })
            }
          />
        </div>
      )}
      {data.por_tipo.some((t) => t.total > 0) && (
        <div className="animate-entrar" style={{ animationDelay: "380ms" }}>
          <PorTipoPergunta
            tipos={data.por_tipo}
            onPraticar={(tipo) =>
              navigate("/praticar", { state: { tipoPergunta: tipo, iniciarImediato: true, quantidade: 10 } })
            }
          />
        </div>
      )}
      <div
        className="grid animate-entrar grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]"
        style={{ animationDelay: "420ms" }}
      >
        <FilaRevisao revisao={data.revisao} onRevisar={() => navigate("/revisao")} />
        <EvolucaoTriagem evolucao={data.evolucao_14_dias} />
      </div>
      <div className="animate-entrar" style={{ animationDelay: "460ms" }}>
        <EvolucaoMemoria memoria={data.memoria} />
      </div>
    </div>
  );
}
