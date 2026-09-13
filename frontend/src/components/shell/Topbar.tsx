import { Flame, LogOut, Menu, Moon, Sun, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useFoco } from "../../lib/focoContexto";
import { ACERVO, NAV } from "../../lib/nav";
import type { Tema } from "../../lib/theme";
import type { Me } from "../../lib/types";
import { BuscaGlobal } from "./BuscaGlobal";
import { Marca } from "./Marca";

interface TopbarProps {
  tema: Tema;
  onAlternarTema: () => void;
  me?: Me;
  revisoesHoje?: number;
  onSair: () => void;
}

function textoProva(provaAlvo: string | null): string | null {
  if (!provaAlvo) return null;
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const alvo = new Date(`${provaAlvo}T00:00:00`);
  const dias = Math.round((alvo.getTime() - hoje.getTime()) / 86_400_000);
  if (dias < 0) return "A data da prova já passou";
  return `Prova em ${dias} dia${dias !== 1 ? "s" : ""}`;
}

// DESIGN_TRIAGEM.md §5: barra superior com abas no lugar do rail lateral. Em
// modo foco (sessão em andamento) as abas dão lugar à barra da sessão.
export function Topbar({ tema, onAlternarTema, me, revisoesHoje, onSair }: TopbarProps) {
  const { ativo: emFoco, setSlot } = useFoco();
  const [gavetaAberta, setGavetaAberta] = useState(false);
  const [contaAberta, setContaAberta] = useState(false);
  const inicial = me?.email ? me.email[0].toUpperCase() : "?";
  const prova = textoProva(me?.prova_alvo ?? null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setGavetaAberta(false);
        setContaAberta(false);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  function contagemRevisao(path: string) {
    if (path !== "/revisao" || !revisoesHoje) return null;
    return (
      <span className="rounded-etq bg-t1 px-1.5 py-px text-[12px] font-bold tabular-nums text-t1-on">{revisoesHoje}</span>
    );
  }

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface">
      <div className="flex h-16 items-center gap-4 px-4 md:px-6 xl:gap-6 xl:px-10">
        {!emFoco && (
          <button
            type="button"
            onClick={() => setGavetaAberta((v) => !v)}
            className="-ml-1.5 rounded-btn p-1.5 text-ink-2 hover:bg-ground lg:hidden"
            aria-label={gavetaAberta ? "Fechar menu" : "Abrir menu"}
            aria-expanded={gavetaAberta}
          >
            {gavetaAberta ? <X size={20} strokeWidth={2} /> : <Menu size={20} strokeWidth={2} />}
          </button>
        )}

        <Marca />

        {emFoco ? (
          <div ref={setSlot} className="flex min-w-0 flex-1 items-center gap-6" />
        ) : (
          <>
            <nav className="hidden h-16 gap-5 lg:flex xl:gap-7">
              {NAV.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex h-16 items-center gap-2 whitespace-nowrap border-b-2 text-[14.5px] transition duration-hover ${
                      isActive
                        ? "border-ink font-semibold text-ink"
                        : "border-transparent font-medium text-muted hover:text-ink"
                    }`
                  }
                >
                  {item.curto ?? item.label}
                  {contagemRevisao(item.path)}
                </NavLink>
              ))}
            </nav>

            <div className="ml-auto flex items-center gap-2.5">
              <BuscaGlobal />

              {me && (
                <span
                  className={`rotulo flex h-9 items-center gap-1.5 whitespace-nowrap rounded-btn px-3 text-ink ${
                    me.respondeu_hoje ? "bg-t4-soft" : "bg-t2-soft"
                  }`}
                  title={`Ofensiva de ${me.ofensiva_dias} dia${me.ofensiva_dias !== 1 ? "s" : ""}${
                    me.respondeu_hoje ? ", mantida hoje" : ": responda uma questão hoje para manter"
                  }`}
                >
                  <Flame size={14} strokeWidth={2} />
                  {me.ofensiva_dias}
                  {/* Abaixo de 1280px só o número: a barra não comporta tudo. */}
                  <span className="hidden xl:inline">dia{me.ofensiva_dias !== 1 ? "s" : ""}</span>
                </span>
              )}

              <button
                type="button"
                onClick={onAlternarTema}
                className="flex h-9 w-9 items-center justify-center rounded-btn text-muted transition duration-hover hover:bg-ground hover:text-ink"
                aria-label={tema === "light" ? "Usar tema escuro" : "Usar tema claro"}
              >
                {tema === "light" ? <Moon size={18} strokeWidth={2} /> : <Sun size={18} strokeWidth={2} />}
              </button>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setContaAberta((v) => !v)}
                  className="flex h-9 w-9 items-center justify-center rounded-pill bg-ink text-[13px] font-bold text-onink"
                  aria-label="Abrir menu da conta"
                  aria-expanded={contaAberta}
                >
                  {inicial}
                </button>
                {contaAberta && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setContaAberta(false)} />
                    <div className="absolute right-0 top-11 z-50 w-64 rounded-card border border-line bg-surface p-2">
                      <div className="px-2.5 py-2">
                        <div className="rotulo text-muted">Conta</div>
                        <div className="mt-1 break-all text-apoio text-ink-2">{me?.email}</div>
                        {prova && <div className="mt-0.5 text-apoio text-muted">{prova}</div>}
                      </div>

                      {me?.is_admin && (
                        <div className="border-t border-line-soft py-1">
                          <div className="rotulo px-2.5 py-1.5 text-muted">Acervo</div>
                          {ACERVO.map((item) => (
                            <NavLink
                              key={item.path}
                              to={item.path}
                              onClick={() => setContaAberta(false)}
                              className="flex items-center gap-2.5 rounded-btn px-2.5 py-2 text-corpo text-ink-2 transition duration-hover hover:bg-ground hover:text-ink"
                            >
                              <item.icon size={16} strokeWidth={2} />
                              {item.label}
                            </NavLink>
                          ))}
                        </div>
                      )}

                      <div className="border-t border-line-soft pt-1">
                        <button
                          type="button"
                          onClick={onSair}
                          className="flex w-full items-center gap-2.5 rounded-btn px-2.5 py-2 text-corpo text-ink-2 transition duration-hover hover:bg-ground hover:text-ink"
                        >
                          <LogOut size={16} strokeWidth={2} />
                          Sair da conta
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {gavetaAberta && !emFoco && (
        <nav className="border-t border-line px-4 py-2 lg:hidden">
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setGavetaAberta(false)}
              className={({ isActive }) =>
                `flex h-11 items-center justify-between rounded-btn px-3 text-corpo ${
                  isActive ? "bg-ground font-semibold text-ink" : "text-ink-2"
                }`
              }
            >
              {item.label}
              {contagemRevisao(item.path)}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
