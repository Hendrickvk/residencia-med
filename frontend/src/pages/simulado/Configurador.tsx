import { Play } from "lucide-react";
import { useEffect, useState } from "react";
import { useAreas, useBancas } from "../../lib/catalogo";
import { formatarPctBR } from "../../lib/format";
import { criarSimulado, useDisponiveisSimulado, useHistoricoSimulados } from "../../lib/simulados";

interface Props {
  onIniciado: (id: number) => void;
}

const PRESETS = [10, 20, 30, 50] as const;

export default function Configurador({ onIniciado }: Props) {
  const { data: areas } = useAreas();
  const { data: bancas } = useBancas();
  const { data: historico } = useHistoricoSimulados();

  const [areaId, setAreaId] = useState<number | undefined>(undefined);
  const [banca, setBanca] = useState<string | undefined>(undefined);
  const [preset, setPreset] = useState<number | "personalizado">(20);
  const [numCustom, setNumCustom] = useState(15);
  const [tempoLimite, setTempoLimite] = useState(30);
  const [tempoEditado, setTempoEditado] = useState(false);
  const [criando, setCriando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const numQuestoes = preset === "personalizado" ? numCustom : preset;
  const { data: disponiveisData } = useDisponiveisSimulado(areaId, banca);
  const disponiveis = disponiveisData?.total ?? null;

  useEffect(() => {
    if (!tempoEditado) setTempoLimite(Math.max(5, Math.round(numQuestoes * 1.5)));
  }, [numQuestoes, tempoEditado]);

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
    <div className="rounded-panel border border-line bg-surface p-6">
      <h1 className="mb-1 text-h1 text-ink-700">Simulado</h1>
      <p className="mb-5 text-corpo text-ink-500">
        Monte uma prova no formato das provas de residência: número de questões, tempo limite e sem correção até o
        final.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-apoio text-ink-500">
          Área (opcional)
          <select
            className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
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

        <label className="flex flex-col gap-1 text-apoio text-ink-500">
          Banca (opcional)
          <select
            className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft disabled:text-ink-300"
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

        <label className="flex flex-col gap-1 text-apoio text-ink-500">
          Número de questões
          <select
            className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
            value={preset}
            onChange={(e) => setPreset(e.target.value === "personalizado" ? "personalizado" : Number(e.target.value))}
          >
            {PRESETS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
            <option value="personalizado">Personalizado</option>
          </select>
        </label>

        {preset === "personalizado" && (
          <label className="flex flex-col gap-1 text-apoio text-ink-500">
            Quantas questões?
            <input
              type="number"
              min={1}
              max={200}
              value={numCustom}
              onChange={(e) => setNumCustom(Number(e.target.value))}
              className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
            />
          </label>
        )}

        <label className="flex flex-col gap-1 text-apoio text-ink-500">
          Tempo limite (minutos)
          <input
            type="number"
            min={1}
            max={600}
            value={tempoLimite}
            onChange={(e) => {
              setTempoEditado(true);
              setTempoLimite(Number(e.target.value));
            }}
            className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
          />
        </label>
      </div>

      {semQuestoesSuficientes && (
        <p className="mt-4 text-apoio text-warn">
          Só há {disponiveis} questão(ões) disponível(is) para esse filtro (pediu {numQuestoes}). Ajuste os filtros
          ou a quantidade.
        </p>
      )}
      {erro && <p className="mt-4 text-apoio text-wrong">{erro}</p>}

      <button
        type="button"
        onClick={iniciar}
        disabled={criando || disponiveis === 0 || semQuestoesSuficientes}
        className="mt-5 flex h-10 items-center gap-2 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-line disabled:text-ink-300"
      >
        <Play size={16} strokeWidth={1.5} />
        Iniciar simulado
      </button>

      {historico && historico.length > 0 && (
        <div className="mt-8 border-t border-line pt-5">
          <div className="mb-3 text-apoio font-medium text-ink-500">Histórico de simulados</div>
          <div className="space-y-1.5">
            {historico.map((h) => (
              <div key={h.id} className="flex items-center justify-between rounded-btn border border-line px-3 py-2 text-apoio">
                <span className="text-ink-700">{h.area ?? "Todas as áreas"}</span>
                <span className="font-mono tabular-nums text-ink-500">
                  {h.acertos}/{h.num_questoes} · {h.pct_acerto !== null ? `${formatarPctBR(h.pct_acerto)}%` : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
