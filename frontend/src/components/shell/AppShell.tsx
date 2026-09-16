import { useEffect, useState } from "react";
import { flushSync } from "react-dom";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { BrincadeiraBoasVindas } from "../BrincadeiraBoasVindas";
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
    const novo = tema === "light" ? "dark" : "light";
    persistirTema(novo);
    void api.patch("/me/tema", { tema: novo }).catch(() => {});

    function trocar() {
      aplicarTema(novo);
      flushSync(() => setTema(novo));
    }
    // View Transition esmaece a tela inteira de um tema para o outro; onde o
    // navegador não tem a API, a troca é imediata como antes.
    if (typeof document.startViewTransition === "function" && !prefereMenosMovimento()) {
      document.startViewTransition(trocar);
    } else {
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
        <Topbar
          tema={tema}
          onAlternarTema={alternarTema}
          me={me}
          revisoesHoje={painel?.revisoes_hoje}
          onSair={onSair}
        />
        <main className="px-4 py-6 md:px-10 md:py-9">
          {/* A chave por caminho remonta o invólucro a cada troca de tela e a
              tela nova entra subindo (DESIGN_TRIAGEM.md §3). */}
          <div key={location.pathname} className="mx-auto w-full max-w-[1360px] animate-entrar">
            <Outlet />
          </div>
        </main>
        <FilaPendenteAviso />
        <BrincadeiraBoasVindas email={me?.email} />
      </div>
    </FocoProvider>
  );
}
