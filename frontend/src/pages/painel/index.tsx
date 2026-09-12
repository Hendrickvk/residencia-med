import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { usePainel } from "../../lib/painel";
import { DiagnosticoPanel } from "./DiagnosticoPanel";
import { ListaErros } from "./ListaErros";
import { RevisoesHoje } from "./RevisoesHoje";

export default function Painel() {
  const { data, isLoading } = usePainel();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-40 animate-pulse rounded-panel bg-line/40" />
        <div className="h-48 animate-pulse rounded-panel bg-line/40" />
      </div>
    );
  }

  if (!data || data.totais.respostas === 0) {
    return (
      <EstadoVazio
        mensagem="Ainda não há respostas registradas para montar seu diagnóstico."
        cta={{ label: "Ir para Praticar", onClick: () => navigate("/praticar") }}
      />
    );
  }

  return (
    <div className="space-y-8">
      <DiagnosticoPanel
        totalResp={data.totais.respostas}
        totalAcertos={data.totais.acertos}
        pctGeral={data.totais.pct_acerto_geral}
        porArea={data.por_area}
        evolucao={data.evolucao_14_dias}
        respondidasHoje={data.respondidas_hoje}
        onContinuar={() => navigate("/praticar")}
      />

      <div>
        <h2 className="mb-3 text-corpo font-semibold text-ink-700">Onde você está errando</h2>
        <ListaErros
          areas={data.por_area}
          onClicarArea={(areaId) => navigate("/praticar", { state: { areaId } })}
          onPraticarArea={(areaId) =>
            navigate("/praticar", { state: { areaId, iniciarImediato: true, quantidade: 10 } })
          }
        />
      </div>

      <div>
        <h2 className="mb-3 text-corpo font-semibold text-ink-700">Revisões de hoje</h2>
        <RevisoesHoje quantidade={data.revisoes_hoje} onRevisar={() => navigate("/revisao")} />
      </div>
    </div>
  );
}
