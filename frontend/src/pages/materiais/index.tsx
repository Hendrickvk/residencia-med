import { File, FileText, RefreshCw, Video } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { Paginacao } from "../../components/Paginacao";
import { useAreas } from "../../lib/catalogo";
import { useMateriais, useStatusSincronizacao, useTiposMateriais } from "../../lib/materiais";
import { useDebounced } from "../../lib/useDebounced";

const POR_PAGINA = 50;

function iconePorTipo(tipo: string) {
  const t = tipo.toLowerCase();
  if (t.includes("vídeo") || t.includes("video")) return Video;
  if (t.includes("apostila")) return FileText;
  return File;
}

function formatarTamanho(bytes: number | null): string {
  if (!bytes) return "—";
  const unidades = ["B", "KB", "MB", "GB"];
  let valor = bytes;
  for (const u of unidades) {
    if (valor < 1024) return u === "B" ? `${valor.toFixed(0)} ${u}` : `${valor.toFixed(1)} ${u}`;
    valor /= 1024;
  }
  return `${valor.toFixed(1)} TB`;
}

function formatarSincronizacao(iso: string | null): string {
  if (!iso) return "Nunca sincronizado";
  const deltaMs = Date.now() - new Date(iso).getTime();
  const horas = Math.floor(deltaMs / 3_600_000);
  const dias = Math.floor(horas / 24);
  if (dias >= 1) return `Sincronizado há ${dias} dia(s)`;
  if (horas >= 1) return `Sincronizado há ${horas}h`;
  return "Sincronizado agora há pouco";
}

// REDESIGN.md §4.5: busca "em tempo real com destaque do trecho encontrado".
function destacarTrecho(texto: string, trecho: string): ReactNode {
  if (!trecho) return texto;
  const idx = texto.toLowerCase().indexOf(trecho.toLowerCase());
  if (idx === -1) return texto;
  return (
    <>
      {texto.slice(0, idx)}
      <mark className="rounded-sm bg-warn-soft text-ink-700">{texto.slice(idx, idx + trecho.length)}</mark>
      {texto.slice(idx + trecho.length)}
    </>
  );
}

export default function Materiais() {
  const navigate = useNavigate();
  const [areaId, setAreaId] = useState<number | undefined>(undefined);
  const [tipo, setTipo] = useState<string | undefined>(undefined);
  const [buscaInput, setBuscaInput] = useState("");
  const [pagina, setPagina] = useState(0);
  const buscaDebounced = useDebounced(buscaInput, 250);

  const { data: areas } = useAreas();
  const { data: tipos } = useTiposMateriais();
  const { data: status } = useStatusSincronizacao();
  const { data, isLoading } = useMateriais({
    area_id: areaId,
    tipo,
    q: buscaDebounced || undefined,
    pagina,
    limite: POR_PAGINA,
  });

  const itens = data?.itens ?? [];
  const total = data?.total ?? 0;
  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));

  function mudarArea(valor: number | undefined) {
    setAreaId(valor);
    setPagina(0);
  }

  return (
    <div>
      <h1 className="mb-4 text-h1 text-ink-700">Materiais</h1>

      <div className="mb-5 flex items-center justify-between rounded-btn border border-line bg-surface px-4 py-2.5">
        <span className="text-apoio text-ink-500">{formatarSincronizacao(status?.ultima_sincronizacao ?? null)}</span>
        <button
          type="button"
          onClick={() => navigate("/sincronizar")}
          className="flex items-center gap-1.5 text-apoio text-action hover:underline"
        >
          <RefreshCw size={13} strokeWidth={1.5} />
          Sincronizar agora
        </button>
      </div>

      <div className="flex flex-col gap-5 md:flex-row">
        <div className="md:w-60 md:shrink-0">
          <div className="mb-2 text-apoio font-medium text-ink-500">Áreas</div>
          <div className="max-h-[420px] overflow-y-auto rounded-panel border border-line bg-surface p-1">
            <button
              type="button"
              onClick={() => mudarArea(undefined)}
              className={`block w-full rounded-btn px-3 py-2 text-left text-corpo transition-hover ${
                areaId === undefined ? "bg-action-soft text-action" : "text-ink-700 hover:bg-canvas"
              }`}
            >
              Todas
            </button>
            {areas?.map((a) => (
              <button
                key={a.id}
                type="button"
                onClick={() => mudarArea(a.id)}
                className={`block w-full truncate rounded-btn px-3 py-2 text-left text-corpo transition-hover ${
                  areaId === a.id ? "bg-action-soft text-action" : "text-ink-700 hover:bg-canvas"
                }`}
              >
                {a.nome}
              </button>
            ))}
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-col gap-2 sm:flex-row">
            <select
              value={tipo ?? ""}
              onChange={(e) => {
                setTipo(e.target.value || undefined);
                setPagina(0);
              }}
              className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft sm:w-48"
            >
              <option value="">Todos os tipos</option>
              {tipos?.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              type="search"
              value={buscaInput}
              onChange={(e) => {
                setBuscaInput(e.target.value);
                setPagina(0);
              }}
              placeholder="Buscar por título..."
              className="h-9 flex-1 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
            />
          </div>

          {isLoading ? (
            <div className="h-64 animate-pulse rounded-panel bg-line/40" />
          ) : total === 0 ? (
            <EstadoVazio mensagem="Nenhum material encontrado. Ajuste os filtros ou adicione um novo." />
          ) : (
            <>
              <div className="overflow-x-auto rounded-panel border border-line">
                <table className="w-full text-left text-corpo">
                  <thead>
                    <tr className="border-b border-line bg-canvas text-apoio text-ink-500">
                      <th className="w-8 px-3 py-2" />
                      <th className="px-3 py-2">Título</th>
                      <th className="px-3 py-2">Assunto</th>
                      <th className="px-3 py-2 text-right">Tamanho</th>
                      <th className="w-24 px-3 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {itens.map((m) => {
                      const Icone = iconePorTipo(m.tipo);
                      return (
                        <tr key={m.id} className="group h-11 border-b border-line last:border-0 hover:bg-canvas">
                          <td className="px-3">
                            <Icone size={16} strokeWidth={1.5} className="text-ink-500" />
                          </td>
                          <td className="px-3 py-2 text-ink-700">{destacarTrecho(m.titulo, buscaDebounced)}</td>
                          <td className="px-3 py-2 text-ink-500">{m.subtopico ?? "—"}</td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-500">
                            {formatarTamanho(m.tamanho_bytes)}
                          </td>
                          <td className="px-3 py-2 text-right">
                            <a
                              href={m.link_mediafire}
                              target="_blank"
                              rel="noreferrer"
                              className="hidden rounded-btn border border-line px-2.5 py-1 text-apoio text-ink-700 transition-hover hover:border-action group-hover:inline-block"
                            >
                              Abrir
                            </a>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="mt-4">
                <Paginacao pagina={pagina} totalPaginas={totalPaginas} total={total} onMudar={setPagina} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
