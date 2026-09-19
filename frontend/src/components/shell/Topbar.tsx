import { Flame, LogOut, Menu, Moon, Sun, Terminal, X } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { PRESSAO } from "../../lib/estilos";
import { useFoco } from "../../lib/focoContexto";
import { usePresenca } from "../../lib/movimento";
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
  // Só a convidada da brincadeira recebe esta opção; para todo mundo vem
  // `undefined` e o item não existe.
  onRever?: () => void;
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

// Sublinhado único que desliza até a aba ativa, em vez de um por aba que só
// liga e desliga. Mede a aba marcada com aria-current (o NavLink põe) depois
// de cada troca de rota e sempre que a barra muda de largura (fonte
// carregando, contagem de revisões aparecendo).
function useIndicadorAba(ativo: boolean) {
  const location = useLocation();
  const navRef = useRef<HTMLElement>(null);
  const [posicao, setPosicao] = useState<{ x: number; largura: number } | null>(null);
  // Sem transição na primeira medida: o sublinhado não pode entrar deslizando do canto.
  const [pronto, setPronto] = useState(false);

  useLayoutEffect(() => {
    const nav = navRef.current;
    if (!ativo || !nav) return;
    function medir() {
      const aba = nav!.querySelector<HTMLElement>('[aria-current="page"]');
      setPosicao(aba ? { x: aba.offsetLeft, largura: aba.offsetWidth } : null);
    }
    medir();
    const observador = new ResizeObserver(medir);
    observador.observe(nav);
    return () => observador.disconnect();
  }, [ativo, location.pathname]);

  // setTimeout e não requestAnimationFrame: o rAF fica parado em aba em segundo
  // plano, e o sublinhado nunca ganhava transição numa aba aberta escondida.
  // A medida em `medir` já forçou o layout da posição inicial.
  useEffect(() => {
    if (!posicao || pronto) return;
    const timer = setTimeout(() => setPronto(true), 0);
    return () => clearTimeout(timer);
  }, [posicao, pronto]);

  return { navRef, posicao, pronto };
}

