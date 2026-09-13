import { AlertTriangle, ArrowRight } from "lucide-react";
import { useState } from "react";
import { useAreas, useBancas } from "../../lib/catalogo";
import { BOTAO_PRIMARIO, CAMPO } from "../../lib/estilos";
import { formatarPctBR } from "../../lib/format";
import { criarSimulado, useDisponiveisSimulado, useHistoricoSimulados } from "../../lib/simulados";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";

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
    <div className="mx-auto flex max-w-[840px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Nova prova</span>
        <h1 className="text-titulo">Simulado</h1>
        <p className="max-w-[60ch] text-corpo text-ink-2">
          Uma prova no formato das provas de residência: tempo limite e correção só no final.
        </p>
      </div>

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
                className={`h-10 min-w-[56px] rounded-btn border px-4 text-[15px] font-semibold tabular-nums transition duration-hover ease-brand ${
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
                className={`${CAMPO} !w-24 tabular-nums`}
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
          <div className="flex items-start gap-2.5 rounded-card bg-t2-soft px-4 py-3 text-apoio text-ink">
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
            className={BOTAO_PRIMARIO}
          >
            Iniciar simulado de {numQuestoes} questões
            <ArrowRight size={18} strokeWidth={2} />
          </button>
        </div>
      </div>

      {historico && historico.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-bloco">Simulados anteriores</h2>
          <div className="rounded-caso border border-line bg-surface">
            {historico.map((h) => {
              const pct = h.pct_acerto;
              const nivel = pct !== null ? nivelTriagem(pct) : null;
              return (
                <div
                  key={h.id}
                  className="grid grid-cols-[minmax(0,1fr)_auto_96px] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
                >
                  <div className="min-w-0">
                    <div className="truncate text-corpo">
                      {h.area ?? "Todas as áreas"}
                      {h.banca ? ` · ${h.banca}` : ""}
                    </div>
                    <div className="text-apoio text-muted">
                      {new Date(h.iniciado_em).toLocaleDateString("pt-BR")} · {h.num_questoes} questões
                    </div>
                  </div>
                  <span className="text-apoio font-semibold tabular-nums">
                    {h.acertos ?? 0}/{h.num_questoes}
                  </span>
                  {nivel !== null && pct !== null ? (
                    <span
                      title={NIVEIS[nivel - 1].nome}
                      className={`rounded-etq px-2 py-1 text-center text-[13px] font-bold tabular-nums ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
                    >
                      {formatarPctBR(pct, 0)}%
                    </span>
                  ) : (
                    <span className="text-center text-apoio text-muted">—</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
