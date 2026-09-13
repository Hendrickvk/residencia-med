import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { useMe } from "../../lib/auth";
import { usePainel } from "../../lib/painel";
import { Cabecalho } from "./Cabecalho";
import { EvolucaoTriagem } from "./EvolucaoTriagem";
import { FilaRevisao } from "./FilaRevisao";
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
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <FilaRevisao quantidade={data.revisoes_hoje} onRevisar={() => navigate("/revisao")} />
        <EvolucaoTriagem evolucao={data.evolucao_14_dias} />
      </div>
    </div>
  );
}
