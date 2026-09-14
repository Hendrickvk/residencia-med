import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, BadgeCheck, Flag } from "lucide-react";
import { useState } from "react";
import { Dialog } from "../../components/Dialog";
import { API_URL, api } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, PRESSAO } from "../../lib/estilos";
import { BarraFoco } from "../../lib/foco";
import { formatarTempoRestante } from "../../lib/format";
import { rolarParaTopo } from "../../lib/movimento";
import { finalizarSimulado, nomeEdicao, responderSimulado, useItensSimulado, useSimulado } from "../../lib/simulados";
import type { ItemSimulado, Simulado } from "../../lib/types";
import { AlternativaLinha } from "../praticar/AlternativaLinha";
import { useCronometroRegressivo } from "./useCronometroRegressivo";

interface Props {
  simuladoId: number;
  onFinalizado: () => void;
}

export default function EmAndamento({ simuladoId, onFinalizado }: Props) {
  const { data: simulado, isLoading: carregandoSimulado } = useSimulado(simuladoId);
  const { data: itens, isLoading: carregandoItens } = useItensSimulado(simuladoId);

  if (carregandoSimulado || carregandoItens || !simulado || !itens) {
    return (
      <>
        <BarraFoco>
          <span className="text-[14.5px] text-ink-2">Simulado</span>
        </BarraFoco>
        <div className="mx-auto flex max-w-[680px] flex-col gap-5">
          <div className="h-[72px] w-32 animate-pulse rounded-card bg-line-soft" />
          <div className="h-[520px] animate-pulse rounded-caso bg-line-soft" />
        </div>
      </>
    );
  }

  return <Conteudo simuladoId={simuladoId} simulado={simulado} itens={itens} onFinalizado={onFinalizado} />;
}

