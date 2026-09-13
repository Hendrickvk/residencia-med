import { ArrowRight, X } from "lucide-react";
import { useState } from "react";
import { useAreas, useAnos, useBancas, useSubtopicos } from "../../lib/catalogo";
import { BOTAO_PRIMARIO, CAMPO } from "../../lib/estilos";
import type { FiltrosPratica } from "../../lib/types";

interface Props {
  onIniciar: (filtros: FiltrosPratica) => void;
  areaInicial?: number;
}

const QUANTIDADES = [10, 20, 30, 50];

function Interruptor({
  ligado,
  onMudar,
  children,
}: {
  ligado: boolean;
  onMudar: (ligado: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={ligado}
      onClick={() => onMudar(!ligado)}
      className="flex items-center gap-3 text-left text-corpo text-ink"
    >
      <span
        className={`relative h-5 w-9 shrink-0 rounded-pill transition-colors duration-hover ease-brand ${
          ligado ? "bg-ink" : "bg-line"
        }`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-pill bg-surface shadow-[0_1px_2px_rgba(0,0,0,0.3)] transition-transform duration-hover ease-brand ${
            ligado ? "translate-x-[18px]" : "translate-x-0.5"
          }`}
        />
      </span>
      {children}
    </button>
  );
}

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
  if (excluirRespondidas) chips.push({ label: "Sem casos já respondidos", onRemover: () => setExcluirRespondidas(false) });

  return (
    <div className="mx-auto flex max-w-[840px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Nova sessão</span>
        <h1 className="text-titulo">Praticar</h1>
      </div>

      <div className="flex flex-col gap-7 rounded-caso border border-line bg-surface p-6 md:p-8">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label htmlFor="filtro-area" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Área</span>
            <select
              id="filtro-area"
              className={CAMPO}
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

          <label htmlFor="filtro-assunto" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Assunto</span>
            <select
              id="filtro-assunto"
              className={CAMPO}
              value={subtopicoId ?? ""}
              disabled={!areaId}
              onChange={(e) => setSubtopicoId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">{areaId ? "Todos" : "Escolha uma área primeiro"}</option>
              {subtopicos?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </select>
          </label>

          <label htmlFor="filtro-banca" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Banca</span>
            <select
              id="filtro-banca"
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

          <label htmlFor="filtro-ano" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Ano</span>
            <select
              id="filtro-ano"
              className={CAMPO}
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
        </div>

        <div className="flex flex-col gap-2">
          <span className="rotulo text-muted">Quantidade de casos</span>
          <div className="flex flex-wrap gap-2">
            {QUANTIDADES.map((q) => (
              <button
                key={q}
                type="button"
                aria-pressed={quantidade === q}
                onClick={() => setQuantidade(q)}
                className={`h-10 min-w-[56px] rounded-btn border px-4 text-[15px] font-semibold tabular-nums transition duration-hover ease-brand ${
                  quantidade === q ? "border-ink bg-ink text-onink" : "border-line bg-surface text-ink-2 hover:border-muted"
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <Interruptor ligado={apenasErros} onMudar={setApenasErros}>
            Apenas casos que errei
          </Interruptor>
          <Interruptor ligado={excluirRespondidas} onMudar={setExcluirRespondidas}>
            Excluir casos já respondidos
          </Interruptor>
        </div>

        {chips.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {chips.map((chip) => (
              <button
                key={chip.label}
                type="button"
                onClick={chip.onRemover}
                aria-label={`Remover filtro ${chip.label}`}
                className="flex items-center gap-1.5 rounded-etq border border-line bg-ground px-2.5 py-1 text-apoio font-medium text-ink-2 transition duration-hover hover:border-muted hover:text-ink"
              >
                {chip.label}
                <X size={13} strokeWidth={2} />
              </button>
            ))}
          </div>
        )}

        <div className="flex justify-end border-t border-line-soft pt-6">
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
            className={BOTAO_PRIMARIO}
          >
            Iniciar sessão de {quantidade} casos
            <ArrowRight size={18} strokeWidth={2} />
          </button>
        </div>
      </div>
    </div>
  );
}
