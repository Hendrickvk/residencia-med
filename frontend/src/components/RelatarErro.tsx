import { useState } from "react";
import { Flag } from "lucide-react";
import { Dialog } from "./Dialog";
import { api } from "../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO, PRESSAO } from "../lib/estilos";

// As partes vêm de db.PARTES_RELATO. Repetidas aqui como rótulos estáticos em
// vez de buscadas por GET: são seis palavras que mudam junto com o schema, e
// um fetch só para preencher seis botões atrasaria a abertura do diálogo.
// O servidor valida de novo, então divergir não grava lixo — dá 422.
const PARTES = ["Enunciado", "Alternativas", "Gabarito", "Explicação", "Imagem", "Outro"] as const;

// "Relatar erro" aparece junto da discussão, nos mesmos três lugares que
// TemaDoCaso: depois de responder no Praticar e na Revisão, e no resultado do
// Simulado. Nunca durante a prova — lá o aluno ainda não viu o gabarito, e
// abrir o diálogo tiraria o foco sem que ele tenha o que relatar.
export function RelatarErro({ questaoId }: { questaoId: number }) {
  const [aberto, setAberto] = useState(false);
  const [parte, setParte] = useState<string | null>(null);
  const [comentario, setComentario] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function abrir() {
    setParte(null);
    setComentario("");
    setErro(null);
    setAberto(true);
  }

  async function enviar() {
    if (!parte || enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      await api.post(`/questoes/${questaoId}/relato`, { parte, comentario: comentario || null });
      setAberto(false);
      setEnviado(true);
    } catch {
      setErro("Não consegui enviar agora. Tente de novo em instantes.");
    } finally {
      setEnviando(false);
    }
  }

  // Depois de relatar, o botão sai do lugar e vira agradecimento: evita o
  // aluno mandar o mesmo relato três vezes achando que não foi.
  if (enviado) {
    return <span className="text-apoio text-muted">Obrigado, seu relato foi registrado.</span>;
  }

  return (
    <>
      <button
        type="button"
        onClick={abrir}
        className={`inline-flex items-center gap-1.5 self-start text-apoio text-muted transition duration-hover ease-brand hover:text-ink-2 ${PRESSAO}`}
      >
        <Flag size={13} strokeWidth={2} />
        Relatar erro
      </button>

      <Dialog titulo="Relatar erro nesta questão" aberto={aberto} onFechar={() => setAberto(false)}>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <span className="rotulo text-muted">Onde está o problema?</span>
            <div className="flex flex-wrap gap-2">
              {PARTES.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setParte(p)}
                  aria-pressed={parte === p}
                  className={`h-9 rounded-btn border px-3 text-[14px] font-medium transition duration-hover ease-brand ${PRESSAO} ${
                    parte === p
                      ? "border-ink bg-ink text-onink"
                      : "border-line text-ink-2 hover:border-muted hover:text-ink"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <label className="flex flex-col gap-2">
            <span className="rotulo text-muted">O que está errado? (opcional)</span>
            <textarea
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              maxLength={1000}
              rows={3}
              placeholder="Ex.: a explicação defende a letra B, mas o gabarito é a C."
              className={`${CAMPO} h-auto resize-none py-2`}
            />
          </label>

          {erro && (
            <p role="alert" className="animate-entrar text-apoio font-medium text-t1">
              {erro}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setAberto(false)} className={BOTAO_SECUNDARIO}>
              Cancelar
            </button>
            <button type="button" onClick={enviar} disabled={!parte || enviando} className={BOTAO_PRIMARIO}>
              {enviando ? "Enviando..." : "Enviar"}
            </button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