// DESIGN_TRIAGEM.md §5: barra superior com abas no lugar do rail lateral. Em
// modo foco (sessão em andamento) as abas dão lugar à barra da sessão.
export function Topbar({ tema, onAlternarTema, me, revisoesHoje, onSair, onRever }: TopbarProps) {
  const { ativo: emFoco, setSlot } = useFoco();
  const [gavetaAberta, setGavetaAberta] = useState(false);
  const [contaAberta, setContaAberta] = useState(false);
  const menuConta = usePresenca(contaAberta);
  const { navRef, posicao: posicaoAba, pronto: indicadorPronto } = useIndicadorAba(!emFoco);
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
      <span className="animate-surgir rounded-etq bg-t1 px-1.5 py-px text-[12px] font-bold tabular-nums text-t1-on">
        {revisoesHoje}
      </span>
    );
  }

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface">
      <div className="flex h-16 items-center gap-4 px-4 md:px-6 xl:gap-6 xl:px-10">
        {!emFoco && (
          <button
            type="button"
            onClick={() => setGavetaAberta((v) => !v)}
            className={`-ml-1.5 rounded-btn p-1.5 text-ink-2 transition duration-hover hover:bg-ground lg:hidden ${PRESSAO}`}
            aria-label={gavetaAberta ? "Fechar menu" : "Abrir menu"}
            aria-expanded={gavetaAberta}
          >
            <span key={gavetaAberta ? "fechar" : "abrir"} className="flex animate-girar">
              {gavetaAberta ? <X size={20} strokeWidth={2} /> : <Menu size={20} strokeWidth={2} />}
            </span>
          </button>
        )}

        {/* Saída universal: vale também no modo foco, em que as abas somem.
            Nada se perde ao sair — respostas e avaliações são gravadas na hora
            e o simulado em andamento pode ser retomado. */}
        <Link
          to="/painel"
          onClick={() => setGavetaAberta(false)}
          aria-label="Conduta, ir para o Painel"
          title="Ir para o Painel"
          className="group/marca shrink-0 rounded-btn transition-opacity duration-hover hover:opacity-80"
        >
          <Marca />
        </Link>

        {/* `gap-3` no celular: com 24px entre os itens, a barra da Revisão
            estourava 390px e comia o "Sair", que o DESIGN_TRIAGEM.md §5 exige
            visível em toda sessão. */}
        {emFoco ? (
          <div ref={setSlot} className="flex min-w-0 flex-1 animate-desvanecer items-center gap-3 sm:gap-6" />
        ) : (
          <>
            <nav ref={navRef} className="relative hidden h-16 animate-desvanecer gap-5 lg:flex xl:gap-7">
              {NAV.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex h-16 items-center gap-2 whitespace-nowrap text-[14.5px] transition-colors duration-hover ${
                      isActive ? "font-semibold text-ink" : "font-medium text-muted hover:text-ink"
                    }`
                  }
                >
                  {item.curto ?? item.label}
                  {contagemRevisao(item.path)}
                </NavLink>
              ))}
              <span
                aria-hidden="true"
                className={`pointer-events-none absolute bottom-0 left-0 h-0.5 bg-ink ${
                  indicadorPronto ? "transition-[transform,width] duration-desliza ease-suave" : ""
                } ${posicaoAba ? "" : "opacity-0"}`}
                style={{
                  width: posicaoAba?.largura ?? 0,
                  transform: `translateX(${posicaoAba?.x ?? 0}px)`,
                }}
              />
            </nav>

            <div className="ml-auto flex animate-desvanecer items-center gap-2.5">
              <BuscaGlobal />

              {me && (
                <span
                  className={`rotulo flex h-9 items-center gap-1.5 whitespace-nowrap rounded-btn px-3 text-ink transition-colors duration-toggle ${
                    me.respondeu_hoje ? "bg-t4-soft" : "bg-t2-soft"
                  }`}
                  title={`Ofensiva de ${me.ofensiva_dias} dia${me.ofensiva_dias !== 1 ? "s" : ""}${
                    me.respondeu_hoje ? ", mantida hoje" : ": responda uma questão hoje para manter"
                  }`}
                >
                  <Flame size={14} strokeWidth={2} />
                  {/* A chave faz o número pular quando a ofensiva sobe. */}
                  <span key={me.ofensiva_dias} className="inline-block animate-marcar">
                    {me.ofensiva_dias}
                  </span>
                  {/* Abaixo de 1280px só o número: a barra não comporta tudo. */}
                  <span className="hidden xl:inline">dia{me.ofensiva_dias !== 1 ? "s" : ""}</span>
                </span>
              )}

              <button
                type="button"
                onClick={onAlternarTema}
                className={`flex h-9 w-9 items-center justify-center rounded-btn text-muted transition duration-hover hover:bg-ground hover:text-ink ${PRESSAO}`}
                aria-label={tema === "light" ? "Usar tema escuro" : "Usar tema claro"}
              >
                <span key={tema} className="flex animate-girar">
                  {tema === "light" ? <Moon size={18} strokeWidth={2} /> : <Sun size={18} strokeWidth={2} />}
                </span>
              </button>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setContaAberta((v) => !v)}
                  className={`flex h-9 w-9 items-center justify-center rounded-pill bg-ink text-[13px] font-bold text-onink transition duration-hover hover:opacity-90 ${PRESSAO}`}
                  aria-label="Abrir menu da conta"
                  aria-expanded={contaAberta}
                >
                  {inicial}
                </button>
                {contaAberta && <div className="fixed inset-0 z-40" onClick={() => setContaAberta(false)} />}
                {menuConta.montado && (
                  <div
                    className={`absolute right-0 top-11 z-50 w-64 origin-top-right rounded-card border border-line bg-surface p-2 ${
                      menuConta.saindo ? "pointer-events-none animate-sumir" : "animate-surgir"
                    }`}
                  >
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

                    {onRever && (
                      <div className="border-t border-line-soft pt-1">
                        <button
                          type="button"
                          onClick={() => {
                            setContaAberta(false);
                            onRever();
                          }}
                          className="flex w-full items-center gap-2.5 rounded-btn px-2.5 py-2 text-corpo text-ink-2 transition duration-hover hover:bg-ground hover:text-ink"
                        >
                          <Terminal size={16} strokeWidth={2} />
                          Rever as boas-vindas
                        </button>
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
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Gaveta sempre montada, com a altura animada de 0 ao conteúdo (truque
          de grid-template-rows 0fr → 1fr). `inert` tira os links fechados do
          teclado e dos leitores de tela. */}
      {!emFoco && (
        <div
          inert={!gavetaAberta}
          className={`grid transition-[grid-template-rows] duration-desliza ease-suave lg:hidden ${
            gavetaAberta ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
        >
          <div className="overflow-hidden">
            <nav className="border-t border-line px-4 py-2">
              {NAV.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setGavetaAberta(false)}
                  className={({ isActive }) =>
                    `flex h-11 items-center justify-between rounded-btn px-3 text-corpo transition-colors duration-hover ${
                      isActive ? "bg-ground font-semibold text-ink" : "text-ink-2 hover:bg-ground"
                    }`
                  }
                >
                  {item.label}
                  {contagemRevisao(item.path)}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}
    </header>
  );
}
