import { ChevronDown } from "lucide-react";
import { type ReactNode, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import { RelatoResolvidoAviso } from "../../components/RelatoResolvidoAviso";
import { useMe } from "../../lib/auth";
import { usePainel } from "../../lib/painel";
import { VOLUME_CONFIAVEL } from "../../lib/triagem";
import type { PrioridadeEstudo } from "../../lib/types";
import { Cabecalho } from "./Cabecalho";
import { CondutaHoje } from "./CondutaHoje";
import { EvolucaoMemoria } from "./EvolucaoMemoria";
import { EvolucaoTriagem } from "./EvolucaoTriagem";
import { NotaProjetada } from "./NotaProjetada";
import { PorTipoPergunta } from "./PorTipoPergunta";
import { PrevisaoSemana } from "./PrevisaoSemana";
import { PrioridadesEstudo } from "./PrioridadesEstudo";
import { ProgressoSemana } from "./ProgressoSemana";
import { QuadroTriagem } from "./QuadroTriagem";

const CHAVE_EVOLUCAO = "residencia-med:painel-evolucao-aberta";

function evolucaoAberta() {
  try {
    return localStorage.getItem(CHAVE_EVOLUCAO) === "1";
  } catch {
    return false;
  }
}

// Os gráficos de acompanhamento ficam recolhidos por padrão: o Painel abre no
// que fazer hoje e no diagnóstico, e a evolução é para quando ela quiser olhar.
// Quem abre uma vez encontra aberta da próxima (preferência do aparelho, por
// isso `localStorage`). Fechada, nada lá dentro é desenhado.
function SecaoEvolucao({ children }: { children: ReactNode }) {
  const [aberta, setAberta] = useState(evolucaoAberta);

  function alternar() {
    const nova = !aberta;
    setAberta(nova);
    try {
      localStorage.setItem(CHAVE_EVOLUCAO, nova ? "1" : "0");
    } catch {
      // Sem armazenamento (aba privada): só não lembra na próxima visita.
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <button
        type="button"
        onClick={alternar}
        aria-expanded={aberta}
        className="flex items-center justify-between gap-4 rounded-card border border-line bg-surface px-5 py-4 text-left transition duration-hover ease-brand hover:border-muted sm:px-6"
      >
        <span className="flex flex-col gap-1">
          <span className="rotulo text-muted">Evolução</span>
          <span className="text-apoio text-ink-2">Memória, tipos de pergunta, os últimos 14 dias e as revisões dos próximos 7</span>
        </span>
        <ChevronDown
          size={20}
          strokeWidth={2}
          className={`shrink-0 text-muted transition-transform duration-toggle ease-suave ${aberta ? "rotate-180" : ""}`}
        />
      </button>
      {aberta && <div className="flex animate-entrar flex-col gap-3">{children}</div>}
    </section>
  );
}

export default function Painel() {
  const { data, isLoading, isPaused, refetch } = usePainel();
  const { data: me } = useMe();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-7">
        <div className="h-[150px] animate-pulse rounded-card bg-line-soft" />
        <div className="h-[200px] animate-pulse rounded-card bg-line-soft" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="h-[300px] animate-pulse rounded-card bg-line-soft" />
          ))}
        </div>
      </div>
    );
  }

  // Sem `data` depois do skeleton só pode ser falha — e falha não é "você ainda
  // não praticou", que é o pior jeito de errar com quem tem histórico. A ordem
  // importa: com dado em cache a tela segue, mesmo que o refetch tenha falhado
  // (mesma regra do RequireAuth).
  if (!data) {
    return (
      <EstadoFalha
        mensagem="Não deu para carregar a sua triagem. Pode ser a conexão."
        pausado={isPaused}
        onTentarDeNovo={() => refetch()}
      />
    );
  }

  if (data.totais.respostas === 0) {
    return (
      <EstadoVazio
        mensagem="Ainda não há respostas para montar a sua triagem. Responda alguns casos e ela aparece aqui."
        cta={{ label: "Praticar agora", onClick: () => navigate("/praticar") }}
      />
    );
  }

  const praticarTema = (t: Pick<PrioridadeEstudo, "area_id" | "especialidade_id" | "subtopico_id">, quantidade: number) =>
    navigate("/praticar", {
      state: {
        areaId: t.area_id,
        especialidadeId: t.especialidade_id,
        subtopicoId: t.subtopico_id,
        iniciarImediato: true,
        quantidade,
      },
    });

  return (
    <div className="flex flex-col gap-7">
      <RelatoResolvidoAviso />
      <Cabecalho
        totais={data.totais}
        porArea={data.por_area}
        respondidasHoje={data.respondidas_hoje}
        provaAlvo={me?.prova_alvo ?? null}
      />
      {/* Diagnóstico e conduta, nessa ordem: o título diz onde está a lacuna,
          e logo abaixo vem o que fazer hoje (DESIGN_TRIAGEM.md §6). */}
      <CondutaHoje
        revisao={data.revisao}
        cartoesHoje={me?.cartoes_hoje ?? 0}
        prioridade={data.prioridades[0]}
        onRevisar={() => navigate("/revisao")}
        onEstudarCartoes={() => navigate("/baralhos?estudar=tudo")}
        onPraticar={praticarTema}
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
          <PrioridadesEstudo prioridades={data.prioridades} onPraticar={praticarTema} />
        </div>
      )}
      {data.semana.novas > 0 && (
        <div className="animate-entrar" style={{ animationDelay: "340ms" }}>
          <ProgressoSemana semana={data.semana} onPraticar={praticarTema} />
        </div>
      )}
      <div className="animate-entrar" style={{ animationDelay: "380ms" }}>
        <SecaoEvolucao>
          {data.por_tipo.some((t) => t.total > 0) && (
            <PorTipoPergunta
              tipos={data.por_tipo}
              onPraticar={(tipo) =>
                navigate("/praticar", { state: { tipoPergunta: tipo, iniciarImediato: true, quantidade: 10 } })
              }
            />
          )}
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
            <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
              <span className="rotulo text-muted">Revisões dos próximos 7 dias</span>
              <PrevisaoSemana dias={data.revisao.proximos_dias} meta={data.revisao.meta} />
            </div>
            <EvolucaoTriagem evolucao={data.evolucao_14_dias} />
          </div>
          <EvolucaoMemoria memoria={data.memoria} />
        </SecaoEvolucao>
      </div>
    </div>
  );
}
