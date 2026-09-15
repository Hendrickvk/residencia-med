import { AlertTriangle, ArrowRight } from "lucide-react";
import { useState } from "react";
import { Dialog } from "../../components/Dialog";
import { EtiquetaPct } from "../../components/EtiquetaPct";
import { useAreas, useBancas } from "../../lib/catalogo";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO, PRESSAO } from "../../lib/estilos";
import { formatarDuracaoMin } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import {
  criarSimulado,
  criarSimuladoOficial,
  nomeEdicao,
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
  if (h.edicao && h.banca) return nomeEdicao(h.banca, h.edicao);
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
          <ProvasOficiais edicoes={edicoes} historico={historico} onIniciado={onIniciado} />
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
  const nome =
    simulado.edicao && simulado.banca ? nomeEdicao(simulado.banca, simulado.edicao) : `Simulado de ${simulado.num_questoes} questões`;

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

function ProvasOficiais({
  edicoes,
  historico,
  onIniciado,
}: {
  edicoes: EdicaoOficial[] | undefined;
  historico: HistoricoSimulado[] | undefined;
  onIniciado: (id: number) => void;
}) {
  const [escolhida, setEscolhida] = useState<EdicaoOficial | null>(null);
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function comecar() {
    if (!escolhida) return;
    setErro(null);
    setCriando(true);
    try {
      const r = await criarSimuladoOficial(escolhida.banca, escolhida.edicao);
      onIniciado(r.id);
    } catch {
      setErro("Não foi possível começar a prova. Tente de novo.");
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

  return (
    <div className="flex flex-col gap-3">
      <p className="max-w-[64ch] text-corpo text-ink-2">
        O caderno inteiro, na ordem original e com 3 minutos por questão, o ritmo da prova do INEP. As questões anuladas
        pelo INEP ficam de fora.
      </p>
      <div className="rounded-caso border border-line bg-surface">
        {edicoes.map((e, i) => {
          const ultima = historico?.find((h) => h.banca === e.banca && h.edicao === e.edicao);
          return (
            <div
              key={`${e.banca}-${e.edicao}`}
              className="grid animate-desvanecer grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border-b border-line-soft px-5 py-4 transition-colors duration-hover last:border-0 hover:bg-ground sm:grid-cols-[minmax(0,1fr)_auto_auto]"
              style={atraso(i, 30)}
            >
              <div className="min-w-0">
                <div className="text-[16px] font-semibold">{nomeEdicao(e.banca, e.edicao)}</div>
                <div className="text-apoio tabular-nums text-muted">
                  {e.total} questões · {formatarDuracaoMin(e.tempo_limite_min)}
                </div>
              </div>
              <div className="hidden items-center gap-2 text-apoio text-muted sm:flex">
                {ultima?.pct_acerto != null && (
                  <>
                    última vez
                    <EtiquetaPct pct={ultima.pct_acerto} />
                  </>
                )}
              </div>
              <button type="button" onClick={() => setEscolhida(e)} className={BOTAO_SECUNDARIO}>
                Fazer esta prova
              </button>
            </div>
          );
        })}
      </div>

      <Dialog
        titulo={escolhida ? `Começar ${nomeEdicao(escolhida.banca, escolhida.edicao)}` : "Começar prova"}
        aberto={escolhida !== null}
        onFechar={() => {
          setEscolhida(null);
          setErro(null);
        }}
      >
        {escolhida && (
          <p className="text-corpo text-ink-2">
            São <strong className="text-ink">{escolhida.total} questões</strong> em{" "}
            <strong className="text-ink">{formatarDuracaoMin(escolhida.tempo_limite_min)}</strong>. O tempo começa a contar
            agora e não para se você fechar a aba: dá para continuar depois, até ele acabar.
          </p>
        )}
        {erro && (
          <div className="mt-4 flex animate-entrar items-start gap-2.5 rounded-card bg-t2-soft px-4 py-3 text-apoio text-ink">
            <AlertTriangle size={16} strokeWidth={2} className="mt-0.5 shrink-0" />
            <span>{erro}</span>
          </div>
        )}
        <div className="mt-6 flex gap-2">
          <button type="button" onClick={() => setEscolhida(null)} className={`${BOTAO_SECUNDARIO} flex-1`}>
            Agora não
          </button>
          <button type="button" onClick={comecar} disabled={criando} className={`${BOTAO_PRIMARIO} flex-1`}>
            Começar a prova
          </button>
        </div>
      </Dialog>
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
    } catch {
      setErro("Não foi possível iniciar o simulado. Tente de novo.");
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
