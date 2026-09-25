import { useQuery } from "@tanstack/react-query";
import { Check, Pencil, RotateCcw, Undo2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Dialog } from "../../components/Dialog";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import { BarraFoco } from "../../lib/foco";
import {
  atualizarCartao, avaliarCartao, cartoesParaEstudar, desfazerCartao, plural,
  textoPrazo,
} from "../../lib/cartoes";
import { corCheia, corDeFundo } from "../../lib/paleta";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";

// As mesmas notas da Revisão de casos (repeticao_espacada.NOTAS_ACERTO): 1
// para o erro, 3/4/5 para "com esforço, lembrei, fácil". Escala igual porque o
// algoritmo é o mesmo — duas escalas dariam dois significados ao mesmo número.
//
// As cores saem da semântica derivada da escala (DESIGN_TRIAGEM.md §2: erro =
// t1, acerto = t4) e são as MESMAS da Revisão de casos. Ela já aprendeu esse
// vocabulário ali; inventar outro aqui faria o mesmo gesto significar duas
// coisas. `text-tN-on` é o que mantém isto legível nos dois temas: no claro o
// laranja pede tinta e o vermelho pede branco; no escuro todos pedem tinta.
const NOTAS = [
  { valor: 1, rotulo: "Errei", cor: "bg-t1 text-t1-on" },
  { valor: 3, rotulo: "Com esforço", cor: "bg-t2 text-t2-on" },
  { valor: 4, rotulo: "Lembrei", cor: "bg-t4 text-t4-on" },
  { valor: 5, rotulo: "Fácil", cor: "bg-t5 text-t5-on" },
];

interface Props {
  /** `null` = fila do dia atravessando todos os baralhos. */
  baralhoId: number | null;
  nome: string;
  cor?: string;
  onSair: () => void;
}

