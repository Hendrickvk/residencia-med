import { useEffect, useState } from "react";
import { flushSync } from "react-dom";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { BrincadeiraBoasVindas } from "../BrincadeiraBoasVindas";
import { jaViu, useEhConvidada } from "../../lib/brincadeira";
import { FilaPendenteAviso } from "../FilaPendenteAviso";
import { api } from "../../lib/api";
import { useAuthActions, useMe } from "../../lib/auth";
import { FocoProvider } from "../../lib/foco";
import { prefereMenosMovimento } from "../../lib/movimento";
import { usePainel } from "../../lib/painel";
import { aplicarTema, persistirTema, temaInicial, temaJaTemPreferencia, type Tema } from "../../lib/theme";
import { Topbar } from "./Topbar";

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: me } = useMe();
  // Só pela contagem de revisões vencidas na aba — mesma query (e cache) do Painel.
  const { data: painel } = usePainel();
  const { sair } = useAuthActions();
  const [tema, setTema] = useState<Tema>(temaInicial);
  // Primeiro acesso da convidada: a página só aparece quando a sessão de
  // boas-vindas termina, e é ela mesma que escurece o tema no meio. `jaViu()`
  // é sincrônico, então para quem já viu — todo o resto dos usuários, sempre —
  // não existe espera nenhuma.
  const [brincadeira, setBrincadeira] = useState<"verificando" | "rodando" | "off">(() =>
    jaViu() ? "off" : "verificando",
  );
  const convidada = useEhConvidada(me?.email);
  // Cada pedido de reprise remonta a sessão com estado limpo.
  const [reprise, setReprise] = useState(0);

  // Rede de segurança: se a verificação não responder (conta sem `/me`,
  // navegador sem `crypto.subtle`), a página aparece de todo jeito.
  useEffect(() => {
    if (brincadeira !== "verificando") return;
    const timer = setTimeout(() => setBrincadeira("off"), 2500);
    return () => clearTimeout(timer);
  }, [brincadeira]);

  useEffect(() => {
    aplicarTema(tema);
  }, [tema]);

  // Tela nova começa do topo: sem isso, sair de uma lista rolada abria o
  // Painel no meio.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  // Sincroniza com a preferência salva no backend só na primeira vez que
  // `/me` chega, e só quando o navegador ainda não tinha uma escolha local
  // — depois disso o toggle manual (com persistência local) manda.
  useEffect(() => {
    if (me && !temaJaTemPreferencia()) {
      persistirTema(me.tema);
      setTema(me.tema);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me?.tema]);

  function alternarTema() {
    trocarTema(tema === "light" ? "dark" : "light");
  }

  function trocarTema(novo: Tema) {
    if (novo === tema) return;
    persistirTema(novo);
    void api.patch("/me/tema", { tema: novo }).catch(() => {});

    // Idempotente de propósito: pode ser chamada de novo se a transição abortar
    // depois de começar.
    function trocar() {
      aplicarTema(novo);
      flushSync(() => setTema(novo));
    }
    // View Transition esmaece a tela inteira de um tema para o outro, mas a
    // troca NÃO pode depender dela: com o documento escondido ela lança
    // `InvalidStateError: Transition was aborted ... Document hidden`, e antes
    // disso o tema simplesmente não mudava e a exceção subia (foi o que
    // aconteceu quando a brincadeira passou a escurecer a tela sozinha).
    const podeAnimar =
      typeof document.startViewTransition === "function" && !prefereMenosMovimento() && !document.hidden;
    if (!podeAnimar) {
      trocar();
      return;
    }
    try {
      const transicao = document.startViewTransition(trocar);
      transicao.finished.catch(() => {});
      transicao.updateCallbackDone.catch(() => trocar());
    } catch {
      trocar();
    }
  }

  async function onSair() {
    await sair();
    navigate("/login", { replace: true });
  }

  return (
    <FocoProvider>
      <div className="min-h-screen bg-ground">
        {/* Enquanto a sessão de boas-vindas roda, a tela fica só com ela: o
            app "liga" quando a brincadeira acaba. As consultas do Painel
            seguem correndo por baixo, então a revelação é instantânea. */}
        {brincadeira === "off" && (
          <>
            <Topbar
              tema={tema}
              onAlternarTema={alternarTema}
              me={me}
              revisoesHoje={painel?.revisoes_hoje}
              onSair={onSair}
              onRever={convidada ? () => setReprise((n) => n + 1) : undefined}
            />
            <main className="px-4 py-6 md:px-10 md:py-9">
              {/* A chave por caminho remonta o invólucro a cada troca de tela e a
                  tela nova entra subindo (DESIGN_TRIAGEM.md §3). */}
              <div key={location.pathname} className="mx-auto w-full max-w-[1360px] animate-entrar">
                <Outlet />
              </div>
            </main>
            <FilaPendenteAviso />
          </>
        )}
        <BrincadeiraBoasVindas
          key={reprise}
          convidada={convidada}
          reprise={reprise > 0}
          onEstado={setBrincadeira}
          onEfeito={(efeito) => {
            if (efeito === "tema-escuro") trocarTema("dark");
          }}
        />
      </div>
    </FocoProvider>
  );
}
