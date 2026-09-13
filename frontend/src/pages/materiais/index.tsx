import { ExternalLink, File, FileText, RefreshCw, Search, Video } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { Paginacao } from "../../components/Paginacao";
import { useMe } from "../../lib/auth";
import { useAreas, useEspecialidades } from "../../lib/catalogo";
import { CAMPO } from "../../lib/estilos";
import { useMateriais, useStatusSincronizacao, useTiposMateriais } from "../../lib/materiais";
import type { Material } from "../../lib/types";
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
    if (valor < 1024) return u === "B" ? `${valor.toFixed(0)} ${u}` : `${valor.toFixed(1).replace(".", ",")} ${u}`;
    valor /= 1024;
  }
  return `${valor.toFixed(1).replace(".", ",")} TB`;
}

function formatarSincronizacao(iso: string | null): string {
  if (!iso) return "Nunca sincronizado";
  const deltaMs = Date.now() - new Date(iso).getTime();
  const horas = Math.floor(deltaMs / 3_600_000);
  const dias = Math.floor(horas / 24);
  if (dias >= 1) return `Sincronizado há ${dias} dia${dias !== 1 ? "s" : ""}`;
  if (horas >= 1) return `Sincronizado há ${horas} h`;
  return "Sincronizado há pouco";
}

// Busca "em tempo real com destaque do trecho encontrado".
function destacarTrecho(texto: string, trecho: string): ReactNode {
  if (!trecho) return texto;
  const idx = texto.toLowerCase().indexOf(trecho.toLowerCase());
  if (idx === -1) return texto;
  return (
    <>
      {texto.slice(0, idx)}
      <mark className="rounded-[2px] bg-t3-soft px-0.5 text-ink">{texto.slice(idx, idx + trecho.length)}</mark>
      {texto.slice(idx + trecho.length)}
    </>
  );
}

