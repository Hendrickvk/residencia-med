import { AlertTriangle, ArrowRight } from "lucide-react";
import { useState } from "react";
import { ApiError } from "../../lib/api";
import { Dialog } from "../../components/Dialog";
import { EtiquetaPct } from "../../components/EtiquetaPct";
import { useAreas, useBancas } from "../../lib/catalogo";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO, PRESSAO } from "../../lib/estilos";
import { formatarDuracaoMin } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import {
  BANCAS_OFICIAIS,
  criarSimulado,
  criarSimuladoOficial,
  nomeEdicao,
  nomeProvaOficial,
  useDisponiveisSimulado,
  useEdicoesOficiais,
  useHistoricoSimulados,
  useSimuladoEmAndamento,
} from "../../lib/simulados";
import type { EdicaoOficial, HistoricoSimulado, SimuladoEmAndamento } from "../../lib/types";

interface Props {
  onIniciado: (id: number) => void;
}

type Modo = "oficial" | "montar";

const PRESETS = [10, 20, 30, 50] as const;

const MODOS = [
  ["oficial", "Prova oficial"],
  ["montar", "Montar simulado"],
] as const;

function rotuloHistorico(h: HistoricoSimulado): string {
  const prova = nomeProvaOficial(h);
  if (prova) return prova;
  return [h.area ?? "Todas as áreas", h.banca].filter(Boolean).join(" · ");
}

