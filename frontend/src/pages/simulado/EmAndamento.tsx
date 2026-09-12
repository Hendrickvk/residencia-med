import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Flag } from "lucide-react";
import { useState } from "react";
import { API_URL, api } from "../../lib/api";
import { formatarMMSS } from "../../lib/format";
import { finalizarSimulado, responderSimulado, useItensSimulado, useSimulado } from "../../lib/simulados";
import type { ItemSimulado, Simulado } from "../../lib/types";
import { AlternativaLinha } from "../praticar/AlternativaLinha";
import { Dialog } from "../../components/Dialog";
import { useCronometroRegressivo } from "./useCronometroRegressivo";

interface Props {
  simuladoId: number;
  onFinalizado: () => void;
}

export default function EmAndamento({ simuladoId, onFinalizado }: Props) {
  const { data: simulado, isLoading: carregandoSimulado } = useSimulado(simuladoId);
  const { data: itens, isLoading: carregandoItens } = useItensSimulado(simuladoId);

  if (carregandoSimulado || carregandoItens || !simulado || !itens) {
    return <div className="h-96 animate-pulse rounded-panel bg-line/40" />;
  }

  return (
    <Conteudo simuladoId={simuladoId} simulado={simulado} itens={itens} onFinalizado={onFinalizado} />
  );
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
  const [idx, setIdx] = useState(0);
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
      estava ? novo.delete(itemAtual.id) : novo.add(itemAtual.id);
      return novo;
    });
    const chamada = estava
      ? api.delete(`/questoes/${itemAtual.id}/marcar`)
      : api.post(`/questoes/${itemAtual.id}/marcar`);
    chamada.catch(() => {
      setMarcadasLocais((prev) => {
        const novo = new Set(prev);
        estava ? novo.add(itemAtual.id) : novo.delete(itemAtual.id);
        return novo;
      });
    });
  }

  const corTempo = restanteSeg < 60 ? "text-wrong" : restanteSeg < 600 ? "text-warn" : "text-ink-700";
  const metadados = [itemAtual.banca, itemAtual.ano, itemAtual.area, itemAtual.subtopico].filter(Boolean).join("  ·  ");

  return (
    <div>
      <div className="mb-4 flex items-center gap-4">
        <div className={`font-mono text-h1 tabular-nums ${corTempo}`}>{formatarMMSS(restanteSeg, "s")}</div>
        <div className="flex-1 text-apoio text-ink-500">
          Questão {idx + 1} de {itens.length}
        </div>
        <button
          type="button"
          onClick={alternarMarcacao}
          title={marcadaAtual ? "Desmarcar" : "Marcar para revisão"}
          className={`rounded-btn border p-2 transition-hover ${
            marcadaAtual ? "border-warn bg-warn-soft text-warn" : "border-line text-ink-500 hover:border-ink-300"
          }`}
        >
          <Flag size={16} strokeWidth={1.5} />
        </button>
      </div>

      <div className="rounded-panel border border-line bg-surface p-6">
        {metadados && <div className="mb-3 text-apoio text-ink-500">{metadados}</div>}
        <p className="max-w-[68ch] text-enunciado text-ink-700">{itemAtual.enunciado}</p>
        {itemAtual.tem_imagem && (
          <img
            src={`${API_URL}/questoes/${itemAtual.id}/imagem`}
            alt="Imagem da questão"
            className="mt-4 max-w-full rounded-btn border border-line"
          />
        )}

        <div className="mt-5 space-y-2">
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
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={() => setIdx((i) => Math.max(0, i - 1))}
          disabled={idx <= 0}
          className="flex h-9 flex-1 items-center justify-center gap-1.5 rounded-btn border border-line text-apoio text-ink-700 transition-hover hover:border-ink-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ArrowLeft size={14} strokeWidth={1.5} />
          Anterior
        </button>
        <button
          type="button"
          onClick={() => setIdx((i) => Math.min(itens.length - 1, i + 1))}
          disabled={idx >= itens.length - 1}
          className="flex h-9 flex-1 items-center justify-center gap-1.5 rounded-btn border border-line text-apoio text-ink-700 transition-hover hover:border-ink-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Próxima
          <ArrowRight size={14} strokeWidth={1.5} />
        </button>
      </div>

      <div className="mt-5">
        <div className="mb-2 text-apoio text-ink-500">Ir para questão</div>
        <div className="flex flex-wrap gap-2">
          {itens.map((item, i) => {
            const respondida = Boolean(respostasLocais[item.id]);
            const marcada = marcadasLocais.has(item.id);
            const atual = i === idx;
            return (
              <button
                key={item.item_id}
                type="button"
                onClick={() => setIdx(i)}
                title={marcada ? "Marcada para revisão" : respondida ? "Respondida" : "Em branco"}
                className={`relative flex h-8 w-8 items-center justify-center rounded-btn border text-apoio font-medium transition-hover ${
                  respondida ? "border-action bg-action text-white" : "border-line text-ink-500 hover:border-ink-300"
                } ${atual ? "ring-2 ring-action ring-offset-1 ring-offset-surface" : ""}`}
              >
                {i + 1}
                {marcada && <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-warn" aria-hidden="true" />}
              </button>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={() => setDialogoAberto(true)}
        className="mt-6 h-10 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        Finalizar simulado
      </button>

      <Dialog titulo="Finalizar simulado" aberto={dialogoAberto} onFechar={() => setDialogoAberto(false)}>
        {emBranco > 0 ? (
          <p className="text-corpo text-ink-700">
            <strong>{emBranco}</strong> questão(ões) ficarão em branco. Essa ação não pode ser desfeita.
          </p>
        ) : (
          <p className="text-corpo text-ink-700">Todas as questões foram respondidas. Confirmar o encerramento?</p>
        )}
        <div className="mt-5 flex gap-2">
          <button
            type="button"
            onClick={() => setDialogoAberto(false)}
            className="h-10 flex-1 rounded-btn border border-line text-sm text-ink-700 transition-hover hover:border-ink-300"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={finalizarAgora}
            disabled={finalizando}
            className="h-10 flex-1 rounded-btn bg-action text-sm font-medium text-white transition-hover hover:bg-action-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            Finalizar
          </button>
        </div>
      </Dialog>
    </div>
  );
}