function Conteudo({
  simuladoId,
  simulado,
  itens,
  onFinalizado,
}: {
  simuladoId: number;
  simulado: Simulado;
  itens: ItemSimulado[];
  onFinalizado: () => void;
}) {
  // Ao retomar uma prova, abre na primeira questão ainda em branco.
  const [idx, setIdx] = useState(() => Math.max(0, itens.findIndex((i) => !i.resposta_dada)));
  // Sentido da última navegação: a questão nova desliza da direita ao avançar
  // e da esquerda ao voltar. null = ainda não navegou (só esmaece).
  const [direcao, setDirecao] = useState<"frente" | "tras" | null>(null);
  const [respostasLocais, setRespostasLocais] = useState<Record<number, string>>(() => {
    const r: Record<number, string> = {};
    for (const item of itens) if (item.resposta_dada) r[item.id] = item.resposta_dada;
    return r;
  });
  const [marcadasLocais, setMarcadasLocais] = useState<Set<number>>(
    () => new Set(itens.filter((i) => i.marcada).map((i) => i.id)),
  );
  const [dialogoAberto, setDialogoAberto] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const queryClient = useQueryClient();

  async function finalizarAgora() {
    if (finalizando) return;
    setFinalizando(true);
    try {
      await finalizarSimulado(simuladoId);
      // Sem isso, o Resultado monta com o cache de ANTES de responder
      // qualquer coisa (mesma queryKey, staleTime padrão) e mostra "não
      // respondida"/gabarito ausente por um instante até um refetch em
      // segundo plano corrigir sozinho — invalidar e esperar aqui evita
      // esse flash de dado errado.
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["simulado-itens", simuladoId] }),
        queryClient.invalidateQueries({ queryKey: ["simulado", simuladoId] }),
        queryClient.invalidateQueries({ queryKey: ["simulado-em-andamento"] }),
        queryClient.invalidateQueries({ queryKey: ["simulados-historico"] }),
      ]);
    } finally {
      onFinalizado();
    }
  }

  const restanteSeg = useCronometroRegressivo(simulado.iniciado_em, simulado.tempo_limite_min, finalizarAgora);

  const itemAtual = itens[idx];
  const respostaAtual = respostasLocais[itemAtual.id] ?? null;
  const marcadaAtual = marcadasLocais.has(itemAtual.id);
  const emBranco = itens.length - Object.keys(respostasLocais).length;

  function irPara(destino: number) {
    const i = Math.min(itens.length - 1, Math.max(0, destino));
    if (i === idx) return;
    setDirecao(i > idx ? "frente" : "tras");
    setIdx(i);
    rolarParaTopo();
  }

  function responder(letra: string) {
    setRespostasLocais((prev) => ({ ...prev, [itemAtual.id]: letra }));
    // Sem fila de retry dedicada aqui (diferente de Praticar): uma falha
    // pontual não deveria travar a navegação do aluno durante a prova — o
    // pior caso é essa resposta específica não persistir, revisável no
    // histórico depois.
    responderSimulado(simuladoId, itemAtual.id, letra).catch(() => {});
  }

  function alternarMarcacao() {
    const estava = marcadasLocais.has(itemAtual.id);
    setMarcadasLocais((prev) => {
      const novo = new Set(prev);
      if (estava) novo.delete(itemAtual.id);
      else novo.add(itemAtual.id);
      return novo;
    });
    const chamada = estava
      ? api.delete(`/questoes/${itemAtual.id}/marcar`)
      : api.post(`/questoes/${itemAtual.id}/marcar`);
    chamada.catch(() => {
      setMarcadasLocais((prev) => {
        const novo = new Set(prev);
        if (estava) novo.add(itemAtual.id);
        else novo.delete(itemAtual.id);
        return novo;
      });
    });
  }

  // DESIGN_TRIAGEM.md §6: t2 com menos de 10 min, t1 com menos de 1 min — como
  // fundo cheio, porque laranja em texto sobre branco não passa em contraste.
  const estadoTempo =
    restanteSeg < 60 ? "bg-t1 text-t1-on" : restanteSeg < 600 ? "bg-t2 text-t2-on" : "text-ink";
  const recorte = [itemAtual.area, itemAtual.especialidade, itemAtual.subtopico].filter(Boolean).join(" · ");
  const nomeProva = simulado.edicao && simulado.banca ? nomeEdicao(simulado.banca, simulado.edicao) : null;
  const prova = nomeProva
    ? [nomeProva, itemAtual.numero_prova ? `questão ${itemAtual.numero_prova} do caderno` : null].filter(Boolean).join(" · ")
    : [itemAtual.banca, itemAtual.ano].filter(Boolean).join(" ");
  const entradaQuestao =
    direcao === "frente" ? "animate-entrar-frente" : direcao === "tras" ? "animate-entrar-tras" : "animate-desvanecer";

  return (
    <>
      <BarraFoco>
        <span className="hidden text-[14.5px] text-ink-2 xl:block">{nomeProva ?? "Simulado"}</span>
        <span className="ml-auto shrink-0 text-[14px] font-semibold tabular-nums">
          Questão {idx + 1} de {itens.length}
        </span>
        <div className="flex shrink-0 items-center gap-2">
          <span
            aria-label="Tempo restante"
            className={`rounded-btn px-2.5 py-1 text-[24px] font-extrabold leading-none tabular-nums transition-colors duration-desliza [font-stretch:85%] ${estadoTempo}`}
          >
            {formatarTempoRestante(restanteSeg)}
          </span>
          <button
            type="button"
            onClick={alternarMarcacao}
            aria-pressed={marcadaAtual}
            className={`flex h-9 items-center gap-1.5 rounded-btn border px-3 text-[14px] font-medium transition duration-hover ${PRESSAO} ${
              marcadaAtual ? "border-t3 bg-t3-soft text-ink" : "border-line text-ink-2 hover:border-muted"
            }`}
          >
            <span key={marcadaAtual ? "marcada" : "livre"} className={`flex ${marcadaAtual ? "animate-marcar" : ""}`}>
              <Flag size={16} strokeWidth={2} />
            </span>
            <span className="hidden sm:inline">{marcadaAtual ? "Marcada" : "Marcar"}</span>
          </button>
          <button
            type="button"
            onClick={() => setDialogoAberto(true)}
            className={`flex h-9 items-center rounded-btn bg-ink px-3.5 text-[14px] font-semibold text-onink transition duration-hover hover:opacity-90 ${PRESSAO}`}
          >
            Finalizar
          </button>
        </div>
      </BarraFoco>

      <div className="mx-auto flex max-w-[680px] flex-col gap-5">
        <div key={itemAtual.item_id} className={`flex flex-col gap-5 ${entradaQuestao}`}>
          <div className="flex items-end justify-between gap-6">
            <div className="flex flex-col gap-1">
              <span className="rotulo text-muted">Questão</span>
              <span className="num-lg">{String(idx + 1).padStart(2, "0")}</span>
            </div>
            <div className="flex min-w-0 flex-col items-end gap-1.5 text-right">
              {recorte && <span className="text-[15px] font-semibold">{recorte}</span>}
              {prova && (
                <span className="flex items-center gap-1.5 text-apoio text-muted">
                  <BadgeCheck size={16} strokeWidth={2} className="text-t4" />
                  Prova oficial · {prova}
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-6 rounded-caso border border-line bg-surface p-6 md:px-11 md:py-9">
            <p className="leitura-enunciado text-ink">{itemAtual.enunciado}</p>
            {itemAtual.tem_imagem && (
              <img
                src={`${API_URL}/questoes/${itemAtual.id}/imagem`}
                alt="Imagem da questão"
                className="max-w-full rounded-card border border-line"
              />
            )}

            <div className="flex flex-col gap-2">
              {Object.keys(itemAtual.alternativas).map((letra) => (
                <AlternativaLinha
                  key={letra}
                  letra={letra}
                  texto={itemAtual.alternativas[letra]}
                  estado={letra === respostaAtual ? "selecionada" : "normal"}
                  disabled={false}
                  onClick={() => responder(letra)}
                />
              ))}
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-line-soft pt-6">
              <button type="button" onClick={() => irPara(idx - 1)} disabled={idx <= 0} className={`group ${BOTAO_SECUNDARIO}`}>
                <ArrowLeft
                  size={16}
                  strokeWidth={2}
                  className="transition-transform duration-toggle ease-suave group-enabled:group-hover:-translate-x-0.5"
                />
                Anterior
              </button>
              <button
                type="button"
                onClick={() => irPara(idx + 1)}
                disabled={idx >= itens.length - 1}
                className={`group ${BOTAO_SECUNDARIO}`}
              >
                Próxima
                <ArrowRight
                  size={16}
                  strokeWidth={2}
                  className="transition-transform duration-toggle ease-suave group-enabled:group-hover:translate-x-0.5"
                />
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 rounded-caso border border-line bg-surface p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="rotulo text-muted">Ir para questão</span>
            <div className="flex flex-wrap items-center gap-4 text-apoio text-muted">
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-[2px] bg-ink" aria-hidden="true" />
                respondida
              </span>
              <span className="flex items-center gap-1.5">
                <span className="relative h-3 w-3 overflow-hidden rounded-[2px] border border-line" aria-hidden="true">
                  <span className="absolute right-0 top-0 h-0 w-0 border-l-[7px] border-t-[7px] border-l-transparent border-t-t3" />
                </span>
                marcada
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-[2px] border border-line" aria-hidden="true" />
                em branco ({emBranco})
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {itens.map((item, i) => {
              const respondida = Boolean(respostasLocais[item.id]);
              const marcada = marcadasLocais.has(item.id);
              const atual = i === idx;
              const estado = [respondida ? "respondida" : "em branco", marcada ? "marcada" : null].filter(Boolean).join(", ");
              return (
                <button
                  key={item.item_id}
                  type="button"
                  onClick={() => irPara(i)}
                  aria-label={`Questão ${i + 1}: ${estado}`}
                  aria-current={atual ? "step" : undefined}
                  className={`relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-btn border text-[13px] font-semibold tabular-nums transition duration-toggle ease-brand ${PRESSAO} ${
                    respondida ? "border-ink bg-ink text-onink" : "border-line bg-surface text-ink-2 hover:border-muted"
                  } ${atual ? "ring-2 ring-focus ring-offset-2 ring-offset-surface" : ""}`}
                >
                  {i + 1}
                  {marcada && (
                    <span
                      className="absolute right-0 top-0 h-0 w-0 animate-desvanecer border-l-[10px] border-t-[10px] border-l-transparent border-t-t3"
                      aria-hidden="true"
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <Dialog titulo="Finalizar simulado" aberto={dialogoAberto} onFechar={() => setDialogoAberto(false)}>
        <p className="text-corpo text-ink-2">
          {emBranco > 0 ? (
            <>
              <strong className="text-ink">{emBranco}</strong> {emBranco === 1 ? "questão vai ficar" : "questões vão ficar"} em
              branco. Essa ação não pode ser desfeita.
            </>
          ) : (
            "Todas as questões foram respondidas. Confirmar o encerramento?"
          )}
        </p>
        <div className="mt-6 flex gap-2">
          <button type="button" onClick={() => setDialogoAberto(false)} className={`${BOTAO_SECUNDARIO} flex-1`}>
            Voltar à prova
          </button>
          <button type="button" onClick={finalizarAgora} disabled={finalizando} className={`${BOTAO_PRIMARIO} flex-1`}>
            Finalizar simulado
          </button>
        </div>
      </Dialog>
    </>
  );
}