export default function Configurador({ onIniciado }: Props) {
  const { data: historico } = useHistoricoSimulados();
  const { data: edicoes } = useEdicoesOficiais();
  const { data: emAndamento } = useSimuladoEmAndamento();
  const [modo, setModo] = useState<Modo>("oficial");
  // Só a troca de aba anima o conteúdo; na chegada à tela quem anima é o AppShell.
  const [trocouModo, setTrocouModo] = useState(false);

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Nova prova</span>
        <h1 className="text-titulo">Simulado</h1>
        <p className="max-w-[60ch] text-corpo text-ink-2">
          Refaça uma prova oficial inteira ou monte um simulado com os filtros que quiser. Nos dois casos há tempo limite
          e a correção só aparece no final.
        </p>
      </div>

      {emAndamento && <ProvaEmAndamento simulado={emAndamento} onContinuar={() => onIniciado(emAndamento.id)} />}

      {/* Colunas iguais para o fundo da aba ativa deslizar exatamente uma
          coluna (100% da própria largura + o gap de 4px). */}
      <div
        role="tablist"
        aria-label="Tipo de simulado"
        className="relative grid grid-cols-2 gap-1 self-start rounded-btn border border-line bg-surface p-1"
      >
        <span
          aria-hidden="true"
          className="absolute inset-y-1 left-1 w-[calc(50%-6px)] rounded-col bg-ink transition-transform duration-desliza ease-suave"
          style={{ transform: modo === "montar" ? "translateX(calc(100% + 4px))" : "none" }}
        />
        {MODOS.map(([m, rotulo]) => (
          <button
            key={m}
            type="button"
            role="tab"
            aria-selected={modo === m}
            onClick={() => {
              if (m === modo) return;
              setModo(m);
              setTrocouModo(true);
            }}
            className={`relative h-9 whitespace-nowrap rounded-col px-4 text-[14.5px] font-semibold transition-colors duration-toggle ${
              modo === m ? "text-onink" : "text-ink-2 hover:text-ink"
            }`}
          >
            {rotulo}
          </button>
        ))}
      </div>

      <div key={modo} className={trocouModo ? "animate-entrar" : ""}>
        {modo === "oficial" ? (
          <ProvasOficiais edicoes={edicoes} onIniciado={onIniciado} />
        ) : (
          <MontarSimulado onIniciado={onIniciado} />
        )}
      </div>

      {historico && historico.length > 0 && (
        <div className="flex animate-desvanecer flex-col gap-3">
          <h2 className="text-bloco">Simulados anteriores</h2>
          <div className="rounded-caso border border-line bg-surface">
            {historico.map((h) => (
              <div
                key={h.id}
                className="grid grid-cols-[minmax(0,1fr)_auto_96px] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
              >
                <div className="min-w-0">
                  <div className="truncate text-corpo">{rotuloHistorico(h)}</div>
                  <div className="text-apoio text-muted">
                    {new Date(h.iniciado_em).toLocaleDateString("pt-BR")} · {h.num_questoes} questões
                  </div>
                </div>
                <span className="text-apoio font-semibold tabular-nums">
                  {h.acertos ?? 0}/{h.num_questoes}
                </span>
                {h.pct_acerto !== null ? (
                  <EtiquetaPct pct={h.pct_acerto} />
                ) : (
                  <span className="text-center text-apoio text-muted">—</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ProvaEmAndamento({ simulado, onContinuar }: { simulado: SimuladoEmAndamento; onContinuar: () => void }) {
  // Momento do render inicial: o cartão só precisa de "faltam cerca de X".
  const [agora] = useState(() => Date.now());
  const fim = new Date(simulado.iniciado_em).getTime() + simulado.tempo_limite_min * 60_000;
  const restanteMin = Math.max(0, Math.floor((fim - agora) / 60_000));
  const nome = nomeProvaOficial(simulado) ?? `Simulado de ${simulado.num_questoes} questões`;

  return (
    <div className="flex animate-entrar flex-wrap items-center justify-between gap-4 rounded-caso border border-ink bg-surface px-6 py-5">
      <div className="flex min-w-0 flex-col gap-1">
        <span className="rotulo text-muted">Prova em andamento</span>
        <span className="text-bloco font-semibold">{nome}</span>
        <span className="text-apoio tabular-nums text-muted">
          {simulado.respondidas} de {simulado.num_questoes} respondidas · faltam {formatarDuracaoMin(restanteMin)}
        </span>
      </div>
      <button type="button" onClick={onContinuar} className={`group ${BOTAO_PRIMARIO}`}>
        Continuar prova
        <ArrowRight size={18} strokeWidth={2} className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5" />
      </button>
    </div>
  );
}

// As edições agrupadas por banca, na ordem de BANCAS_OFICIAIS; dentro de cada
// uma, a ordem do servidor (mais recentes primeiro). Eram 13 linhas iguais numa
// lista só, e o que distingue uma prova da outra é a banca antes do ano.
function agruparPorBanca(edicoes: EdicaoOficial[]) {
  const posicao = (banca: string) => {
    const i = BANCAS_OFICIAIS.findIndex((b) => b.banca === banca);
    return i === -1 ? BANCAS_OFICIAIS.length : i;
  };
  const grupos = new Map<string, EdicaoOficial[]>();
  for (const e of edicoes) grupos.set(e.banca, [...(grupos.get(e.banca) ?? []), e]);
  return [...grupos]
    .sort(([a], [b]) => posicao(a) - posicao(b) || a.localeCompare(b))
    .map(([banca, lista]) => {
      const info = BANCAS_OFICIAIS.find((b) => b.banca === banca);
      return { banca, nome: info?.nome ?? banca, orgao: info?.orgao, edicoes: lista };
    });
}

function ProvasOficiais({
  edicoes,
  onIniciado,
}: {
  edicoes: EdicaoOficial[] | undefined;
  onIniciado: (id: number) => void;
}) {
  const [escolhida, setEscolhida] = useState<EdicaoOficial | null>(null);
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Sem `bloco`, a prova inteira.
  async function comecar(bloco?: number) {
    if (!escolhida) return;
    setErro(null);
    setCriando(true);
    try {
      const r = await criarSimuladoOficial(escolhida.banca, escolhida.edicao, bloco);
      onIniciado(r.id);
    } catch (e) {
      // 403 = e-mail ainda não confirmado. Aqui "tente de novo" seria mentira:
      // a resposta só muda quando ela confirmar, e quem explica isso é a frase
      // do servidor, com a faixa do topo logo acima.
      setErro(
        e instanceof ApiError && e.status === 403
          ? e.message
          : "Não foi possível começar a prova. Tente de novo.",
      );
      setCriando(false);
    }
  }

  // Mesma queryKey do componente pai (cache compartilhado): aqui só para saber
  // se a lista falhou, em vez de deixar o esqueleto de carregamento para sempre.
  const { isError, refetch } = useEdicoesOficiais();

  if (!edicoes && isError) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-caso border border-line bg-surface px-6 py-5">
        <span className="text-corpo text-ink-2">Não foi possível carregar as provas oficiais.</span>
        <button type="button" onClick={() => refetch()} className={BOTAO_SECUNDARIO}>
          Tentar de novo
        </button>
      </div>
    );
  }

  if (!edicoes) {
    return <div className="h-[280px] animate-pulse rounded-caso bg-line-soft" />;
  }

  if (edicoes.length === 0) {
    return (
      <p className="rounded-caso border border-line bg-surface px-6 py-5 text-corpo text-ink-2">
        Nenhuma prova oficial completa no banco ainda. Use “Montar simulado”.
      </p>
    );
  }

  const grupos = agruparPorBanca(edicoes);

  return (
    <div className="flex flex-col gap-7">
      <p className="max-w-[64ch] text-corpo text-ink-2">
        O caderno na ordem original, com 3 minutos por questão, o ritmo das provas oficiais. Faça de uma vez ou em blocos
        de até 25 questões. As questões anuladas pela banca ficam de fora.
      </p>
      {grupos.map((g, gi) => {
        // Posição na cascata de entrada, contínua de uma banca para a outra.
        const inicio = grupos.slice(0, gi).reduce((soma, anterior) => soma + anterior.edicoes.length, 0);
        return (
          <section key={g.banca} className="flex flex-col gap-3">
            <h2 className="flex animate-desvanecer items-baseline gap-2 text-bloco" style={atraso(inicio, 30)}>
              {g.nome}
              {g.orgao && <span className="text-apoio font-normal text-muted">{g.orgao}</span>}
            </h2>
            <div className="rounded-caso border border-line bg-surface">
              {g.edicoes.map((e, i) => (
                <LinhaEdicao key={e.edicao} edicao={e} indice={inicio + i} onFazer={() => setEscolhida(e)} />
              ))}
            </div>
          </section>
        );
      })}

      <Dialog
        titulo={escolhida ? nomeEdicao(escolhida.banca, escolhida.edicao) : "Prova oficial"}
        aberto={escolhida !== null}
        onFechar={() => {
          setEscolhida(null);
          setErro(null);
        }}
      >
        {escolhida && <EscolhaDaProva edicao={escolhida} criando={criando} onComecar={comecar} />}
        {erro && (
          <div className="mt-4 flex animate-entrar items-start gap-2.5 rounded-card bg-t2-soft px-4 py-3 text-apoio text-ink">
            <AlertTriangle size={16} strokeWidth={2} className="mt-0.5 shrink-0" />
            <span>{erro}</span>
          </div>
        )}
        <button
          type="button"
          data-autofocus
          onClick={() => setEscolhida(null)}
          className={`${BOTAO_SECUNDARIO} mt-6 w-full`}
        >
          Agora não
        </button>
      </Dialog>
    </div>
  );
}

// Uma edição na lista: o que ela é e o que a aluna já fez nela — a nota da
// última prova inteira e, dos blocos, a nota somada quando todos estão feitos
// ou quantos já foram.
function LinhaEdicao({ edicao: e, indice, onFazer }: { edicao: EdicaoOficial; indice: number; onFazer: () => void }) {
  const blocosFeitos = e.blocos.filter((b) => b.ultima_pct !== null).length;
  return (
    <div
      className="grid animate-desvanecer grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border-b border-line-soft px-5 py-4 transition-colors duration-hover last:border-0 hover:bg-ground"
      style={atraso(indice, 30)}
    >
      <div className="min-w-0">
        <div className="text-[16px] font-semibold tabular-nums">{e.edicao}</div>
        <div className="text-apoio tabular-nums text-muted">
          {e.total} questões · {formatarDuracaoMin(e.tempo_limite_min)}
        </div>
        {(e.ultima_pct !== null || blocosFeitos > 0) && (
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-apoio text-muted">
            {e.ultima_pct !== null && (
              <span className="flex items-center gap-2">
                prova inteira
                <EtiquetaPct pct={e.ultima_pct} />
              </span>
            )}
            {e.pct_blocos !== null ? (
              <span className="flex items-center gap-2">
                em blocos
                <EtiquetaPct pct={e.pct_blocos} />
              </span>
            ) : (
              blocosFeitos > 0 && (
                <span className="tabular-nums">
                  {blocosFeitos} de {e.blocos.length} blocos
                </span>
              )
            )}
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={onFazer}
        aria-label={`Fazer esta prova: ${nomeEdicao(e.banca, e.edicao)}`}
        className={BOTAO_SECUNDARIO}
      >
        Fazer esta prova
      </button>
    </div>
  );
}

// O diálogo antes de começar: o tempo não para depois do clique, então a
// escolha entre a prova inteira e um bloco é também a confirmação.
function EscolhaDaProva({
  edicao: e,
  criando,
  onComecar,
}: {
  edicao: EdicaoOficial;
  criando: boolean;
  onComecar: (bloco?: number) => void;
}) {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-corpo text-ink-2">
        O tempo começa a contar quando você começa e não para se você fechar a aba: dá para continuar depois, até ele
        acabar.
      </p>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <span className="text-corpo font-semibold">Prova inteira</span>
          <span className="text-apoio tabular-nums text-muted">
            {e.total} questões · {formatarDuracaoMin(e.tempo_limite_min)}
          </span>
        </div>
        <button type="button" disabled={criando} onClick={() => onComecar()} className={BOTAO_PRIMARIO}>
          Começar a prova inteira
        </button>
      </div>
      {e.blocos.length > 1 && (
        <div className="flex flex-col gap-1 border-t border-line-soft pt-5">
          <span className="text-corpo font-semibold">Em blocos</span>
          <p className="text-apoio text-muted">Partes seguidas do caderno, no mesmo ritmo, com o resultado ao fim de cada uma.</p>
          <ul className="mt-2 flex flex-col divide-y divide-line-soft">
            {e.blocos.map((b) => (
              <li key={b.bloco} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <div className="text-corpo">Bloco {b.bloco}</div>
                  <div className="text-apoio tabular-nums text-muted">
                    {b.total} questões · {formatarDuracaoMin(b.tempo_limite_min)}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {b.ultima_pct !== null && <EtiquetaPct pct={b.ultima_pct} />}
                  <button
                    type="button"
                    disabled={criando}
                    onClick={() => onComecar(b.bloco)}
                    aria-label={`${b.ultima_pct !== null ? "Refazer" : "Começar"} o bloco ${b.bloco}`}
                    className={`${BOTAO_SECUNDARIO} !h-9 !px-3.5 !text-[14.5px]`}
                  >
                    {b.ultima_pct !== null ? "Refazer" : "Começar"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MontarSimulado({ onIniciado }: { onIniciado: (id: number) => void }) {
  const { data: areas } = useAreas();
  const { data: bancas } = useBancas();

  const [areaId, setAreaId] = useState<number | undefined>(undefined);
  const [banca, setBanca] = useState<string | undefined>(undefined);
  const [preset, setPreset] = useState<number | "personalizado">(20);
  const [numCustom, setNumCustom] = useState(15);
  // null = tempo sugerido automaticamente pela quantidade; vira número assim
  // que o aluno edita o campo.
  const [tempoManual, setTempoManual] = useState<number | null>(null);
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const numQuestoes = preset === "personalizado" ? numCustom : preset;
  const tempoLimite = tempoManual ?? Math.max(5, Math.round(numQuestoes * 1.5));
  const { data: disponiveisData } = useDisponiveisSimulado(areaId, banca);
  const disponiveis = disponiveisData?.total ?? null;

  async function iniciar() {
    setErro(null);
    setCriando(true);
    try {
      const r = await criarSimulado({ area_id: areaId, banca, num_questoes: numQuestoes, tempo_limite_min: tempoLimite });
      onIniciado(r.id);
    } catch (e) {
      setErro(
        e instanceof ApiError && e.status === 403
          ? e.message
          : "Não foi possível iniciar o simulado. Tente de novo.",
      );
    } finally {
      setCriando(false);
    }
  }

  const semQuestoesSuficientes = disponiveis !== null && disponiveis < numQuestoes;

  return (
    <div className="flex flex-col gap-7 rounded-caso border border-line bg-surface p-6 md:p-8">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <label htmlFor="simulado-area" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Área</span>
          <select
            id="simulado-area"
            className={CAMPO}
            value={areaId ?? ""}
            onChange={(e) => setAreaId(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Todas</option>
            {areas?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.nome}
              </option>
            ))}
          </select>
        </label>

        <label htmlFor="simulado-banca" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Banca</span>
          <select
            id="simulado-banca"
            className={CAMPO}
            value={banca ?? ""}
            disabled={!bancas?.length}
            onChange={(e) => setBanca(e.target.value || undefined)}
          >
            <option value="">Todas</option>
            {bancas?.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Número de questões</span>
        <div className="flex flex-wrap items-center gap-2">
          {[...PRESETS, "personalizado" as const].map((p) => (
            <button
              key={p}
              type="button"
              aria-pressed={preset === p}
              onClick={() => setPreset(p)}
              className={`h-10 min-w-[56px] rounded-btn border px-4 text-[15px] font-semibold tabular-nums transition duration-hover ease-brand ${PRESSAO} ${
                preset === p ? "border-ink bg-ink text-onink" : "border-line bg-surface text-ink-2 hover:border-muted"
              }`}
            >
              {p === "personalizado" ? "Outro" : p}
            </button>
          ))}
          {preset === "personalizado" && (
            <input
              id="simulado-num-custom"
              type="number"
              min={1}
              max={200}
              value={numCustom}
              aria-label="Quantas questões"
              onChange={(e) => setNumCustom(Number(e.target.value))}
              className={`${CAMPO} !w-24 animate-surgir tabular-nums`}
            />
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="simulado-tempo" className="rotulo text-muted">
          Tempo limite
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <input
            id="simulado-tempo"
            type="number"
            min={1}
            max={600}
            value={tempoLimite}
            onChange={(e) => setTempoManual(Number(e.target.value))}
            className={`${CAMPO} !w-24 tabular-nums`}
          />
          <span className="text-corpo text-ink-2">minutos</span>
          {tempoManual === null && <span className="text-apoio text-muted">sugestão de 1,5 min por questão</span>}
        </div>
      </div>

      {(semQuestoesSuficientes || erro) && (
        <div className="flex animate-entrar items-start gap-2.5 rounded-card bg-t2-soft px-4 py-3 text-apoio text-ink">
          <AlertTriangle size={16} strokeWidth={2} className="mt-0.5 shrink-0" />
          <span>
            {erro ??
              `Só há ${disponiveis} questão(ões) para esse filtro, e você pediu ${numQuestoes}. Ajuste os filtros ou a quantidade.`}
          </span>
        </div>
      )}

      <div className="flex justify-end border-t border-line-soft pt-6">
        <button
          type="button"
          onClick={iniciar}
          disabled={criando || disponiveis === 0 || semQuestoesSuficientes}
          className={`group ${BOTAO_PRIMARIO}`}
        >
          Iniciar simulado de {numQuestoes} questões
          <ArrowRight
            size={18}
            strokeWidth={2}
            className="transition-transform duration-toggle ease-suave group-enabled:group-hover:translate-x-0.5"
          />
        </button>
      </div>
    </div>
  );
}
