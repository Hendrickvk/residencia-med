import { useState } from "react";
import { useLocation } from "react-router-dom";
import type { FiltrosPratica, ResumoSessao } from "../../lib/types";
import Configurador from "./Configurador";
import Resumo from "./Resumo";
import Sessao from "./Sessao";

type Fase =
  | { tipo: "config" }
  | { tipo: "sessao"; filtros: FiltrosPratica; nonce: number }
  | { tipo: "resumo"; resumo: ResumoSessao };

// Vindo do Painel ("Praticar 10" de uma área do quadro ou de um tema de "Onde
// você ganha mais pontos") — lido só na primeira montagem (useState lazy), não
// deveria reagir a re-renders posteriores da mesma navegação.
interface EstadoNavegacao {
  areaId?: number;
  especialidadeId?: number;
  subtopicoId?: number;
  iniciarImediato?: boolean;
  quantidade?: number;
}

export default function Praticar() {
  const location = useLocation();
  const estadoNav = (location.state as EstadoNavegacao | null) ?? null;

  const [fase, setFaseBruta] = useState<Fase>(() => {
    if (estadoNav?.iniciarImediato) {
      return {
        tipo: "sessao",
        nonce: Date.now(),
        filtros: {
          area_id: estadoNav.areaId,
          especialidade_id: estadoNav.especialidadeId,
          subtopico_id: estadoNav.subtopicoId,
          quantidade: estadoNav.quantidade ?? 20,
          apenas_erros: false,
          excluir_respondidas: false,
        },
      };
    }
    return { tipo: "config" };
  });
  // A primeira fase já entra com a animação da troca de tela (AppShell); só
  // as trocas seguintes animam aqui, para não somar dois movimentos.
  const [trocouFase, setTrocouFase] = useState(false);

  function setFase(nova: Fase) {
    setFaseBruta(nova);
    setTrocouFase(true);
  }

  const entrada = trocouFase ? "animate-entrar" : "";

  if (fase.tipo === "config") {
    return (
      <div key="config" className={entrada}>
        <Configurador
          areaInicial={estadoNav?.areaId}
          onIniciar={(filtros) => setFase({ tipo: "sessao", filtros, nonce: Date.now() })}
        />
      </div>
    );
  }

  if (fase.tipo === "sessao") {
    return (
      <Sessao
        filtros={fase.filtros}
        nonce={fase.nonce}
        onFinalizar={(resumo) => setFase({ tipo: "resumo", resumo })}
        onVoltar={() => setFase({ tipo: "config" })}
      />
    );
  }

  return (
    <div key="resumo" className={entrada}>
      <Resumo resumo={fase.resumo} onNovaSessao={() => setFase({ tipo: "config" })} />
    </div>
  );
}
