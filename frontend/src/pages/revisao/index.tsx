import { useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, RefreshCw, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import { Kbd } from "../../components/Kbd";
import { TemaDoCaso } from "../../components/TemaDoCaso";
import { ImagemQuestao } from "../../components/ImagemQuestao";
import { CriarCartao } from "../../components/CriarCartao";
import { RelatarErro } from "../../components/RelatarErro";
import { TextoDiscussao } from "../../components/TextoDiscussao";
import { BOTAO_PRIMARIO, PRESSAO } from "../../lib/estilos";
import { BarraFoco } from "../../lib/foco";
import { rolarParaTopo } from "../../lib/movimento";
import { estimarDuracao, formatarPrazo } from "../../lib/prazo";
import { avaliarRevisao, useLevaRevisao } from "../../lib/revisao";
import { seloDasProvas } from "../../lib/simulados";
import type { QuestaoRevisao } from "../../lib/types";
import { AlternativaLinha, type EstadoAlternativa } from "../praticar/AlternativaLinha";
import { useCronometro } from "../praticar/useCronometro";
import ResumoRevisao, { type AvaliacaoSessao } from "./ResumoRevisao";

// Índice de JS Date.getDay() (0=domingo), diferente do weekday() do Python
// que o app.py original usava (0=segunda) — cuidado se algum dia comparar.
const NOME_DIA_SEMANA = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

const LETRAS = ["A", "B", "C", "D", "E"];

// Lote de "Revisar mais" depois da meta cumprida: pequeno, e só se o aluno pedir.
const LOTE_EXTRA = 10;

// DESIGN_TRIAGEM.md §6: depois de acertar, o aluno diz como foi lembrar. O
// prazo de cada botão vem do servidor (repeticao_espacada.prever_prazos) —
// nunca escrito fixo aqui.
const NOTAS_ACERTO = [
  { nota: 3, chave: "3", label: "Com esforço", tecla: "1", cor: "bg-t2" },
  { nota: 4, chave: "4", label: "Lembrei", tecla: "2", cor: "bg-t4" },
  { nota: 5, chave: "5", label: "Fácil", tecla: "3", cor: "bg-t5" },
] as const;

export default function Revisao() {
  // 0 = só o que cabe na meta de hoje; LOTE_EXTRA depois de "Revisar mais".
  const [extra, setExtra] = useState(0);
  const { data, isLoading, isPaused, refetch } = useLevaRevisao(extra);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  // Cópia local só depois que o aluno muda a ordem (erro reinsere o caso
  // mais adiante); até lá a fila exibida é a do servidor.
  const [filaSessao, setFilaSessao] = useState<QuestaoRevisao[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  // O primeiro caso só esmaece; os seguintes deslizam, como no Praticar.
  const [avancou, setAvancou] = useState(false);
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoSessao[]>([]);
  const { tempoDecorridoMs } = useCronometro(idx);

  const fila = filaSessao ?? data?.fila ?? [];
  const restantes = Math.max(fila.length - idx, 0);
  const q = fila[idx];
  const acertou = q ? selecionada === q.resposta_correta : false;

  // A contagem da aba e do Painel vem do servidor: atualiza ao sair da Revisão.
  useEffect(() => {
    return () => {
      void queryClient.invalidateQueries({ queryKey: ["painel"] });
    };
  }, [queryClient]);

  function limparCaso() {
    setSelecionada(null);
    setConfirmado(false);
  }

  function reiniciarSessao() {
    setIdx(0);
    limparCaso();
    setFilaSessao(null);
    setAvaliacoes([]);
    setAvancou(true);
    rolarParaTopo();
    void queryClient.invalidateQueries({ queryKey: ["painel"] });
  }

  function recomecar() {
    reiniciarSessao();
    void refetch();
  }

  function revisarMais() {
    reiniciarSessao();
    // Mudar `extra` já busca a fila nova; se já era o lote extra, busca de novo.
    if (extra === LOTE_EXTRA) void refetch();
    else setExtra(LOTE_EXTRA);
  }

  async function avaliar(nota: number) {
    if (!q || !selecionada || !confirmado || enviando) return;
    const certa = selecionada === q.resposta_correta;
    const qualidade = certa ? nota : 1;
    setEnviando(true);
    // Tempo do caso inteiro (ler, responder, ler a discussão), como no Praticar:
    // é o que alimenta a estimativa de duração da revisão.
    const tempoMs = tempoDecorridoMs();
    // Mesma política de antes: se a gravação falhar, a sessão segue.
    const resultado = await avaliarRevisao(q.id, { qualidade, alternativa: selecionada, tempo_ms: tempoMs }).catch(
      () => null,
    );
    setEnviando(false);
    setAvaliacoes((anteriores) => [
      ...anteriores,
      {
        id: q.id,
        correta: certa,
        qualidade,
        primeira: !anteriores.some((a) => a.id === q.id),
        recuperado: resultado?.recuperado ?? false,
        consolidou: resultado?.consolidou ?? false,
      },
    ]);
    if (!certa) {
      // O servidor já agenda de verdade para 10 minutos, mas a fila que o
      // cliente buscou não saberia disso sozinha: sem reinserir, o caso sumia
      // da sessão. Volta com os prazos recalculados a partir do erro.
      const copia = [...fila];
      copia.splice(Math.min(idx + 4, copia.length), 0, resultado ? { ...q, prazos: resultado.prazos } : q);
      setFilaSessao(copia);
    }
    setIdx((i) => i + 1);
    limparCaso();
    setAvancou(true);
    rolarParaTopo();
  }

  // A–E seleciona, Enter confirma. Depois de confirmar: acertou, 1/2/3 dão a
  // nota; errou, Enter ou → vai para o próximo (a nota é do gabarito).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const alvo = e.target as HTMLElement | null;
      if (alvo && ["INPUT", "TEXTAREA", "SELECT"].includes(alvo.tagName)) return;
      if (!q) return;

      const letra = e.key.length === 1 ? e.key.toUpperCase() : "";
      if (!confirmado) {
        if (LETRAS.includes(letra) && letra in q.alternativas) setSelecionada(letra);
        else if (e.key === "Enter" && selecionada) {
          e.preventDefault();
          setConfirmado(true);
        }
        return;
      }
      if (acertou) {
        const opcao = NOTAS_ACERTO.find((o) => o.tecla === e.key);
        if (opcao) {
          e.preventDefault();
          void avaliar(opcao.nota);
        }
      } else if (e.key === "Enter" || e.key === "ArrowRight") {
        e.preventDefault();
        void avaliar(1);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, confirmado, selecionada, acertou, enviando]);

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-[680px] flex-col gap-5">
        <div className="h-[72px] w-32 animate-pulse rounded-card bg-line-soft" />
        <div className="h-[360px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  // Mesma regra do Painel: falha não é fila vazia, e só vale quando não há nada
  // para mostrar — `filaSessao` é revisão em andamento, e dado em cache segue
  // na tela mesmo com refetch falhado.
  if (!data && !filaSessao) {
    return (
      <div className="mx-auto max-w-[680px]">
        <EstadoFalha
          mensagem="Não deu para carregar a sua fila de revisão. Pode ser a conexão."
          pausado={isPaused}
          onTentarDeNovo={() => refetch()}
        />
      </div>
    );
  }

  if (!q) {
    if (avaliacoes.length > 0) {
      return (
        <div className="animate-entrar">
          <ResumoRevisao avaliacoes={avaliacoes} onRecomecar={recomecar} onRevisarMais={revisarMais} />
        </div>
      );
    }
    const hoje = data?.hoje;
    // Meta cumprida com casos esperando: nada de alerta, e mais só se pedir.
    if (hoje && hoje.excedente > 0) {
      return (
        <div className="mx-auto max-w-[680px] animate-entrar">
          <EstadoVazio
            mensagem={`Meta de hoje cumprida: ${hoje.feitas_hoje} caso${hoje.feitas_hoje !== 1 ? "s" : ""} revisado${
              hoje.feitas_hoje !== 1 ? "s" : ""
            }. Outros ${hoje.excedente} já venceram e podem esperar até amanhã.`}
            cta={{ label: `Revisar mais ${Math.min(LOTE_EXTRA, hoje.excedente)}`, onClick: revisarMais }}
          />
        </div>
      );
    }
    return (
      <div className="mx-auto max-w-[680px] animate-entrar">
        <EstadoVazio
          mensagem={
            data?.proxima_leva
              ? `Nenhuma revisão vencida hoje. As próximas ${data.proxima_leva.total} vencem ${
                  NOME_DIA_SEMANA[new Date(`${data.proxima_leva.dia}T00:00:00`).getDay()]
                }.`
              : "Nenhuma revisão vencida hoje."
          }
          cta={{ label: "Praticar casos novos", onClick: () => navigate("/praticar") }}
        />
      </div>
    );
  }

  // Sem o tema, que só entra na discussão (TemaDoCaso).
  const recorte = [q.area, q.especialidade].filter(Boolean).join(" · ");
  // Todas as provas em que o caso caiu, não só o caderno principal.
  const prova = seloDasProvas(q);

  return (
    <>
      <BarraFoco>
        <span className="hidden text-[14.5px] text-ink-2 xl:block">Revisão espaçada</span>
        <span className="ml-auto shrink-0 text-[14px] font-semibold tabular-nums">
          {restantes} restante{restantes !== 1 ? "s" : ""}
          {data && (
            <span className="hidden font-normal text-muted sm:inline">
              {" "}
              · {estimarDuracao(restantes, data.hoje.segundos_por_caso)}
            </span>
          )}
        </span>
        {/* Em tela estreita fica só o ícone: o rótulo inteiro empurrava o
            "Sair" para fora da barra. Mesmo padrão do Simulado. */}
        <button
          type="button"
          onClick={recomecar}
          title="Recomeçar fila"
          aria-label="Recomeçar fila"
          className={`group flex h-9 shrink-0 items-center gap-1.5 rounded-btn border border-line px-2.5 text-[14px] font-medium text-ink-2 transition duration-hover hover:border-muted hover:text-ink sm:px-3 ${PRESSAO}`}
        >
          <RotateCcw
            size={15}
            strokeWidth={2}
            className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]"
          />
          <span className="hidden sm:inline">Recomeçar fila</span>
        </button>
        {/* Cada avaliação já foi gravada ao clicar: sair não perde nada. */}
        <button
          type="button"
          onClick={() => navigate("/painel")}
          title="Sair da revisão (o que você já avaliou está salvo)"
          className="flex h-9 shrink-0 items-center px-2.5 text-[14px] font-medium text-muted transition duration-hover hover:text-ink"
        >
          Sair
        </button>
      </BarraFoco>

      <div className="mx-auto max-w-[680px]">
        <div key={idx} className={`flex flex-col gap-5 ${avancou ? "animate-entrar-frente" : "animate-desvanecer"}`}>
          <div className="flex items-end justify-between gap-6">
            <div className="flex flex-col gap-1">
              <span className="rotulo text-muted">Caso</span>
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
            <p className="leitura-enunciado text-ink">{q.enunciado}</p>
            {q.tem_imagem && (
              <ImagemQuestao questaoId={q.id} alt="Imagem do caso" />
            )}

            <div className="flex flex-col gap-2">
              {LETRAS.filter((letra) => letra in q.alternativas).map((letra) => {
                let estado: EstadoAlternativa = "normal";
                if (!confirmado) estado = letra === selecionada ? "selecionada" : "normal";
                else if (letra === q.resposta_correta) estado = "correta";
                else if (letra === selecionada) estado = "errada";
                else estado = "neutra";
                return (
                  <AlternativaLinha
                    key={letra}
                    letra={letra}
                    texto={q.alternativas[letra]}
                    estado={estado}
                    // null: mostra as etiquetas de conduta, sem coluna de percentual.
                    percentual={confirmado ? null : undefined}
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
                </div>
                <button
                  type="button"
                  onClick={() => setConfirmado(true)}
                  disabled={!selecionada}
                  className={`${BOTAO_PRIMARIO} ml-auto pr-2.5`}
                >
                  Confirmar resposta
                  <Kbd sobreTinta>Enter</Kbd>
                </button>
              </div>
            ) : (
              <>
                <div className="flex animate-entrar flex-col gap-3 border-t border-line-soft pt-6">
                  <span className="rotulo text-muted">Discussão do caso</span>
                  <span className="text-subtitulo">Resposta correta: {q.resposta_correta}</span>
                  <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                    <TemaDoCaso tema={q.subtopico} />
                    <div className="flex flex-wrap items-center gap-4">
                      <CriarCartao
                        questaoId={q.id}
                        respostaCorreta={q.alternativas[q.resposta_correta]}
                      />
                      <RelatarErro questaoId={q.id} />
                    </div>
                  </div>
                  {q.explicacao && <TextoDiscussao texto={q.explicacao} />}
                </div>

                {acertou ? (
                  <div
                    className="flex animate-entrar flex-col gap-3 border-t border-line-soft pt-6"
                    style={{ animationDelay: "90ms" }}
                  >
                    <span className="text-apoio text-muted">Você acertou. Como foi lembrar?</span>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      {NOTAS_ACERTO.map((op) => (
                        <button
                          key={op.nota}
                          type="button"
                          disabled={enviando}
                          onClick={() => void avaliar(op.nota)}
                          className="group flex flex-col items-start gap-1 rounded-btn border border-line bg-surface px-3.5 py-2.5 text-left transition duration-hover ease-brand hover:border-muted active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
                        >
                          <span className="flex w-full items-center justify-between gap-2">
                            <span className="flex items-center gap-2 text-[15px] font-medium text-ink">
                              <span
                                className={`h-2.5 w-2.5 shrink-0 rounded-[2px] transition-transform duration-toggle ease-suave group-hover:scale-125 ${op.cor}`}
                                aria-hidden="true"
                              />
                              {op.label}
                            </span>
                            <Kbd>{op.tecla}</Kbd>
                          </span>
                          <span className="text-apoio tabular-nums text-muted">volta em {formatarPrazo(q.prazos[op.chave])}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div
                    className="flex animate-entrar flex-wrap items-center justify-between gap-3"
                    style={{ animationDelay: "90ms" }}
                  >
                    <span className="flex items-center gap-2 text-apoio text-ink-2">
                      <RefreshCw size={16} strokeWidth={2} />
                      Volta na sua revisão em {formatarPrazo(q.prazos["1"])}
                    </span>
                    <button
                      type="button"
                      disabled={enviando}
                      onClick={() => void avaliar(1)}
                      className={`${BOTAO_PRIMARIO} pr-2.5`}
                    >
                      Próximo caso
                      <Kbd sobreTinta>Enter</Kbd>
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
