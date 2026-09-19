import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Marca } from "../components/shell/Marca";
import { ApiError } from "../lib/api";
import { useAuthActions } from "../lib/auth";
import { BOTAO_PRIMARIO, CAMPO } from "../lib/estilos";

// Tela do link recebido por e-mail (`/senha/:token`). Rota pública: quem chega
// aqui justamente não consegue entrar. O token não aparece em nenhum texto da
// página — só viaja na URL e no corpo do POST.
export default function Senha() {
  const { token = "" } = useParams();
  const [senha, setSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const { redefinirSenha } = useAuthActions();
  const navigate = useNavigate();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (senha !== confirmar) {
      setErro("As senhas não coincidem.");
      return;
    }
    setEnviando(true);
    try {
      await redefinirSenha(token, senha);
      // O endpoint devolve a sessão no cookie: entra direto, sem pedir de novo
      // a senha que acabou de ser criada.
      navigate("/painel", { replace: true });
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível conectar à API.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ground px-4 py-10">
      <div className="flex w-full max-w-[400px] animate-entrar flex-col gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <Marca grande />
          <p className="text-corpo text-ink-2">Escolha uma senha nova</p>
        </div>

        <form
          onSubmit={onSubmit}
          className="flex flex-col gap-4 rounded-caso border border-line bg-surface p-6 md:p-7"
        >
          <label htmlFor="senha-nova" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Nova senha</span>
            <input
              id="senha-nova"
              type="password"
              autoComplete="new-password"
              autoFocus
              required
              minLength={6}
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className={CAMPO}
            />
          </label>
          <label htmlFor="senha-confirmar" className="flex flex-col gap-1.5">
            <span className="rotulo text-muted">Confirmar senha</span>
            <input
              id="senha-confirmar"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              value={confirmar}
              onChange={(e) => setConfirmar(e.target.value)}
              className={CAMPO}
            />
          </label>

          {erro && (
            <p role="alert" className="animate-entrar text-apoio font-medium text-t1">
              {erro}
              {/* Link expirado ou já usado cai aqui: o caminho de volta é pedir outro. */}
              <button
                type="button"
                onClick={() => navigate("/login", { replace: true })}
                className="ml-1 font-semibold text-ink underline underline-offset-2"
              >
                Voltar ao login
              </button>
            </p>
          )}

          <button type="submit" disabled={enviando} className={`${BOTAO_PRIMARIO} mt-1 w-full`}>
            Salvar e entrar
          </button>
        </form>
      </div>
    </div>
  );
}
