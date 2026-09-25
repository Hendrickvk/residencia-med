import { Flame, LogOut, Moon, Sparkles, Sun, Terminal, UserRound } from "lucide-react";
import { textoProva } from "../../lib/format";
import { nomeExibido } from "../../lib/perfil";
import { Avatar } from "../Avatar";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { PRESSAO } from "../../lib/estilos";
import { useFoco } from "../../lib/focoContexto";
import { usePresenca } from "../../lib/movimento";
import { ACERVO, indiceDaAba, NAV } from "../../lib/nav";
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
  onNovidades: () => void;
  temNovidade: boolean;
  // Só a convidada da brincadeira recebe esta opção; para todo mundo vem
  // `undefined` e o item não existe.
  onRever?: () => void;
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
export function Topbar({ tema, onAlternarTema, me, revisoesHoje, onSair, onRever, onNovidades, temNovidade }: TopbarProps) {
  const { ativo: emFoco, setSlot } = useFoco();
  const [contaAberta, setContaAberta] = useState(false);
  const menuConta = usePresenca(contaAberta);
  const { navRef, posicao: posicaoAba, pronto: indicadorPronto } = useIndicadorAba(!emFoco);
  const prova = textoProva(me?.prova_alvo ?? null);
  const abaAtual = indiceDaAba(useLocation().pathname);
  // Fora das abas (perfil) o traço do rodapé some, mas guarda a posição: ao
  // voltar ele sai de onde estava, e não do canto da tela.
  const [ultimaAba, setUltimaAba] = useState(Math.max(abaAtual, 0));
  if (abaAtual >= 0 && abaAtual !== ultimaAba) setUltimaAba(abaAtual);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setContaAberta(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  // Mesma etiqueta para as duas abas que têm fila vencida: é a mesma
  // pergunta ("o que me espera hoje?"), e dois tratamentos diferentes para a
  // mesma coisa fariam a aluna achar que significam coisas diferentes. No
  // rodapé ela vai no canto do ícone, com um anel da cor da barra para
  // recortar o traço do ícone.
  function contagemDaAba(path: string, noIcone = false) {
    const total = path === "/revisao" ? revisoesHoje : path === "/baralhos" ? me?.cartoes_hoje : 0;
    if (!total) return null;
    const base = "animate-surgir rounded-etq bg-t1 font-bold tabular-nums text-t1-on";
    return (
      <span
        className={
          noIcone
            ? `${base} absolute -top-1.5 left-3 px-1 text-[11px] leading-4 ring-2 ring-surface`
            : `${base} px-1.5 py-px text-[12px]`
        }
      >
        {total}
      </span>
    );
  }

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface">
      <div className="flex h-16 items-center gap-4 px-4 md:px-6 xl:gap-6 xl:px-10">
        {/* Saída universal: vale também no modo foco, em que as abas somem.
            Nada se perde ao sair — respostas e avaliações são gravadas na hora
            e o simulado em andamento pode ser retomado. */}
        <Link
          to="/painel"
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
                  {contagemDaAba(item.path)}
                </NavLink>
              ))}
              {/* 1px de largura esticado por `scaleX`: só transform anima, sem
                  refazer o layout a cada quadro, como acontecia com `width`. */}
              <span
                aria-hidden="true"
                className={`pointer-events-none absolute bottom-0 left-0 h-0.5 w-px origin-left bg-ink ${
                  indicadorPronto ? "transition-transform duration-desliza ease-suave" : ""
                } ${posicaoAba ? "" : "opacity-0"}`}
                style={{
                  transform: `translateX(${posicaoAba?.x ?? 0}px) scaleX(${posicaoAba?.largura ?? 0})`,
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
                  className={`flex rounded-pill transition duration-hover hover:opacity-90 ${PRESSAO}`}
                  aria-label="Abrir menu da conta"
                  aria-expanded={contaAberta}
                >
                  <Avatar me={me} />
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
                      <div className="mt-1 break-all text-corpo font-semibold text-ink">{nomeExibido(me)}</div>
                      {/* O e-mail vira apoio quando já existe um nome; sem
                          nome ele já é a linha de cima e não se repete. */}
                      {me?.nome && <div className="break-all text-apoio text-muted">{me.email}</div>}
                      {prova && <div className="mt-0.5 text-apoio text-muted">{prova}</div>}
                    </div>

                    {/* Primeiro item da lista: é o que a pessoa procura
                        quando abre o menu da conta. */}
                    <div className="border-t border-line-soft py-1">
                      <NavLink
                        to="/perfil"
                        onClick={() => setContaAberta(false)}
                        className="flex items-center gap-2.5 rounded-btn px-2.5 py-2 text-corpo text-ink-2 transition duration-hover hover:bg-ground hover:text-ink"
                      >
                        <UserRound size={16} strokeWidth={2} />
                        Seu perfil
                      </NavLink>
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
                        onClick={() => {
                          setContaAberta(false);
                          onNovidades();
                        }}
                        className="flex w-full items-center gap-2.5 rounded-btn px-2.5 py-2 text-corpo text-ink-2 transition duration-hover hover:bg-ground hover:text-ink"
                      >
                        <Sparkles size={16} strokeWidth={2} />
                        O que mudou
                        {/* Ponto de pendência, não etiqueta colorida: a escala
                            de triagem só codifica nível (DESIGN_TRIAGEM.md §2),
                            então aqui é tinta. */}
                        {temNovidade && <span className="ml-auto h-2 w-2 rounded-pill bg-ink" aria-label="novidade não lida" />}
                      </button>
                    </div>

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

      {/* Abaixo de 1024px as abas moram no rodapé, ao alcance do polegar, com
          as mesmas contagens. Antes ficavam num menu ☰, e a contagem de
          revisões só aparecia com ele aberto: a aluna abria o app no celular
          sem ver o que vencia hoje. Some no modo foco, em que o rodapé é da
          ação da sessão. Fixa dentro do cabeçalho, que não tem transform, e
          por isso fica acima do conteúdo pelo z-30 dele. */}
      {!emFoco && (
        <nav className="fixed inset-x-0 bottom-0 animate-desvanecer border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden">
          <div className="relative grid grid-cols-5">
            {NAV.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex h-14 flex-col items-center justify-center gap-1 text-[12px] transition-colors duration-hover ${
                    isActive ? "font-semibold text-ink" : "font-medium text-muted"
                  }`
                }
              >
                <span className="relative">
                  <item.icon size={20} strokeWidth={2} />
                  {contagemDaAba(item.path, true)}
                </span>
                {item.curto ?? item.label}
              </NavLink>
            ))}
            {/* O traço de tinta do sublinhado das abas, na borda que dá para
                o conteúdo. As colunas têm a mesma largura: a posição é o
                índice, sem medir nada. */}
            <span
              aria-hidden="true"
              className={`pointer-events-none absolute left-0 top-0 h-0.5 w-1/5 bg-ink transition-transform duration-desliza ease-suave ${
                abaAtual < 0 ? "opacity-0" : ""
              }`}
              style={{ transform: `translateX(${ultimaAba * 100}%)` }}
            />
          </div>
        </nav>
      )}
    </header>
  );
}