export default function Materiais() {
  const navigate = useNavigate();
  const { data: me } = useMe();
  const [areaId, setAreaId] = useState<number | undefined>(undefined);
  const [especialidadeId, setEspecialidadeId] = useState<number | undefined>(undefined);
  const [tipo, setTipo] = useState<string | undefined>(undefined);
  const [buscaInput, setBuscaInput] = useState("");
  const [pagina, setPagina] = useState(0);
  const buscaDebounced = useDebounced(buscaInput, 250);

  const { data: areas } = useAreas();
  const { data: especialidades } = useEspecialidades(areaId);
  const { data: tipos } = useTiposMateriais();
  const { data: status } = useStatusSincronizacao();
  const { data, isLoading } = useMateriais({
    area_id: areaId,
    especialidade_id: especialidadeId,
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
    setEspecialidadeId(undefined);
    setPagina(0);
  }

  function mudarEspecialidade(valor: number) {
    setEspecialidadeId(valor);
    setPagina(0);
  }

  // "aberta" = área escolhida, mas o filtro ativo é uma especialidade dela.
  const classeArea = (estado: "ativa" | "aberta" | "normal") =>
    // shrink-0: dentro da coluna com rolagem os botões encolhiam e os nomes se sobrepunham.
    `block w-full shrink-0 truncate rounded-btn px-3 py-2 text-left text-corpo transition duration-hover ${
      estado === "ativa"
        ? "bg-ink font-semibold text-onink"
        : estado === "aberta"
          ? "font-semibold text-ink hover:bg-ground"
          : "text-ink-2 hover:bg-ground hover:text-ink"
    }`;

  const classeEspecialidade = (ativa: boolean) =>
    `flex w-full shrink-0 items-center justify-between gap-2 rounded-btn py-1.5 pl-6 pr-3 text-left text-apoio transition duration-hover ${
      ativa ? "bg-ink font-semibold text-onink" : "text-ink-2 hover:bg-ground hover:text-ink"
    }`;

  // Com uma especialidade escolhida ela se repetiria em todas as linhas: fica só o assunto.
  const recorteMaterial = (m: Material) =>
    (especialidadeId ? m.subtopico : [m.especialidade, m.subtopico].filter(Boolean).join(" · ")) || null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-2">
          <span className="rotulo text-muted">Acervo de estudo</span>
          <h1 className="text-titulo">Materiais</h1>
        </div>
        <div className="flex items-center gap-4 text-apoio text-muted">
          <span>{formatarSincronizacao(status?.ultima_sincronizacao ?? null)}</span>
          {/* A sincronização é tela do Acervo (Streamlit), só para admin. */}
          {me?.is_admin && (
            <button
              type="button"
              onClick={() => navigate("/sincronizar")}
              className="flex items-center gap-1.5 font-semibold text-ink underline-offset-2 hover:underline"
            >
              <RefreshCw size={14} strokeWidth={2} />
              Sincronizar agora
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-5 md:flex-row">
        <nav aria-label="Áreas" className="md:w-60 md:shrink-0">
          <div className="rotulo mb-2 text-muted">Áreas</div>
          <div className="flex max-h-64 flex-col gap-0.5 overflow-y-auto rounded-card border border-line bg-surface p-1.5 md:max-h-[520px]">
            <button
              type="button"
              onClick={() => mudarArea(undefined)}
              className={classeArea(areaId === undefined ? "ativa" : "normal")}
            >
              Todas
            </button>
            {areas?.map((a) => {
              const aberta = areaId === a.id;
              return (
                <div key={a.id} className="flex shrink-0 flex-col gap-0.5">
                  <button
                    type="button"
                    onClick={() => mudarArea(a.id)}
                    aria-expanded={aberta}
                    className={classeArea(aberta ? (especialidadeId === undefined ? "ativa" : "aberta") : "normal")}
                  >
                    {a.nome}
                  </button>
                  {aberta &&
                    especialidades
                      ?.filter((e) => e.total_materiais > 0)
                      .map((e) => (
                        <button
                          key={e.id}
                          type="button"
                          onClick={() => mudarEspecialidade(e.id)}
                          aria-pressed={especialidadeId === e.id}
                          className={classeEspecialidade(especialidadeId === e.id)}
                        >
                          <span className="truncate">{e.nome}</span>
                          <span className="shrink-0 tabular-nums opacity-70">{e.total_materiais}</span>
                        </button>
                      ))}
                </div>
              );
            })}
          </div>
        </nav>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <select
              aria-label="Tipo de material"
              value={tipo ?? ""}
              onChange={(e) => {
                setTipo(e.target.value || undefined);
                setPagina(0);
              }}
              className={`${CAMPO} sm:w-52`}
            >
              <option value="">Todos os tipos</option>
              {tipos?.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <div className="relative flex-1">
              <Search size={16} strokeWidth={2} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
              <input
                type="search"
                aria-label="Buscar por título"
                value={buscaInput}
                onChange={(e) => {
                  setBuscaInput(e.target.value);
                  setPagina(0);
                }}
                placeholder="Buscar por título"
                className={`${CAMPO} pl-9`}
              />
            </div>
          </div>

          {isLoading ? (
            <div className="h-64 animate-pulse rounded-card bg-line-soft" />
          ) : total === 0 ? (
            <EstadoVazio mensagem="Nenhum material encontrado. Ajuste a área, o tipo ou a busca." />
          ) : (
            <>
              <div className="overflow-x-auto rounded-card border border-line bg-surface">
                <table className="w-full text-left text-corpo">
                  <thead>
                    <tr className="border-b border-line">
                      <th className="w-10 px-4 py-2.5" />
                      <th className="rotulo px-3 py-2.5 text-muted">Título</th>
                      <th className="rotulo hidden px-3 py-2.5 text-muted xl:table-cell">
                        {especialidadeId ? "Assunto" : "Especialidade · assunto"}
                      </th>
                      <th className="rotulo hidden px-3 py-2.5 text-right text-muted sm:table-cell">Tamanho</th>
                      <th className="w-24 px-3 py-2.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {itens.map((m) => {
                      const Icone = iconePorTipo(m.tipo);
                      const recorte = recorteMaterial(m);
                      return (
                        <tr key={m.id} className="group h-11 border-b border-line-soft last:border-0 hover:bg-ground">
                          <td className="px-4">
                            <Icone size={16} strokeWidth={2} className="text-muted" aria-label={m.tipo} />
                          </td>
                          {/* overflow-wrap: nomes de arquivo sem espaço empurravam a tabela para fora do contêiner. */}
                          <td className="px-3 py-2 text-ink [overflow-wrap:anywhere]">
                            {destacarTrecho(m.titulo, buscaDebounced)}
                            {/* Abaixo de 1280px o assunto vem sob o título: a coluna própria sumia para a direita. */}
                            {recorte && <div className="text-apoio text-muted xl:hidden">{recorte}</div>}
                          </td>
                          <td className="hidden px-3 py-2 text-muted xl:table-cell">{recorte ?? "—"}</td>
                          <td className="hidden px-3 py-2 text-right tabular-nums text-muted sm:table-cell">
                            {formatarTamanho(m.tamanho_bytes)}
                          </td>
                          <td className="px-3 py-2 text-right">
                            {/* opacity em vez de display: o link continua alcançável pelo teclado.
                                Em tela de toque não existe hover, então ele fica sempre visível. */}
                            <a
                              href={m.link_mediafire}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 rounded-btn border border-line bg-surface px-2.5 py-1 text-apoio font-semibold text-ink opacity-0 transition duration-hover hover:border-muted focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
                            >
                              Abrir
                              <ExternalLink size={13} strokeWidth={2} />
                            </a>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <Paginacao pagina={pagina} totalPaginas={totalPaginas} total={total} onMudar={setPagina} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
