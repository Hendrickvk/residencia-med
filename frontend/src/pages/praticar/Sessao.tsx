import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, Clock, Flag, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { EstadoVazio } from "../../components/EstadoVazio";
import { Kbd } from "../../components/Kbd";
import { API_URL, api } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { BarraFoco } from "../../lib/foco";
import { formatarMMSS } from "../../lib/format";
import { enfileirarResposta } from "../../lib/respostasQueue";
import type { FiltrosPratica, Questao, ResumoSessao } from "../../lib/types";
import { AlternativaLinha, type EstadoAlternativa } from "./AlternativaLinha";
import { useCronometro } from "./useCronometro";

interface Props {
  filtros: FiltrosPratica;
  nonce: number;
  onFinalizar: (resumo: ResumoSessao) => void;
  onVoltar: () => void;
}

const LETRAS = ["A", "B", "C", "D", "E"];

export default function Sessao({ filtros, nonce, onFinalizar, onVoltar }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["sessao-pratica", nonce],
    queryFn: () =>
      api.get<{ questoes: Questao[] }>("/praticar/sessao", {
        area_id: filtros.area_id,
        especialidade_id: filtros.especialidade_id,
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
  // Acerto/erro de cada caso já concluído, para o progresso na barra de foco.
  const [resultados, setResultados] = useState<boolean[]>([]);
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
      area: questaoAtual.area,
      especialidade: questaoAtual.especialidade,
      tempoMs,
    });
    setResultados((r) => [...r, foiCorreta]);
    avancarOuFinalizar();
  }

  function alternarMarcacao() {
    if (!questaoAtual) return;
    const estavaMarcada = marcadas.has(questaoAtual.id);
    const id = questaoAtual.id;
    setMarcadas((prev) => {
      const novo = new Set(prev);
      if (estavaMarcada) novo.delete(id);
      else novo.add(id);
      return novo;
    });
    const chamada = estavaMarcada ? api.delete(`/questoes/${id}/marcar`) : api.post(`/questoes/${id}/marcar`);
    chamada.catch(() => {
      // Reverte no cliente se o servidor recusou — a UI não pode afirmar um
      // estado de marcação que o backend não confirmou.
      setMarcadas((prev) => {
        const novo = new Set(prev);
        if (estavaMarcada) novo.add(id);
        else novo.delete(id);
        return novo;
      });
    });
  }

  function encerrarSessao() {
    onFinalizar({ respondidas: respondidasRef.current, duracaoTotalMs: Date.now() - inicioSessaoRef.current });
  }

  // A–E seleciona, Enter confirma, → avança, M marca (MIGRACAO.md §4, Fase 3).
  // → só avança quando o próximo passo é inequívoco: resposta errada tem
  // um único "Próximo caso", mas resposta certa exige escolher a calibração
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
      <>
        <BarraFoco>
          <span className="text-[14.5px] text-ink-2">Sessão de prática</span>
        </BarraFoco>
        <div className="mx-auto flex max-w-[840px] flex-col gap-5">
          <div className="h-[72px] w-32 animate-pulse rounded-card bg-line-soft" />
          <div className="h-[520px] animate-pulse rounded-caso bg-line-soft" />
        </div>
      </>
    );
  }

  if (isError || fila.length === 0) {
    return (
      <div className="mx-auto max-w-[840px]">
        <EstadoVazio
          mensagem="Nenhum caso encontrado para esses filtros. Amplie o recorte e tente de novo."
          cta={{ label: "Ajustar filtros", onClick: onVoltar }}
        />
      </div>
    );
  }

  const marcadaAtual = marcadas.has(questaoAtual.id);
  const recorteSessao = filtros.especialidade_id
    ? fila[0]?.especialidade
    : filtros.area_id
      ? fila[0]?.area
      : null;
  const recorteCaso = [questaoAtual.area, questaoAtual.especialidade, questaoAtual.subtopico]
    .filter(Boolean)
    .join(" · ");
  const prova = [questaoAtual.banca, questaoAtual.ano].filter(Boolean).join(" ");
  // `{}` = ninguém além do próprio aluno respondeu ainda (db.distribuicao_respostas_questao
  // exclui o usuário atual). Sem esse caso, todas as alternativas apareciam com 0%.
  const distribuicaoVazia = distribuicao !== null && Object.keys(distribuicao).length === 0;
  const pctEscolha =
    selecionada && distribuicao && !distribuicaoVazia ? (distribuicao[selecionada] ?? 0) : undefined;

  return (
    <>
      <BarraFoco>
        <span className="hidden min-w-0 truncate text-[14.5px] text-ink-2 xl:block">
          Sessão de prática{recorteSessao ? ` · ${recorteSessao}` : ""}
        </span>
        <div className="ml-auto flex min-w-0 flex-1 items-center justify-end gap-3">
          <div className="hidden w-full max-w-[440px] gap-[3px] md:flex" aria-hidden="true">
            {fila.map((q, i) => {
              let cor = "bg-line";
              if (i < resultados.length) cor = resultados[i] ? "bg-t4" : "bg-t1";
              else if (i === idx) cor = confirmado ? (correta ? "bg-t4" : "bg-t1") : "bg-ink";
              return <span key={q.id} className={`h-2 flex-1 rounded-[2px] ${cor}`} />;
            })}
          </div>
          <span className="shrink-0 text-[14px] font-semibold tabular-nums">
            {idx + 1} de {fila.length}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="flex items-center gap-1.5 pr-2 text-[15px] font-semibold tabular-nums">
            <Clock size={16} strokeWidth={2} />
            {formatarMMSS(decorridoMs)}
          </span>
          <button
            type="button"
            onClick={alternarMarcacao}
            aria-pressed={marcadaAtual}
            title={marcadaAtual ? "Desmarcar caso (M)" : "Marcar para revisão (M)"}
            className={`flex h-9 items-center gap-1.5 rounded-btn border px-3 text-[14px] font-medium transition duration-hover ${
              marcadaAtual ? "border-t3 bg-t3-soft text-ink" : "border-line text-ink-2 hover:border-muted"
            }`}
          >
            <Flag size={16} strokeWidth={2} />
            <span className="hidden sm:inline">{marcadaAtual ? "Marcado" : "Marcar"}</span>
          </button>
          <button
            type="button"
            onClick={encerrarSessao}
            className="flex h-9 items-center px-2.5 text-[14px] font-medium text-muted transition duration-hover hover:text-ink"
          >
            Encerrar
          </button>
        </div>
      </BarraFoco>

      <div className="mx-auto flex max-w-[840px] flex-col gap-5">
        <div className="flex items-end justify-between gap-6">
          <div className="flex flex-col gap-1">
            <span className="rotulo text-muted">Caso</span>
            <span className="num-lg">{String(idx + 1).padStart(2, "0")}</span>
          </div>
          <div className="flex min-w-0 flex-col items-end gap-1.5 text-right">
            {recorteCaso && <span className="text-[15px] font-semibold">{recorteCaso}</span>}
            {prova && (
              <span className="flex items-center gap-1.5 text-apoio text-muted">
                <BadgeCheck size={16} strokeWidth={2} className="text-t4" />
                Prova oficial · {prova}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-6 rounded-caso border border-line bg-surface p-6 md:px-11 md:py-9">
          <p className="max-w-[68ch] text-enunciado text-ink">{questaoAtual.enunciado}</p>
          {questaoAtual.tem_imagem && (
            <img
              src={`${API_URL}/questoes/${questaoAtual.id}/imagem`}
              alt="Imagem do caso"
              className="max-w-full rounded-card border border-line"
            />
          )}

          <div className="flex flex-col gap-2">
            {LETRAS.filter((letra) => letra in questaoAtual.alternativas).map((letra) => {
              let estado: EstadoAlternativa = "normal";
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
                  percentual={
                    confirmado ? (distribuicao && !distribuicaoVazia ? (distribuicao[letra] ?? 0) : null) : undefined
                  }
                  disabled={confirmado}
                  onClick={() => setSelecionada(letra)}
                />
              );
            })}
          </div>

          {!confirmado ? (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="hidden items-center gap-4 text-apoio text-muted sm:flex">
                <span className="flex items-center gap-1.5">
                  <Kbd>A–E</Kbd>selecionar
                </span>
                <span className="flex items-center gap-1.5">
                  <Kbd>M</Kbd>marcar
                </span>
              </div>
              <button type="button" onClick={confirmar} disabled={!selecionada} className={`${BOTAO_PRIMARIO} ml-auto pr-2.5`}>
                Confirmar resposta
                <Kbd sobreTinta>Enter</Kbd>
              </button>
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-3 border-t border-line-soft pt-6">
                <span className="rotulo text-muted">Discussão do caso</span>
                <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                  <span className="text-subtitulo">Resposta correta: {questaoAtual.resposta_correta}</span>
                  {/* Altura reservada: a frase só entra quando a distribuição chega. */}
                  <span className="min-h-[1.45em] text-apoio text-muted">
                    {distribuicaoVazia
                      ? "Ninguém mais respondeu este caso ainda."
                      : pctEscolha === undefined
                        ? null
                        : pctEscolha === 0
                          ? `Nenhum outro aluno marcou ${selecionada}.`
                          : correta
                            ? `Você acertou, como ${Math.round(pctEscolha)}% dos outros alunos`
                            : `Você marcou ${selecionada}, como ${Math.round(pctEscolha)}% dos outros alunos`}
                  </span>
                </div>
                {questaoAtual.explicacao && (
                  <p className="max-w-[66ch] text-[16.5px] leading-[1.7] text-ink-2">{questaoAtual.explicacao}</p>
                )}
              </div>

              {correta ? (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="text-apoio text-muted">Como você chegou nessa resposta?</span>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" onClick={() => concluir("chute", true)} className={BOTAO_SECUNDARIO}>
                      Acertei no chute
                    </button>
                    <button type="button" onClick={() => concluir("seguro", true)} className={BOTAO_PRIMARIO}>
                      Acertei com segurança
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-apoio text-ink-2">
                    <RefreshCw size={16} strokeWidth={2} />
                    Volta na sua revisão em 10 min
                  </span>
                  <button type="button" onClick={() => concluir(undefined, false)} className={`${BOTAO_PRIMARIO} pr-2.5`}>
                    Próximo caso
                    <Kbd sobreTinta>Enter</Kbd>
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
