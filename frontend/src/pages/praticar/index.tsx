import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useMe } from "../../lib/auth";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { lerSessao, limparSessao, type SessaoSalva } from "../../lib/sessaoSalva";
import type { FiltrosPratica, ResumoSessao } from "../../lib/types";
import Configurador from "./Configurador";
import Resumo from "./Resumo";
import Sessao from "./Sessao";

type Fase =
  | { tipo: "config" }
  | { tipo: "sessao"; filtros: FiltrosPratica; nonce: number; salva?: SessaoSalva | null }
  | { tipo: "resumo"; resumo: ResumoSessao };

// Vindo do Painel ("Praticar 10" de uma área do quadro ou de um tema de "Onde
// você ganha mais pontos") — lido só na primeira montagem (useState lazy), não
// deveria reagir a re-renders posteriores da mesma navegação.
interface EstadoNavegacao {
  areaId?: number;
  especialidadeId?: number;
  subtopicoId?: number;
  tipoPergunta?: string;
  iniciarImediato?: boolean;
  quantidade?: number;
  // Vindo da lista de marcadas, na página de perfil.
  apenasMarcadas?: boolean;
}

export default function Praticar() {
  const location = useLocation();
  const estadoNav = (location.state as EstadoNavegacao | null) ?? null;
  const { data: me } = useMe();
  // Lido uma vez: se ela fechou a aba no meio de uma sessão, é isto que
  // aparece aqui em vez de a sessão simplesmente ter deixado de existir.
  const [salva, setSalva] = useState<SessaoSalva | null>(() => lerSessao());
  const pendente = salva && me && salva.email === me.email ? salva : null;

  const [fase, setFaseBruta] = useState<Fase>(() => {
    if (estadoNav?.iniciarImediato) {
      return {
        tipo: "sessao",
        nonce: Date.now(),
        filtros: {
          area_id: estadoNav.areaId,
          especialidade_id: estadoNav.especialidadeId,
          subtopico_id: estadoNav.subtopicoId,
          tipo_pergunta: estadoNav.tipoPergunta,
          quantidade: estadoNav.quantidade ?? 20,
          apenas_erros: false,
          excluir_respondidas: false,
          apenas_marcadas: estadoNav.apenasMarcadas,
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
      <div key="config" className={`flex flex-col gap-5 ${entrada}`}>
        {pendente && (
          <div className="flex flex-col gap-3 rounded-card border border-line bg-surface px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-corpo text-ink-2">
              Você parou no caso {pendente.idx + 1} de {pendente.questoes.length} de uma sessão anterior.
            </p>
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                className={BOTAO_PRIMARIO}
                onClick={() => {
                  setFase({ tipo: "sessao", filtros: pendente.filtros, nonce: pendente.salvoEm, salva: pendente });
                  setSalva(null);
                }}
              >
                Retomar
              </button>
              <button
                type="button"
                className={BOTAO_SECUNDARIO}
                onClick={() => {
                  limparSessao();
                  setSalva(null);
                }}
              >
                Descartar
              </button>
            </div>
          </div>
        )}
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
        salva={fase.salva}
        email={me?.email}
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
