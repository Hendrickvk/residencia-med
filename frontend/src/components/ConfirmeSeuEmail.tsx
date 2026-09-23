import { useState } from "react";
import { MailCheck } from "lucide-react";
import { api, ApiError } from "../lib/api";
import { useMe } from "../lib/auth";
import { BOTAO_SECUNDARIO } from "../lib/estilos";

// Faixa que aparece enquanto a conta não confirmou o e-mail. Fica acima da
// tela inteira, e não só no Painel, porque o que ela explica é justamente por
// que Praticar e Simulado não abrem.
//
// Sem cor de triagem: a escala só codifica nível de aproveitamento
// (DESIGN_TRIAGEM.md §2), e isto não é um nível — é um recado. Borda e tinta,
// como o resto do que não é nível.
export function ConfirmeSeuEmail() {
  const { data: me } = useMe();
  const [estado, setEstado] = useState<"parado" | "enviando" | "enviado">("parado");
  const [erro, setErro] = useState<string | null>(null);

  if (!me || me.email_confirmado) return null;

  async function reenviar() {
    setErro(null);
    setEstado("enviando");
    try {
      await api.post("/auth/confirmar/reenviar");
      setEstado("enviado");
    } catch (e) {
      setEstado("parado");
      setErro(e instanceof ApiError ? e.message : "Não deu para pedir outro link agora.");
    }
  }

  return (
    <div
      role="status"
      className="mb-7 flex animate-entrar flex-col gap-3 rounded-card border border-line bg-surface p-5 md:flex-row md:items-center md:justify-between md:gap-6"
    >
      <div className="flex items-start gap-3">
        <MailCheck className="mt-0.5 shrink-0 text-ink-2" size={18} strokeWidth={2} aria-hidden="true" />
        <div>
          <p className="text-corpo font-semibold text-ink">Confirme o seu e-mail para liberar as questões</p>
          <p className="mt-0.5 text-apoio text-muted">
            Mandamos um link para <span className="text-ink-2">{me.email}</span>. Se não chegou, olhe o spam
            {" "}— ou peça outro.
          </p>
        </div>
      </div>

      {estado === "enviado" ? (
        <p className="shrink-0 text-apoio font-medium text-t4">Link novo enviado.</p>
      ) : (
        <button
          type="button"
          onClick={reenviar}
          disabled={estado === "enviando"}
          className={`${BOTAO_SECUNDARIO} shrink-0`}
        >
          {estado === "enviando" ? "Enviando…" : "Enviar outro link"}
        </button>
      )}

      {erro && (
        <p role="alert" className="text-apoio font-medium text-t1 md:shrink-0">
          {erro}
        </p>
      )}
    </div>
  );
}
