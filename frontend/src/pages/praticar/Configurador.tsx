import { Play, X } from "lucide-react";
import { useState } from "react";
import { useAreas, useAnos, useBancas, useSubtopicos } from "../../lib/catalogo";
import type { FiltrosPratica } from "../../lib/types";

interface Props {
  onIniciar: (filtros: FiltrosPratica) => void;
  areaInicial?: number;
}

const QUANTIDADES = [10, 20, 30, 50];

const campoClasse =
  "h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft disabled:cursor-not-allowed disabled:text-ink-300";
const rotuloClasse = "flex flex-col gap-1 text-apoio text-ink-500";

export default function Configurador({ onIniciar, areaInicial }: Props) {
  const [areaId, setAreaId] = useState<number | undefined>(areaInicial);
  const [subtopicoId, setSubtopicoId] = useState<number | undefined>(undefined);
  const [banca, setBanca] = useState<string | undefined>(undefined);
  const [ano, setAno] = useState<number | undefined>(undefined);
  const [quantidade, setQuantidade] = useState(20);
  const [apenasErros, setApenasErros] = useState(false);
  const [excluirRespondidas, setExcluirRespondidas] = useState(false);

  const { data: areas } = useAreas();
  const { data: subtopicos } = useSubtopicos(areaId);
  const { data: bancas } = useBancas();
  const { data: anos } = useAnos();

  const nomeArea = areas?.find((a) => a.id === areaId)?.nome;
  const nomeSubtopico = subtopicos?.find((s) => s.id === subtopicoId)?.nome;

  const chips: { label: string; onRemover: () => void }[] = [];
  if (nomeArea) chips.push({ label: nomeArea, onRemover: () => setAreaId(undefined) });
  if (nomeSubtopico) chips.push({ label: nomeSubtopico, onRemover: () => setSubtopicoId(undefined) });
  if (banca) chips.push({ label: banca, onRemover: () => setBanca(undefined) });
  if (ano) chips.push({ label: String(ano), onRemover: () => setAno(undefined) });
  if (apenasErros) chips.push({ label: "Apenas erros", onRemover: () => setApenasErros(false) });
  if (excluirRespondidas) chips.push({ label: "Excluir respondidas", onRemover: () => setExcluirRespondidas(false) });

  return (
    <div className="rounded-panel border border-line bg-surface p-6">
      <h1 className="mb-5 text-h1 text-ink-700">Praticar</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className={rotuloClasse}>
          Área (opcional)
          <select
            className={campoClasse}
            value={areaId ?? ""}
            onChange={(e) => {
              setAreaId(e.target.value ? Number(e.target.value) : undefined);
              setSubtopicoId(undefined);
            }}
          >
            <option value="">Todas</option>
            {areas?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.nome}
              </option>
            ))}
          </select>
        </label>

        <label className={rotuloClasse}>
          Assunto (opcional)
          <select
            className={campoClasse}
            value={subtopicoId ?? ""}
            disabled={!areaId}
            onChange={(e) => setSubtopicoId(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Todos</option>
            {subtopicos?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nome}
              </option>
            ))}
          </select>
        </label>

        <label className={rotuloClasse}>
          Banca (opcional)
          <select
            className={campoClasse}
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

        <label className={rotuloClasse}>
          Ano (opcional)
          <select
            className={campoClasse}
            value={ano ?? ""}
            disabled={!anos?.length}
            onChange={(e) => setAno(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Todos</option>
            {anos?.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>

        <label className={rotuloClasse}>
          Quantidade de questões
          <select className={campoClasse} value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))}>
            {QUANTIDADES.map((q) => (
              <option key={q} value={q}>
                {q}
              </option>
            ))}
          </select>
        </label>

        <div className="flex flex-col justify-center gap-2 pt-4 sm:pt-0">
          <label className="flex items-center gap-2 text-corpo text-ink-700">
            <input type="checkbox" checked={apenasErros} onChange={(e) => setApenasErros(e.target.checked)} />
            Apenas questões que errei
          </label>
          <label className="flex items-center gap-2 text-corpo text-ink-700">
            <input
              type="checkbox"
              checked={excluirRespondidas}
              onChange={(e) => setExcluirRespondidas(e.target.checked)}
            />
            Excluir questões já respondidas
          </label>
        </div>
      </div>

      {chips.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {chips.map((chip) => (
            <button
              key={chip.label}
              type="button"
              onClick={chip.onRemover}
              className="flex items-center gap-1 rounded-pill bg-action-soft px-2.5 py-1 text-apoio text-action"
            >
              {chip.label}
              <X size={12} strokeWidth={2} />
            </button>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={() =>
          onIniciar({
            area_id: areaId,
            subtopico_id: subtopicoId,
            banca,
            ano,
            apenas_erros: apenasErros,
            excluir_respondidas: excluirRespondidas,
            quantidade,
          })
        }
        className="mt-6 flex h-10 items-center gap-2 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        <Play size={16} strokeWidth={1.5} />
        Iniciar sessão de {quantidade} questões
      </button>
    </div>
  );
}
