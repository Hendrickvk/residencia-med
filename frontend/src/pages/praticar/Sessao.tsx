import { useQuery } from "@tanstack/react-query";
import { Flag, Square as IconeParar } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { API_URL, api } from "../../lib/api";
import { formatarMMSS } from "../../lib/format";
import { enfileirarResposta } from "../../lib/respostasQueue";
import type { FiltrosPratica, Questao, ResumoSessao } from "../../lib/types";
import { AlternativaLinha } from "./AlternativaLinha";
import { useCronometro } from "./useCronometro";

interface Props {
  filtros: FiltrosPratica;
  nonce: number;
  onFinalizar: (resumo: ResumoSessao) => void;
}

const LETRAS = ["A", "B", "C", "D", "E"];

export default function Sessao({ filtros, nonce, onFinalizar }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["sessao-pratica", nonce],
    queryFn: () =>
      api.get<{ questoes: Questao[] }>("/praticar/sessao", {
        area_id: filtros.area_id,
        subtopico_id: filtros.subtopico_id,
        banca: filtros.banca,
        ano: filtros.ano,
        apenas_erros: filtros.apenas_erros,
        excluir_respondidas: filtros.excluir_respondidas,
        quantidade: filtros.quantidade,
      }),
    staleTime: Infinity,
    gcTime: 0,
  });

  const fila = data?.questoes ?? [];
  const [idx, setIdx] = useState(0);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [distribuicao, setDistribuicao] = useState<Record<string, number> | null>(null);
  const [marcadas, setMarcadas] = useState<Set<number>>(() => new Set());
  const respondidasRef = useRef<ResumoSessao["respondidas"]>([]);
  const inicioSessaoRef = useRef(Date.now());
  const { decorridoMs, tempoDecorridoMs } = useCronometro(idx);

  const questaoAtual = fila[idx];
  const correta = questaoAtual ? selecionada === questaoAtual.resposta_correta : false;

  useEffect(() => {
    if (data) setMarcadas(new Set(fila.filter((q) => q.marcada).map((q) => q.id)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  function confirmar() {
    if (!selecionada || !questaoAtual) return;
    setConfirmado(true);
    // % dos demais usuários por alternativa: busca não-bloqueante — o
    // feedback de acerto/erro já foi mostrado comparando com o gabarito
    // embutido no lote, sem depender desta chamada (MIGRACAO.md §2).
    api
      .get<Record<string, number>>(`/questoes/${questaoAtual.id}/distribuicao`)
      .then(setDistribuicao)
      .catch(() => {});
  }

  function avancarOuFinalizar() {
    if (idx + 1 >= fila.length) {
      onFinalizar({ respondidas: respondidasRef.current, duracaoTotalMs: Date.now() - inicioSessaoRef.current });
    } else {
      setIdx((i) => i + 1);
      setSelecionada(null);
      setConfirmado(false);
      setDistribuicao(null);
    }
  }

  function concluir(confianca: "seguro" | "chute" | undefined, foiCorreta: boolean) {
    if (!questaoAtual || !selecionada) return;
    const tempoMs = tempoDecorridoMs();
    enfileirarResposta({ questao_id: questaoAtual.id, alternativa: selecionada, confianca, tempo_ms: tempoMs });
    respondidasRef.current.push({
      id: questaoAtual.id,
      correta: foiCorreta,
      subtopico: questaoAtual.subtopico,
      tempoMs,
    });
    avancarOuFinalizar();
  }

  function alternarMarcacao() {
    if (!questaoAtual) return;
    const estavaMarcada = marcadas.has(questaoAtual.id);
    const id = questaoAtual.id;
    setMarcadas((prev) => {
      const novo = new Set(prev);
      estavaMarcada ? novo.delete(id) : novo.add(id);
      return novo;
    });
    const chamada = estavaMarcada ? api.delete(`/questoes/${id}/marcar`) : api.post(`/questoes/${id}/marcar`);
    chamada.catch(() => {
      // Reverte no cliente se o servidor recusou — a UI não pode afirmar um
      // estado de marcação que o backend não confirmou.
      setMarcadas((prev) => {
        const novo = new Set(prev);
        estavaMarcada ? novo.add(id) : novo.delete(id);
        return novo;
      });
    });
  }

  function encerrarSessao() {
    onFinalizar({ respondidas: respondidasRef.current, duracaoTotalMs: Date.now() - inicioSessaoRef.current });
  }

  // A–E seleciona, Enter confirma, → avança, M marca (REDESIGN.md §4.2).
  // → só avança quando o próximo passo é inequívoco: resposta errada tem
  // um único "Continuar", mas resposta certa exige escolher a calibração
  // (duas opções) — uma seta não pode decidir isso no lugar do aluno.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const alvo = e.target as HTMLElement | null;
      if (alvo && ["INPUT", "TEXTAREA", "SELECT"].includes(alvo.tagName)) return;
      if (!questaoAtual) return;

      const letra = e.key.length === 1 ? e.key.toUpperCase() : "";

      if (!confirmado && LETRAS.includes(letra) && letra in questaoAtual.alternativas) {
        setSelecionada(letra);
        return;
      }
      if (e.key === "Enter" && !confirmado && selecionada) {
        e.preventDefault();
        confirmar();
        return;
      }
      if ((e.key === "Enter" || e.key === "ArrowRight") && confirmado && !correta) {
        e.preventDefault();
        concluir(undefined, false);
        return;
      }
      if (letra === "M") {
        e.preventDefault();
        alternarMarcacao();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [confirmado, selecionada, questaoAtual, correta]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-[3px] w-full animate-pulse rounded-full bg-line" />
        <div className="h-40 animate-pulse rounded-panel bg-line/40" />
      </div>
    );
  }

  if (isError || fila.length === 0) {
    return (
      <div className="rounded-panel border border-line bg-surface p-8 text-center">
        <p className="text-corpo text-ink-500">Nenhuma questão encontrada para esses filtros.</p>
      </div>
    );
  }

  const marcadaAtual = marcadas.has(questaoAtual.id);
  const metadados = [questaoAtual.banca, questaoAtual.ano, questaoAtual.area, questaoAtual.subtopico]
    .filter(Boolean)
    .join("  ·  ");

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <div className="flex-1">
          <div className="h-[3px] w-full overflow-hidden rounded-full bg-line">
            <div
              className="h-full bg-action transition-[width] duration-toggle ease-brand"
              style={{ width: `${(idx / fila.length) * 100}%` }}
            />
          </div>
          <div className="mt-1.5 text-apoio text-ink-500">
            {idx + 1} de {fila.length}
          </div>
        </div>
        <div className="font-mono text-corpo tabular-nums text-ink-500">{formatarMMSS(decorridoMs)}</div>
        <button
          type="button"
          onClick={alternarMarcacao}
          title={marcadaAtual ? "Desmarcar" : "Marcar para revisão"}
          className={`rounded-btn border p-2 transition-hover ${
            marcadaAtual ? "border-action bg-action-soft text-action" : "border-line text-ink-500 hover:border-ink-300"
          }`}
        >
          <Flag size={16} strokeWidth={1.5} />
        </button>
        <button
          type="button"
          onClick={encerrarSessao}
          title="Encerrar sessão"
          className="rounded-btn border border-line p-2 text-ink-500 transition-hover hover:border-ink-300"
        >
          <IconeParar size={16} strokeWidth={1.5} />
        </button>
      </div>

      <div className="rounded-panel border border-line bg-surface p-6">
        {metadados && <div className="mb-3 text-apoio text-ink-500">{metadados}</div>}
        <p className="max-w-[68ch] text-enunciado text-ink-700">{questaoAtual.enunciado}</p>
        {questaoAtual.tem_imagem && (
          <img
            src={`${API_URL}/questoes/${questaoAtual.id}/imagem`}
            alt="Imagem da questão"
            className="mt-4 max-w-full rounded-btn border border-line"
          />
        )}

        <div className="mt-5 space-y-2">
          {LETRAS.filter((letra) => letra in questaoAtual.alternativas).map((letra) => {
            let estado: "normal" | "selecionada" | "correta" | "errada" | "neutra" = "normal";
            if (!confirmado) estado = letra === selecionada ? "selecionada" : "normal";
            else if (letra === questaoAtual.resposta_correta) estado = "correta";
            else if (letra === selecionada) estado = "errada";
            else estado = "neutra";

            return (
              <AlternativaLinha
                key={letra}
                letra={letra}
                texto={questaoAtual.alternativas[letra]}
                estado={estado}
                percentual={confirmado ? distribuicao?.[letra] : undefined}
                disabled={confirmado}
                onClick={() => setSelecionada(letra)}
              />
            );
          })}
        </div>

        {!confirmado && (
          <button
            type="button"
            onClick={confirmar}
            disabled={!selecionada}
            className="mt-5 h-10 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-line disabled:text-ink-300"
          >
            Confirmar resposta
          </button>
        )}

        {confirmado && (
          <div className="mt-5">
            {correta ? (
              <p className="text-corpo font-medium text-correct">Correto!</p>
            ) : (
              <p className="text-corpo font-medium text-wrong">
                Errado. A resposta correta é {questaoAtual.resposta_correta}.
              </p>
            )}

            {questaoAtual.explicacao && (
              <div className="mt-3 rounded-btn border border-line bg-canvas p-3 text-corpo text-ink-700">
                {questaoAtual.explicacao}
              </div>
            )}

            <div className="mt-4">
              {correta ? (
                <div>
                  <div className="mb-2 text-apoio text-ink-500">Como você chegou nessa resposta?</div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => concluir("seguro", true)}
                      className="h-9 flex-1 rounded-btn bg-action px-3 text-sm font-medium text-white transition-hover hover:bg-action-hover"
                    >
                      Acertei com segurança
                    </button>
                    <button
                      type="button"
                      onClick={() => concluir("chute", true)}
                      className="h-9 flex-1 rounded-btn border border-line px-3 text-sm text-ink-700 transition-hover hover:border-ink-300"
                    >
                      Acertei no chute
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => concluir(undefined, false)}
                  className="h-10 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
                >
                  Continuar
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 text-apoio text-ink-300">A–E seleciona · Enter confirma · → avança · M marca para revisão</div>
    </div>
  );
}
