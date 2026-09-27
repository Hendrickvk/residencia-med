import { ArrowRight, ChevronDown, RotateCcw, Share2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { TemaDoCaso } from "../../components/TemaDoCaso";
import { AvisoGabaritoProvisorio } from "../../components/AvisoGabaritoProvisorio";
import { ImagemQuestao } from "../../components/ImagemQuestao";
import { CriarCartao } from "../../components/CriarCartao";
import { RelatarErro } from "../../components/RelatarErro";
import { TextoDiscussao } from "../../components/TextoDiscussao";
import { compartilharCartao, type DadosCartao, desenharCartao, nomeArquivoCartao } from "../../lib/cartaoResultado";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { formatarMMSS, formatarNumeroBR, formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import {
  distanciaDoCorte,
  nomeEdicao,
  nomeProvaOficial,
  useDesempenhoSimulado,
  useItensSimulado,
  useSimulado,
  useTemasErradosSimulado,
} from "../../lib/simulados";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";
import type { ComparacaoCorte, ProvaEmBlocos } from "../../lib/types";
import { AlternativaLinha, type EstadoAlternativa } from "../praticar/AlternativaLinha";

interface Props {
  simuladoId: number;
  onNovoSimulado: () => void;
}

// Temas para revisar mostrados antes de "Mostrar todos".
const TEMAS_VISIVEIS = 8;

export default function Resultado({ simuladoId, onNovoSimulado }: Props) {
  const { data: simulado } = useSimulado(simuladoId);
  const { data: itens } = useItensSimulado(simuladoId);
  const { data: desempenho } = useDesempenhoSimulado(simuladoId);
  const { data: temas } = useTemasErradosSimulado(simuladoId);
  const [abertos, setAbertos] = useState<Set<number>>(new Set());
  const [todosTemas, setTodosTemas] = useState(false);
  const navigate = useNavigate();
  // Cartão para compartilhar (lib/cartaoResultado.ts): o da prova oficial
  // inteira ou, no resultado do bloco que fecha a prova, o da prova em blocos
  // somada — um bloco solto não é o resultado de uma prova. Desenhado assim que
  // o resultado chega, para o toque em "Compartilhar" abrir o compartilhamento
  // na hora.
  const [cartao, setCartao] = useState<File | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const dadosCartao = useMemo<DadosCartao | null>(() => {
    if (!simulado?.edicao || !simulado.banca) return null;
    const prova = nomeEdicao(simulado.banca, simulado.edicao);
    if (!simulado.bloco) {
      if (!desempenho) return null;
      const t = simulado.num_questoes;
      const a = simulado.acertos ?? 0;
      return { prova, pct: t ? Math.round((100 * a) / t) : 0, acertos: a, total: t, areas: desempenho };
    }
    const p = simulado.prova_em_blocos;
    if (!p) return null;
    return { prova, pct: Math.round(p.pct_acerto), acertos: p.acertos, total: p.num_questoes, areas: p.areas, emBlocos: true };
  }, [simulado, desempenho]);
  useEffect(() => {
    if (!dadosCartao) return;
    let vivo = true;
    desenharCartao(dadosCartao)
      .then((blob) => {
        if (vivo) setCartao(new File([blob], nomeArquivoCartao(dadosCartao.prova), { type: "image/png" }));
      })
      .catch(() => {});
    return () => {
      vivo = false;
    };
  }, [dadosCartao]);

  if (!simulado || !itens) {
    return (
      <div className="mx-auto flex max-w-[680px] flex-col gap-6">
        <div className="h-[110px] animate-pulse rounded-card bg-line-soft" />
        <div className="h-[160px] animate-pulse rounded-caso bg-line-soft" />
        <div className="h-[320px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  const total = simulado.num_questoes;
  const acertos = simulado.acertos ?? 0;
  const respondidas = simulado.total_respondidas ?? 0;
  // Com uma casa, como no Painel, e o nível pelo valor exato: arredondado, 58,6%
  // virava "59%" ao lado de "0,4 ponto abaixo do corte de 59".
  const pct = total ? (100 * acertos) / total : 0;
  const nivel = nivelTriagem(pct);
  const areas = [...(desempenho ?? [])].sort((a, b) => a.pct_acerto - b.pct_acerto);
  const nomeProva = nomeProvaOficial(simulado);
  const nesta = simulado.bloco ? "neste bloco" : nomeProva ? "nesta prova" : "neste simulado";
  // Tempo de tela (db.somar_tempo_simulado); simulado de antes da medição não tem.
  const tempoTotalMs = itens.reduce((soma, i) => soma + (i.tempo_ms ?? 0), 0);
  const comTempo = tempoTotalMs > 0 && respondidas > 0;
  const mediaMs = comTempo ? tempoTotalMs / respondidas : 0;
  // Ritmo que o tempo do simulado dá a cada questão: 3 min na prova oficial.
  const ritmoMs = (simulado.tempo_limite_min * 60_000) / total;
  const acimaDoRitmo = itens.filter((i) => (i.tempo_ms ?? 0) > ritmoMs).length;

  function alternar(itemId: number) {
    setAbertos((prev) => {
      const novo = new Set(prev);
      if (novo.has(itemId)) novo.delete(itemId);
      else novo.add(itemId);
      return novo;
    });
  }

  return (
    <div className="mx-auto flex max-w-[680px] animate-desvanecer flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">{nomeProva ? `Resultado · ${nomeProva}` : "Resultado do simulado"}</span>
        <h1 className="text-titulo">
          {acertos} de {total} questões certas.
        </h1>
      </div>

      {simulado.gabarito_preliminar && <AvisoGabaritoProvisorio fundo="bg-surface" />}

      {/* A primeira coluna mais larga: com uma casa decimal, "100,0%" não cabia num terço. */}
      <div className="grid grid-cols-1 divide-y divide-line-soft rounded-caso border border-line bg-surface sm:grid-cols-[1.5fr_1fr_1fr] sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Aproveitamento</span>
          <NumeroAnimado className="num-lg self-start" valor={pct} formatar={(v) => `${formatarPctBR(v, 1)}%`} />
          <span
            className={`rotulo animate-surgir self-start rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
            style={{ animationDelay: "750ms" }}
          >
            {NIVEIS[nivel - 1].nome}
          </span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Respondidas</span>
          <span className="num-lg">{respondidas}</span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Em branco</span>
          <span className="num-lg">{Math.max(total - respondidas, 0)}</span>
        </div>
      </div>

      {simulado.corte && <LinhaCorte corte={simulado.corte} />}
      {simulado.bloco && simulado.prova_em_blocos && <ProvaCompleta dados={simulado.prova_em_blocos} />}

      {dadosCartao && (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            disabled={!cartao}
            onClick={async () => {
              if (!cartao) return;
              const resultado = await compartilharCartao(cartao, dadosCartao.prova, dadosCartao.pct, dadosCartao.emBlocos);
              setAviso(resultado === "baixado" ? "A imagem foi para a pasta de downloads." : null);
            }}
            className={BOTAO_SECUNDARIO}
          >
            <Share2 size={18} strokeWidth={2} aria-hidden="true" />
            {dadosCartao.emBlocos ? "Compartilhar a prova inteira" : "Compartilhar resultado"}
          </button>
          {aviso && (
            <span role="status" className="text-apoio text-muted">
              {aviso}
            </span>
          )}
        </div>
      )}

      {comTempo && (
        <p className="text-corpo text-ink-2">
          Tempo médio de <strong className="font-semibold text-ink">{formatarMMSS(mediaMs)}</strong> por questão
          respondida, {mediaMs > ritmoMs ? "acima" : "dentro"} do ritmo de {formatarMMSS(ritmoMs)}{" "}
          {nomeProva ? "da prova" : "do simulado"}.
          {acimaDoRitmo > 0 && ` Em ${acimaDoRitmo} ${acimaDoRitmo === 1 ? "questão" : "questões"}, você passou desse tempo.`}
        </p>
      )}

      {areas.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-bloco">Desempenho por área {nesta}</h2>
          <div className="rounded-caso border border-line bg-surface">
            {areas.map((d, i) => {
              const nv = nivelTriagem(d.pct_acerto);
              return (
                <div
                  key={d.area}
                  className="grid animate-entrar grid-cols-[minmax(0,1fr)_minmax(80px,200px)_52px_48px] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
                  style={atraso(i + 2, 50)}
                >
                  <span className="truncate text-corpo">{d.area}</span>
                  <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                    <div
                      className={`h-1 origin-left animate-crescer ${CLASSES_NIVEL[nv].cheio}`}
                      style={{ width: `${d.pct_acerto}%`, ...atraso(i + 4, 50) }}
                    />
                  </div>
                  <span className="text-right text-apoio font-semibold tabular-nums">{formatarPctBR(d.pct_acerto, 0)}%</span>
                  <span className="text-right text-apoio tabular-nums text-muted">
                    {d.acertos}/{d.total}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {temas && temas.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <h2 className="text-bloco">Temas para revisar</h2>
            <p className="text-apoio text-muted">
              Com erro ou em branco {nesta}: os de mais erros primeiro e, no empate,
              os que mais caem no Revalida e no ENAMED.
            </p>
          </div>
          <div className="rounded-caso border border-line bg-surface">
            {(todosTemas ? temas : temas.slice(0, TEMAS_VISIVEIS)).map((t) => {
              const quantidade = Math.min(10, t.questoes_banco);
              return (
                <div
                  key={t.subtopico_id}
                  className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
                >
                  <div className="min-w-0">
                    <div className="truncate text-corpo font-semibold">{t.tema}</div>
                    <div className="truncate text-apoio text-muted">
                      {t.especialidade} · acertou {t.acertos} de {t.total}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      navigate("/praticar", {
                        state: {
                          areaId: t.area_id,
                          especialidadeId: t.especialidade_id,
                          subtopicoId: t.subtopico_id,
                          iniciarImediato: true,
                          quantidade,
                        },
                      })
                    }
                    className="group flex items-center gap-1 whitespace-nowrap text-apoio font-semibold text-ink underline-offset-2 hover:underline"
                  >
                    Praticar {quantidade}
                    <ArrowRight
                      size={14}
                      strokeWidth={2}
                      className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5"
                    />
                  </button>
                </div>
              );
            })}
          </div>
          {!todosTemas && temas.length > TEMAS_VISIVEIS && (
            <button type="button" onClick={() => setTodosTemas(true)} className={`self-start ${BOTAO_SECUNDARIO}`}>
              Mostrar os {temas.length} temas
            </button>
          )}
        </div>
      )}

      <div className="flex flex-col gap-3">
        <h2 className="text-bloco">Revisão completa</h2>
        <div className="flex flex-col gap-2">
          {itens.map((item) => {
            const aberto = abertos.has(item.item_id);
            const naoRespondida = item.resposta_dada === null;
            const acertou = item.correta === 1;
            // Na prova oficial, o número do caderno facilita conferir com o gabarito do INEP.
            const numero = nomeProva && item.numero_prova ? item.numero_prova : item.ordem + 1;

            return (
              <div
                key={item.item_id}
                className={`rounded-card border bg-surface transition-colors duration-hover ${aberto ? "border-muted" : "border-line"}`}
              >
                <button
                  type="button"
                  onClick={() => alternar(item.item_id)}
                  aria-expanded={aberto}
                  className={`grid w-full items-center gap-3 px-4 py-3 text-left transition-colors duration-hover hover:bg-ground ${
                    comTempo ? "grid-cols-[92px_auto_minmax(0,1fr)_auto_auto]" : "grid-cols-[92px_auto_minmax(0,1fr)_auto]"
                  } ${aberto ? "rounded-t-card" : "rounded-card"}`}
                >
                  {naoRespondida ? (
                    <span className="rotulo rounded-etq border border-line px-2 py-1 text-center text-[12px] text-muted">Em branco</span>
                  ) : acertou ? (
                    <span className="rotulo rounded-etq bg-t4 px-2 py-1 text-center text-[12px] text-t4-on">Correta</span>
                  ) : (
                    <span className="rotulo rounded-etq bg-t1 px-2 py-1 text-center text-[12px] text-t1-on">Errada</span>
                  )}
                  <span className="text-[14px] font-semibold tabular-nums">Questão {numero}</span>
                  <span className="truncate text-corpo text-ink-2">{item.enunciado}</span>
                  {comTempo && (
                    // Negrito em --ink onde passou do ritmo: é onde a prova custou mais tempo.
                    <span
                      className={`text-apoio tabular-nums ${(item.tempo_ms ?? 0) > ritmoMs ? "font-semibold text-ink" : "text-muted"}`}
                    >
                      <span className="sr-only">Tempo na questão: </span>
                      {/* Traço: o aluno nem abriu a questão. */}
                      {item.tempo_ms === null ? "—" : formatarMMSS(item.tempo_ms)}
                    </span>
                  )}
                  <ChevronDown
                    size={16}
                    strokeWidth={2}
                    className={`shrink-0 text-muted transition-transform duration-desliza ease-suave ${aberto ? "rotate-180" : ""}`}
                  />
                </button>
                {aberto && (
                  <div className="flex animate-entrar flex-col gap-5 border-t border-line-soft p-5 md:px-11 md:py-7">
                    {/* Mesmo recuo lateral do cartão do caso: a linha fica no mesmo comprimento. */}
                    <p className="leitura-enunciado text-ink">{item.enunciado}</p>
                    {item.tem_imagem && (
                      <ImagemQuestao questaoId={item.id} alt="Imagem da questão" />
                    )}
                    <div className="flex flex-col gap-2">
                      {Object.keys(item.alternativas).map((letra) => {
                        let estado: EstadoAlternativa = "neutra";
                        if (item.resposta_correta && letra === item.resposta_correta) estado = "correta";
                        else if (letra === item.resposta_dada) estado = "errada";
                        return (
                          <AlternativaLinha key={letra} letra={letra} texto={item.alternativas[letra]} estado={estado} disabled />
                        );
                      })}
                    </div>
                    {item.explicacao && (
                      <div className="flex flex-col gap-2 border-t border-line-soft pt-5">
                        <span className="rotulo text-muted">Comentário</span>
                        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                          <TemaDoCaso tema={item.subtopico} />
                          <div className="flex flex-wrap items-center gap-4">
                            <CriarCartao
                              questaoId={item.id}
                              respostaCorreta={
                                item.resposta_correta ? item.alternativas[item.resposta_correta] : undefined
                              }
                            />
                            <RelatarErro questaoId={item.id} />
                          </div>
                        </div>
                        <TextoDiscussao texto={item.explicacao} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <button type="button" onClick={onNovoSimulado} className={`group ${BOTAO_PRIMARIO}`}>
          <RotateCcw
            size={16}
            strokeWidth={2}
            className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]"
          />
          Novo simulado
        </button>
      </div>
    </div>
  );
}

// A nota de corte da 1ª etapa do Revalida nesta edição (db.comparar_com_corte). Onde a
// prova era só objetiva e contada em acertos, a nota que a aluna teria tirado e a
// distância até o corte; onde a discursiva entrava na soma, ou a nota é a TRI do ENAMED,
// só o corte, sem veredito.
function LinhaCorte({ corte: c }: { corte: ComparacaoCorte }) {
  const corte = (
    <strong className="font-semibold text-ink">
      {formatarNumeroBR(c.corte)} de {c.maximo}
    </strong>
  );
  if (c.escala === "TRI") {
    return (
      <p className="text-corpo text-ink-2">
        A nota de corte da 1ª etapa nesta edição foi {corte} pontos, na escala da TRI que o INEP passou a usar, a mesma
        do ENAMED: ela pesa a dificuldade de cada questão entre todos os candidatos, e só os acertos não dizem se você
        passaria.
      </p>
    );
  }
  if (c.nota === null) {
    return (
      <p className="text-corpo text-ink-2">
        A nota de corte da 1ª etapa nesta edição foi {corte} pontos, somando a prova discursiva, que o Conduta não
        aplica. Só a objetiva não diz se você passaria.
      </p>
    );
  }
  const anuladas = c.anuladas === 1 ? "da questão anulada" : `das ${c.anuladas} questões anuladas`;
  return (
    <p className="text-corpo text-ink-2">
      A nota de corte da 1ª etapa nesta edição foi {corte}.{" "}
      {c.anuladas ? `Contando o ponto ${anuladas}, que o INEP deu a todos, a sua seria ` : "A sua seria "}
      <strong className="font-semibold text-ink">{formatarNumeroBR(c.nota)}</strong>:{" "}
      <strong className="font-semibold text-ink">{distanciaDoCorte(c.nota, c.corte)}</strong>.
    </p>
  );
}

// No resultado do bloco que fecha a prova: a prova inteira, com a última vez de
// cada bloco (db.prova_em_blocos), e o corte dela. É o momento raro em que a
// aluna termina uma prova oficial aos pedaços, e o que vai no cartão.
function ProvaCompleta({ dados: p }: { dados: ProvaEmBlocos }) {
  const nivel = nivelTriagem(p.pct_acerto);
  return (
    <section className="flex animate-entrar flex-col gap-3 rounded-caso border border-ink bg-surface p-6">
      <span className="rotulo text-muted">Prova completa, em blocos</span>
      <div className="flex flex-wrap items-center gap-3">
        <NumeroAnimado className="num-lg" valor={p.pct_acerto} formatar={(v) => `${formatarPctBR(v, 1)}%`} />
        <span className={`rotulo rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}>
          {NIVEIS[nivel - 1].nome}
        </span>
      </div>
      <p className="text-corpo text-ink-2">
        Com a última vez de cada bloco, a prova inteira fica em{" "}
        <strong className="font-semibold text-ink">
          {p.acertos} de {p.num_questoes}
        </strong>{" "}
        questões.
      </p>
      {p.corte && <LinhaCorte corte={p.corte} />}
    </section>
  );
}
