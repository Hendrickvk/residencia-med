import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ArrowRight, X } from "lucide-react";
import { useState } from "react";
import { api } from "../../lib/api";
import { useAreas, useAnos, useBancas, useEspecialidades, useTemas, useTiposPergunta } from "../../lib/catalogo";
import { BOTAO_PRIMARIO, CAMPO, PRESSAO } from "../../lib/estilos";
import type { FiltrosPratica } from "../../lib/types";

interface Props {
  onIniciar: (filtros: FiltrosPratica) => void;
  areaInicial?: number;
}

const QUANTIDADES = [10, 20, 30, 50];

// Botão de escolha única (quantidade, tipo de pergunta): o escolhido fica em tinta.
function classeSegmento(ativo: boolean) {
  return `h-10 min-w-[56px] rounded-btn border px-4 text-[15px] font-semibold transition duration-hover ease-brand ${PRESSAO} ${
    ativo ? "border-ink bg-ink text-onink" : "border-line bg-surface text-ink-2 hover:border-muted"
  }`;
}

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
      className="group flex items-center gap-3 text-left text-corpo text-ink"
    >
      <span
        className={`relative h-5 w-9 shrink-0 rounded-pill transition-colors duration-toggle ease-brand ${
          ligado ? "bg-ink" : "bg-line"
        }`}
      >
        {/* O pino alarga um pouco enquanto pressionado, como um interruptor físico. */}
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-pill bg-surface shadow-[0_1px_2px_rgba(0,0,0,0.3)] transition-[transform,width] duration-desliza ease-suave group-active:w-5 ${
            ligado ? "translate-x-[18px] group-active:translate-x-[14px]" : "translate-x-0.5"
          }`}
        />
      </span>
      {children}
    </button>
  );
}

export default function Configurador({ onIniciar, areaInicial }: Props) {
  const [areaId, setAreaId] = useState<number | undefined>(areaInicial);
  const [especialidadeId, setEspecialidadeId] = useState<number | undefined>(undefined);
  const [subtopicoId, setSubtopicoId] = useState<number | undefined>(undefined);
  const [tipoPergunta, setTipoPergunta] = useState<string | undefined>(undefined);
  const [banca, setBanca] = useState<string | undefined>(undefined);
  const [ano, setAno] = useState<number | undefined>(undefined);
  const [quantidade, setQuantidade] = useState(20);
  const [apenasErros, setApenasErros] = useState(false);
  const [excluirRespondidas, setExcluirRespondidas] = useState(false);

  // Recorte sem a quantidade: ela corta a fila, não muda o que existe no banco.
  const recorte = {
    area_id: areaId,
    especialidade_id: especialidadeId,
    subtopico_id: subtopicoId,
    tipo_pergunta: tipoPergunta,
    banca,
    ano,
    apenas_erros: apenasErros,
    excluir_respondidas: excluirRespondidas,
  };
  // Chave exclusiva desta tela (a armadilha do CLAUDE.md sobre queryKey
  // compartilhada) e o número anterior no lugar do vazio enquanto recarrega,
  // para ele não piscar a cada filtro.
  const { data: contagem } = useQuery({
    queryKey: ["praticar-contagem", recorte],
    queryFn: () => api.get<{ total: number }>("/praticar/contagem", recorte),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
  const total = contagem?.total;
  const naFila = total === undefined ? quantidade : Math.min(quantidade, total);

  const { data: areas } = useAreas();
  const { data: especialidades } = useEspecialidades(areaId);
  const { data: temas } = useTemas(areaId, especialidadeId);
  const { data: tipos } = useTiposPergunta();
  const { data: bancas } = useBancas();
  const { data: anos } = useAnos();

  // Só especialidades e temas com casos: escolher um vazio levaria direto ao "nenhum caso encontrado".
  const especialidadesComCasos = especialidades?.filter((e) => e.total_questoes > 0);
  const temasComCasos = temas?.filter((t) => t.total_questoes > 0);
  const nomeArea = areas?.find((a) => a.id === areaId)?.nome;
  const nomeEspecialidade = especialidades?.find((e) => e.id === especialidadeId)?.nome;
  const nomeTema = temas?.find((t) => t.id === subtopicoId)?.nome;

  // Cada nível depende do anterior: trocar a área ou a especialidade limpa o que vinha abaixo.
  function escolherArea(id: number | undefined) {
    setAreaId(id);
    escolherEspecialidade(undefined);
  }
  function escolherEspecialidade(id: number | undefined) {
    setEspecialidadeId(id);
    setSubtopicoId(undefined);
  }

  const chips: { label: string; onRemover: () => void }[] = [];
  if (nomeArea) chips.push({ label: nomeArea, onRemover: () => escolherArea(undefined) });
  if (nomeEspecialidade) chips.push({ label: nomeEspecialidade, onRemover: () => escolherEspecialidade(undefined) });
  if (nomeTema) chips.push({ label: nomeTema, onRemover: () => setSubtopicoId(undefined) });
  if (tipoPergunta) chips.push({ label: tipoPergunta, onRemover: () => setTipoPergunta(undefined) });
  if (banca) chips.push({ label: banca, onRemover: () => setBanca(undefined) });
  if (ano) chips.push({ label: String(ano), onRemover: () => setAno(undefined) });
  if (apenasErros) chips.push({ label: "Apenas erros", onRemover: () => setApenasErros(false) });
  if (excluirRespondidas) chips.push({ label: "Sem casos já respondidos", onRemover: () => setExcluirRespondidas(false) });

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
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
              onChange={(e) => escolherArea(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">Todas</option>
              {areas?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.nome}
                </option>
              ))}
            </select>
          </label>

          <label htmlFor="filtro-especialidade" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Especialidade</span>
            <select
              id="filtro-especialidade"
              className={CAMPO}
              value={especialidadeId ?? ""}
              disabled={!areaId}
              onChange={(e) => escolherEspecialidade(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">{areaId ? "Todas" : "Escolha uma área primeiro"}</option>
              {especialidadesComCasos?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nome} ({e.total_questoes})
                </option>
              ))}
            </select>
          </label>

          {/* Linha inteira: há nomes de tema com mais de 50 caracteres. */}
          <label htmlFor="filtro-tema" className="flex flex-col gap-1.5 sm:col-span-2">
            <span className="rotulo text-muted">Tema</span>
            <select
              id="filtro-tema"
              className={CAMPO}
              value={subtopicoId ?? ""}
              disabled={!especialidadeId}
              onChange={(e) => setSubtopicoId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">{especialidadeId ? "Todos" : "Escolha uma especialidade primeiro"}</option>
              {temasComCasos?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nome} ({t.total_questoes})
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

        {tipos && (
          <div className="flex flex-col gap-2">
            <span className="rotulo text-muted">Tipo de pergunta</span>
            <div className="flex flex-wrap gap-2">
              {[undefined, ...tipos].map((t) => (
                <button
                  key={t ?? "todos"}
                  type="button"
                  aria-pressed={tipoPergunta === t}
                  onClick={() => setTipoPergunta(t)}
                  className={classeSegmento(tipoPergunta === t)}
                >
                  {t ?? "Todos"}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <span className="rotulo text-muted">Quantidade de casos</span>
          <div className="flex flex-wrap gap-2">
            {QUANTIDADES.map((q) => (
              <button
                key={q}
                type="button"
                aria-pressed={quantidade === q}
                onClick={() => setQuantidade(q)}
                className={`${classeSegmento(quantidade === q)} tabular-nums`}
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
                className={`group flex animate-surgir items-center gap-1.5 rounded-etq border border-line bg-ground px-2.5 py-1 text-apoio font-medium text-ink-2 transition duration-hover hover:border-muted hover:text-ink ${PRESSAO}`}
              >
                {chip.label}
                <X size={13} strokeWidth={2} className="transition-transform duration-toggle ease-suave group-hover:rotate-90" />
              </button>
            ))}
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line-soft pt-6">
          {/* A contagem responde a cada filtro: antes só se descobria o tamanho
              do recorte depois de começar a sessão, ou no "nenhum caso". */}
          <span aria-live="polite" className="text-apoio tabular-nums text-muted">
            {total === undefined
              ? "Contando os casos…"
              : total === 0
                ? "Nenhum caso nesse recorte"
                : `${total.toLocaleString("pt-BR")} ${total === 1 ? "caso" : "casos"} nesse recorte`}
          </span>
          <button
            type="button"
            disabled={total === 0}
            onClick={() =>
              onIniciar({
                area_id: areaId,
                especialidade_id: especialidadeId,
                subtopico_id: subtopicoId,
                tipo_pergunta: tipoPergunta,
                banca,
                ano,
                apenas_erros: apenasErros,
                excluir_respondidas: excluirRespondidas,
                quantidade,
              })
            }
            className={`group ${BOTAO_PRIMARIO}`}
          >
            Iniciar sessão de {naFila} {naFila === 1 ? "caso" : "casos"}
            <ArrowRight size={18} strokeWidth={2} className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
