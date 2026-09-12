import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { FilaPendenteAviso } from "../FilaPendenteAviso";
import { api } from "../../lib/api";
import { useAuthActions, useMe } from "../../lib/auth";
import { LABEL_POR_PATH } from "../../lib/nav";
import { aplicarTema, persistirTema, temaInicial, temaJaTemPreferencia, type Tema } from "../../lib/theme";
import { Rail, lerPreferenciaRail, salvarPreferenciaRail } from "./Rail";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: me } = useMe();
  const { sair } = useAuthActions();
  const [expandida, setExpandida] = useState(lerPreferenciaRail);
  const [gavetaAberta, setGavetaAberta] = useState(false);
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

  function alternarRail() {
    setExpandida((atual) => {
      salvarPreferenciaRail(!atual);
      return !atual;
    });
  }

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

  const titulo = LABEL_POR_PATH[location.pathname] ?? "";

  return (
    <div className="min-h-screen bg-canvas">
      <Rail
        expandida={expandida}
        onToggle={alternarRail}
        aberta={gavetaAberta}
        onFechar={() => setGavetaAberta(false)}
        contadores={me ? { questoes: me.total_questoes, materiais: me.total_materiais } : undefined}
      />
      <div className={`transition-toggle ease-brand ${expandida ? "md:pl-rail" : "md:pl-rail-collapsed"}`}>
        <Topbar
          titulo={titulo}
          tema={tema}
          onAlternarTema={alternarTema}
          onAbrirMenu={() => setGavetaAberta(true)}
          me={me}
          onSair={onSair}
        />
        <main className="px-4 py-6 md:px-8">
          <div className="mx-auto w-full max-w-[1160px]">
            <Outlet />
          </div>
        </main>
      </div>
      <FilaPendenteAviso />
    </div>
  );
}
