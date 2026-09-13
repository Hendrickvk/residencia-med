import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Marca } from "../components/shell/Marca";
import { ApiError } from "../lib/api";
import { useAuthActions } from "../lib/auth";
import { BOTAO_PRIMARIO, CAMPO } from "../lib/estilos";

export default function Login() {
  const [aba, setAba] = useState<"entrar" | "criar">("entrar");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const { entrar, cadastrar } = useAuthActions();
  const navigate = useNavigate();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (aba === "criar" && senha !== confirmar) {
      setErro("As senhas não coincidem.");
      return;
    }
    setEnviando(true);
    try {
      if (aba === "entrar") await entrar(email, senha);
      else await cadastrar(email, senha);
      navigate("/painel", { replace: true });
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível conectar à API.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ground px-4 py-10">
      <div className="flex w-full max-w-[400px] flex-col gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <Marca grande />
          <p className="text-corpo text-ink-2">Sua plataforma de estudos para residência médica</p>
        </div>

        <div className="flex flex-col gap-5 rounded-caso border border-line bg-surface p-6 md:p-7">
          <div role="tablist" aria-label="Acesso" className="grid grid-cols-2 gap-1 rounded-btn bg-ground p-1">
            {(["entrar", "criar"] as const).map((valor) => (
              <button
                key={valor}
                type="button"
                role="tab"
                aria-selected={aba === valor}
                onClick={() => {
                  setAba(valor);
                  setErro(null);
                }}
                className={`h-9 rounded-col text-[14px] transition duration-hover ${
                  aba === valor ? "border border-line bg-surface font-semibold text-ink" : "text-muted hover:text-ink"
                }`}
              >
                {valor === "entrar" ? "Entrar" : "Criar conta"}
              </button>
            ))}
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <label htmlFor="login-email" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">E-mail</span>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={CAMPO}
              />
            </label>
            <label htmlFor="login-senha" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">Senha</span>
              <input
                id="login-senha"
                type="password"
                autoComplete={aba === "entrar" ? "current-password" : "new-password"}
                required
                minLength={6}
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                className={CAMPO}
              />
            </label>
            {aba === "criar" && (
              <label htmlFor="login-confirmar" className="flex flex-col gap-1.5">
                <span className="rotulo text-muted">Confirmar senha</span>
                <input
                  id="login-confirmar"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={6}
                  value={confirmar}
                  onChange={(e) => setConfirmar(e.target.value)}
                  className={CAMPO}
                />
              </label>
            )}

            {erro && (
              <p role="alert" className="text-apoio font-medium text-t1">
                {erro}
              </p>
            )}

            <button type="submit" disabled={enviando} className={`${BOTAO_PRIMARIO} mt-1 w-full`}>
              {aba === "entrar" ? "Entrar" : "Criar conta"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