export default function Estudo({ baralhoId, nome, cor, onSair }: Props) {
  // O lote inteiro de uma vez, como no Praticar (MIGRACAO.md §0): nada de ida
  // ao servidor entre um cartão e o próximo.
  const { data, isLoading, isError, isPaused, refetch } = useQuery({
    queryKey: ["estudo", baralhoId],
    queryFn: () => cartoesParaEstudar(baralhoId),
    staleTime: Infinity,
    gcTime: 0,
  });
  const [idx, setIdx] = useState(0);
  const [virado, setVirado] = useState(false);
  // Guarda a nota de cada cartão: é o que o resumo conta, e o que permite
  // desfazer a última.
  const [notas, setNotas] = useState<number[]>([]);
  // Texto reescrito durante a sessão. Fica aqui em vez de no cache da query
  // porque o lote tem `staleTime: Infinity` e não vai ser refeito.
  const [reescritos, setReescritos] = useState<Record<number, { frente: string; verso: string }>>({});
  const [editando, setEditando] = useState(false);
  const [desfazendo, setDesfazendo] = useState(false);

  const fila = data?.cartoes ?? [];
  const bruto = fila[idx];
  const atual = bruto ? { ...bruto, ...reescritos[bruto.id] } : undefined;
  const acertos = notas.filter((n) => n >= 3).length;
  const feitos = notas.length;
  const progresso = fila.length ? (feitos / fila.length) * 100 : 0;
  // Quantos ainda vêm depois deste: é o que a pilha de trás desenha.
  const restantes = Math.max(fila.length - feitos - 1, 0);

  function responder(nota: number) {
    if (!atual) return;
    // Fire-and-forget, como o `/respostas` do Praticar: a tela não espera a
    // rede para ir ao próximo cartão.
    void avaliarCartao(atual.id, nota).catch(() => {});
    setNotas((n) => [...n, nota]);
    setVirado(false);
    setIdx((i) => i + 1);
  }

  // Desfazer volta o cartão E o agendamento: o servidor restaura o estado do
  // SM-2 a partir do histórico. Só a última nota, que é o caso real (tecla
  // errada); desfazer em cadeia seria outra conversa.
  async function desfazer() {
    if (feitos === 0 || desfazendo) return;
    const anterior = fila[feitos - 1];
    setDesfazendo(true);
    try {
      await desfazerCartao(anterior.id);
      setNotas((n) => n.slice(0, -1));
      setIdx(feitos - 1);
      setVirado(false);
    } catch {
      // Falhou no servidor: não mexe na tela, senão ela veria de volta um
      // cartão que continua agendado como estava.
    } finally {
      setDesfazendo(false);
    }
  }

  // Espaço vira o cartão; 1–4 dão a nota; Ctrl/Cmd+Z desfaz. Teclado é o que
  // torna uma sessão de 40 cartões suportável — mesmo princípio dos atalhos
  // A–E do Praticar. As ações vão por ref para o efeito não se remontar a
  // cada render.
  const acoes = useRef({ responder, desfazer, editando });
  useEffect(() => {
    acoes.current = { responder, desfazer, editando };
  });
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Digitando no formulário de edição, o teclado é do formulário.
      if (acoes.current.editando) return;
      if ((e.key === "z" || e.key === "Z") && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        void acoes.current.desfazer();
        return;
      }
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        setVirado(true);
        return;
      }
      if (!virado) return;
      const i = Number(e.key) - 1;
      if (i >= 0 && i < NOTAS.length) acoes.current.responder(NOTAS[i].valor);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [virado]);

  return (
    <>
      <BarraFoco>
        <div className="flex w-full items-center gap-3">
          {/* Numa sessão que atravessa baralhos, o nome e a cor são do cartão
              da vez — é o que diz onde ela está. */}
          <span
            className="h-5 w-1.5 shrink-0 rounded-pill"
            style={corDeFundo(atual?.cor ?? cor, "pasta")}
            aria-hidden="true"
          />
          <span className="truncate text-corpo font-semibold text-ink">
            {baralhoId === null ? atual?.baralho ?? nome : nome}
          </span>
          {/* Trilho de progresso em vez de só "3 de 8": a barra enchendo é o
              que dá a sensação de que a pilha está acabando. */}
          <div className="ml-auto hidden h-1.5 w-40 overflow-hidden rounded-pill bg-line-soft sm:block">
            {/* `scaleX` e não `width`: anima só transform, sem refazer layout. */}
            <span
              className="block h-full origin-left bg-ink transition-transform duration-desliza ease-suave"
              style={{ transform: `scaleX(${progresso / 100})` }}
            />
          </div>
          <span className="shrink-0 text-apoio tabular-nums text-muted">
            {Math.min(feitos + 1, fila.length)} de {fila.length}
          </span>
          {feitos > 0 && (
            <button
              type="button"
              onClick={() => void desfazer()}
              disabled={desfazendo}
              className="flex shrink-0 items-center gap-1 text-apoio text-muted transition duration-hover hover:text-ink"
            >
              <Undo2 size={14} strokeWidth={2} />
              Desfazer
            </button>
          )}
          <button type="button" onClick={onSair} className="shrink-0 text-apoio text-muted hover:text-ink">
            Encerrar
          </button>
        </div>
      </BarraFoco>

      <div className="mx-auto flex w-full max-w-[680px] animate-entrar flex-col gap-5">
        {isLoading && <div className="h-[320px] animate-pulse rounded-caso bg-line-soft" />}

        {!isLoading && (isError || isPaused) && !data && (
          <EstadoFalha
            mensagem="Não deu para montar o estudo. Pode ser a conexão."
            pausado={isPaused}
            onTentarDeNovo={() => void refetch()}
          />
        )}

        {data && fila.length === 0 && (
          <EstadoVazio
            mensagem={
              baralhoId === null
                ? "Nenhum cartão vencido hoje. Volte quando o próximo prazo chegar."
                : "Nenhum cartão vencido neste baralho hoje. Volte quando o próximo prazo chegar."
            }
            cta={{ label: "Voltar", onClick: onSair }}
          />
        )}

        {data && fila.length > 0 && !atual && (
          <ResumoSessao total={feitos} acertos={acertos} cor={cor} onSair={onSair} />
        )}

        {atual && (
          <>
            {/* A pilha atrás é o que falta na fila: enquanto ela avança, as
                bordas vão sumindo. */}
            <div className="relative pt-3">
              {restantes > 1 && (
                <span
                  className="absolute inset-x-8 top-0 h-3 rounded-t-caso border border-b-0 border-line bg-surface opacity-50"
                  aria-hidden="true"
                />
              )}
              {restantes > 0 && (
                <span
                  className="absolute inset-x-4 top-1.5 h-3 rounded-t-caso border border-b-0 border-line bg-surface"
                  aria-hidden="true"
                />
              )}
              <div className="[perspective:1600px]">
                {/* O cartão vira de verdade: as duas faces ocupam a mesma
                    célula da grade e o bloco gira em Y. Grade, e não o verso em
                    `absolute inset-0`: assim o cartão tem a altura da face mais
                    longa — com o absoluto ele tinha a da frente, e um verso
                    comprido vazava por cima dos botões de nota. */}
                <div
                  className={`grid transition-transform duration-desliza ease-suave [transform-style:preserve-3d] ${
                    virado ? "[transform:rotateY(180deg)]" : ""
                  }`}
                >
                  <FaceCartao texto={atual.frente} rotulo="Frente" cor={atual.cor ?? cor} />
                  <FaceCartao texto={atual.verso} rotulo="Verso" cor={atual.cor ?? cor} verso />
                </div>
              </div>
            </div>

            {/* Corrigir aqui, e não depois: o momento em que ela vê que o
                cartão está mal escrito é justamente o de respondê-lo. Tendo de
                sair para achar o baralho, ela não corrige. */}
            <button
              type="button"
              onClick={() => setEditando(true)}
              className="flex items-center gap-1.5 self-center text-apoio text-muted transition duration-hover hover:text-ink"
            >
              <Pencil size={13} strokeWidth={2} />
              Editar este cartão
            </button>

            {!virado ? (
              <button type="button" onClick={() => setVirado(true)} className={`${BOTAO_PRIMARIO} w-full`}>
                <RotateCcw size={16} strokeWidth={2} />
                Ver a resposta
                <span className="text-apoio font-normal opacity-70">espaço</span>
              </button>
            ) : (
              <div className="grid animate-entrar grid-cols-2 gap-2.5 sm:grid-cols-4">
                {NOTAS.map((nota, i) => (
                  <button
                    key={nota.valor}
                    type="button"
                    onClick={() => responder(nota.valor)}
                    className={`flex flex-col items-center gap-0.5 rounded-pill px-3 py-2.5 font-semibold transition duration-hover ease-brand hover:opacity-90 active:scale-[0.97] ${nota.cor}`}
                  >
                    <span className="text-[15px] leading-tight">{nota.rotulo}</span>
                    {/* O prazo vem do servidor, da mesma conta que grava: o
                        botão não pode prometer um intervalo e agendar outro. */}
                    <span className="text-apoio font-normal opacity-80">
                      {textoPrazo(atual.prazos[String(nota.valor)])} · {i + 1}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {atual && (
        <EditarNoEstudo
          key={atual.id}
          aberto={editando}
          frenteAtual={atual.frente}
          versoAtual={atual.verso}
          onFechar={() => setEditando(false)}
          onSalvo={(frente, verso) => {
            void atualizarCartao(atual.id, frente, verso).catch(() => {});
            setReescritos((r) => ({ ...r, [atual.id]: { frente, verso } }));
            setEditando(false);
          }}
        />
      )}
    </>
  );
}

function EditarNoEstudo({
  aberto, frenteAtual, versoAtual, onFechar, onSalvo,
}: {
  aberto: boolean;
  frenteAtual: string;
  versoAtual: string;
  onFechar: () => void;
  onSalvo: (frente: string, verso: string) => void;
}) {
  const [frente, setFrente] = useState(frenteAtual);
  const [verso, setVerso] = useState(versoAtual);

  return (
    <Dialog titulo="Editar este cartão" aberto={aberto} onFechar={onFechar}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (frente.trim() && verso.trim()) onSalvo(frente, verso);
        }}
        className="flex flex-col gap-4"
      >
        <label htmlFor="estudo-frente" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Frente</span>
          <textarea
            id="estudo-frente"
            value={frente}
            onChange={(e) => setFrente(e.target.value)}
            maxLength={2000}
            rows={3}
            autoFocus
            className={`${CAMPO} h-auto py-2 leading-normal`}
          />
        </label>
        <label htmlFor="estudo-verso" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Verso</span>
          <textarea
            id="estudo-verso"
            value={verso}
            onChange={(e) => setVerso(e.target.value)}
            maxLength={2000}
            rows={3}
            className={`${CAMPO} h-auto py-2 leading-normal`}
          />
        </label>
        <div className="flex gap-2">
          <button type="button" onClick={onFechar} className={`${BOTAO_SECUNDARIO} flex-1`}>
            Cancelar
          </button>
          <button
            type="submit"
            disabled={!frente.trim() || !verso.trim()}
            className={`${BOTAO_PRIMARIO} flex-1`}
          >
            Salvar
          </button>
        </div>
      </form>
    </Dialog>
  );
}

function FaceCartao({
  texto, rotulo, cor, verso = false,
}: {
  texto: string;
  rotulo: string;
  cor?: string;
  verso?: boolean;
}) {
  return (
    <div
      className={`col-start-1 row-start-1 flex min-h-[260px] flex-col gap-4 rounded-caso border border-line bg-surface p-7 [backface-visibility:hidden] ${
        verso ? "[transform:rotateY(180deg)]" : ""
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="h-3 w-1 rounded-pill" style={corDeFundo(cor, "pasta")} aria-hidden="true" />
        <span className="rotulo text-muted">{rotulo}</span>
      </div>
      <p className="flex flex-1 items-center justify-center whitespace-pre-wrap text-center text-enunciado text-ink">
        {texto}
      </p>
    </div>
  );
}

function ResumoSessao({
  total, acertos, cor, onSair,
}: {
  total: number;
  acertos: number;
  cor?: string;
  onSair: () => void;
}) {
  const pct = total ? Math.round((acertos / total) * 100) : 0;
  return (
    <div className="flex animate-entrar flex-col items-center gap-5 rounded-caso border border-line bg-surface px-6 py-10 text-center">
      {/* O visto na cor `on` do tom: branco fixo sumia nos tons claros. Carimba
          ao chegar, como a letra da alternativa escolhida: fim de sessão é
          raro, e é onde o movimento pode comemorar um pouco. */}
      <span
        className="flex h-12 w-12 animate-marcar items-center justify-center rounded-pill"
        style={corCheia(cor, "pasta")}
      >
        <Check size={22} strokeWidth={2.5} />
      </span>
      <div>
        <p className="text-subtitulo text-ink">
          {plural(total)} revisado{total === 1 ? "" : "s"}
        </p>
        <p className="mt-1 text-corpo text-ink-2">
          {/* Sem cor de triagem no número: aqui é a sessão dela, não um nível
              de aproveitamento do Painel. */}
          Você lembrou de {acertos} ({pct}%). Os que falharam voltam ainda hoje.
        </p>
      </div>
      <button type="button" onClick={onSair} className={BOTAO_PRIMARIO}>
        Voltar
      </button>
    </div>
  );
}
