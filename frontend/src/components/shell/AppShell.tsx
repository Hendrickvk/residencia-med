import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { FilaPendenteAviso } from "../FilaPendenteAviso";
import { api } from "../../lib/api";
import { useAuthActions, useMe } from "../../lib/auth";
import { FocoProvider } from "../../lib/foco";
import { usePainel } from "../../lib/painel";
import { aplicarTema, persistirTema, temaInicial, temaJaTemPreferencia, type Tema } from "../../lib/theme";
import { Topbar } from "./Topbar";

export function AppShell() {
  const navigate = useNavigate();
  const { data: me } = useMe();
  // Só pela contagem de revisões vencidas na aba — mesma query (e cache) do Painel.
  const { data: painel } = usePainel();
  const { sair } = useAuthActions();
  const [tema, setTema] = useState<Tema>(temaInicial);

  useEffect(() => {
    aplicarTema(tema);
  }, [tema]);

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
    setTema((atual) => {
      const novo = atual === "light" ? "dark" : "light";
      persistirTema(novo);
      void api.patch("/me/tema", { tema: novo }).catch(() => {});
      return novo;
    });
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
          <div className="mx-auto w-full max-w-[1360px]">
            <Outlet />
          </div>
        </main>
        <FilaPendenteAviso />
      </div>
    </FocoProvider>
  );
}
