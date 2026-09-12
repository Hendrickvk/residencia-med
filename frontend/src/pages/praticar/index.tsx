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

// Vindo do Painel ("Praticar 10 desta área" ou clique numa linha de "Onde
// você está errando") — lido só na primeira montagem (useState lazy), não
// deveria reagir a re-renders posteriores da mesma navegação.
interface EstadoNavegacao {
  areaId?: number;
  iniciarImediato?: boolean;
  quantidade?: number;
}

export default function Praticar() {
  const location = useLocation();
  const estadoNav = (location.state as EstadoNavegacao | null) ?? null;

  const [fase, setFase] = useState<Fase>(() => {
    if (estadoNav?.iniciarImediato) {
      return {
        tipo: "sessao",
        nonce: Date.now(),
        filtros: {
          area_id: estadoNav.areaId,
          quantidade: estadoNav.quantidade ?? 20,
          apenas_erros: false,
          excluir_respondidas: false,
        },
      };
    }
    return { tipo: "config" };
  });

  if (fase.tipo === "config") {
    return (
      <Configurador
        areaInicial={estadoNav?.areaId}
        onIniciar={(filtros) => setFase({ tipo: "sessao", filtros, nonce: Date.now() })}
      />
    );
  }

  if (fase.tipo === "sessao") {
    return (
      <Sessao
        filtros={fase.filtros}
        nonce={fase.nonce}
        onFinalizar={(resumo) => setFase({ tipo: "resumo", resumo })}
      />
    );
  }

  return <Resumo resumo={fase.resumo} onNovaSessao={() => setFase({ tipo: "config" })} />;
}
