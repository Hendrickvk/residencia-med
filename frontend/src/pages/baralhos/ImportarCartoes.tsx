import { FileUp, X } from "lucide-react";
import { useRef, useState } from "react";
import { Dialog } from "../../components/Dialog";
import { ApiError } from "../../lib/api";
import { importarCartoes, plural, type ResultadoImportacao } from "../../lib/cartoes";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";

// Importar em duas etapas: conferir (o servidor lê e devolve a contagem e uma
// amostra, sem gravar) e só então importar. Um separador errado viraria
// centenas de cartões tortos, e não há apagar em lote.
export function ImportarCartoes({
  aberto, baralhoId, onFechar, onSalvo,
}: {
  aberto: boolean;
  baralhoId: number;
  onFechar: () => void;
  onSalvo: () => void;
}) {
  const [texto, setTexto] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [previa, setPrevia] = useState<ResultadoImportacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const campoArquivo = useRef<HTMLInputElement>(null);
  // Abre sempre limpo.
  const [ultimoAberto, setUltimoAberto] = useState(aberto);
  if (aberto !== ultimoAberto) {
    setUltimoAberto(aberto);
    if (aberto) {
      setTexto("");
      setArquivo(null);
      setPrevia(null);
      setErro(null);
    }
  }

  const vazio = !arquivo && !texto.trim();

  function trocou() {
    setPrevia(null);
    setErro(null);
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (vazio) return;
    setEnviando(true);
    setErro(null);
    try {
      const r = await importarCartoes(baralhoId, arquivo ?? texto, !previa);
      if (previa) {
        onSalvo();
        onFechar();
      } else setPrevia(r);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível conectar à API.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog titulo="Importar cartões" aberto={aberto} onFechar={onFechar}>
      <form onSubmit={enviar} className="flex flex-col gap-4">
        <p className="text-apoio text-ink-2">
          Uma linha por cartão, com frente e verso separados por tab, ponto e vírgula ou vírgula. Do Anki, vale o
          arquivo .apkg ou o export em texto.
        </p>

        {arquivo ? (
          <div className="flex items-center gap-3 rounded-btn border border-line bg-ground px-3 py-2.5">
            <FileUp size={18} strokeWidth={2} className="shrink-0 text-muted" />
            <span className="min-w-0 flex-1 truncate text-corpo text-ink">{arquivo.name}</span>
            <button
              type="button"
              onClick={() => {
                setArquivo(null);
                trocou();
              }}
              aria-label="Tirar o arquivo"
              className="rounded-btn p-1.5 text-muted transition duration-hover hover:bg-surface hover:text-ink"
            >
              <X size={14} strokeWidth={2} />
            </button>
          </div>
        ) : (
          <>
            <label htmlFor="importar-texto" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">Colar</span>
              <textarea
                id="importar-texto"
                value={texto}
                onChange={(e) => {
                  setTexto(e.target.value);
                  trocou();
                }}
                rows={5}
                autoFocus
                placeholder={"Sinal de Murphy;Colecistite aguda\nTríade de Charcot;Colangite"}
                className={`${CAMPO} h-auto py-2 leading-normal`}
              />
            </label>
            <input
              ref={campoArquivo}
              type="file"
              accept=".apkg,.txt,.csv,.tsv,text/plain,text/csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                e.target.value = "";
                if (f) {
                  setArquivo(f);
                  trocou();
                }
              }}
            />
            <button type="button" onClick={() => campoArquivo.current?.click()} className={BOTAO_SECUNDARIO}>
              <FileUp size={18} strokeWidth={2} />
              Escolher arquivo
            </button>
          </>
        )}

        {previa && (
          <div role="status" className="animate-entrar flex flex-col gap-2.5 rounded-card border border-line bg-ground p-3">
            <p className="text-apoio text-ink-2">
              <span className="font-semibold text-ink">{plural(previa.cartoes)}</span>
              {previa.ignorados > 0 &&
                ` · ${previa.ignorados} sem frente ou verso ${previa.ignorados === 1 ? "ficou" : "ficaram"} de fora${
                  arquivo?.name.endsWith(".apkg") ? " (em geral, um campo que era só imagem)" : ""
                }`}
            </p>
            <ul className="flex flex-col gap-2">
              {previa.amostra.map((c, i) => (
                <li key={i} className="rounded-btn border border-line bg-surface px-3 py-2 [overflow-wrap:anywhere]">
                  <p className="line-clamp-2 whitespace-pre-line text-apoio font-semibold text-ink">{c.frente}</p>
                  <p className="mt-0.5 line-clamp-2 whitespace-pre-line text-apoio text-ink-2">{c.verso}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {erro && (
          <p role="alert" className="animate-entrar text-apoio font-medium text-t1">
            {erro}
          </p>
        )}

        <button type="submit" disabled={enviando || vazio} className={`${BOTAO_PRIMARIO} w-full`}>
          {enviando ? (previa ? "Importando…" : "Lendo…") : previa ? `Importar ${plural(previa.cartoes)}` : "Conferir"}
        </button>
      </form>
    </Dialog>
  );
}
