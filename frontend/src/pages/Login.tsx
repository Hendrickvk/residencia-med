import { Stethoscope } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../lib/api";
import { useAuthActions } from "../lib/auth";

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
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-panel bg-action-soft text-action">
            <Stethoscope size={28} strokeWidth={1.5} />
          </div>
          <div className="text-h1 text-ink-700">Residência Med</div>
          <div className="mt-1 text-apoio text-ink-500">Sua plataforma de estudos para residência médica</div>
        </div>

        <div className="rounded-panel border border-line bg-surface p-6">
          <div className="mb-5 flex gap-1 rounded-btn bg-canvas p-1">
            {(["entrar", "criar"] as const).map((valor) => (
              <button
                key={valor}
                type="button"
                onClick={() => {
                  setAba(valor);
                  setErro(null);
                }}
                className={`flex-1 rounded-btn py-1.5 text-apoio font-medium transition-hover ${
                  aba === valor ? "bg-surface text-ink-700 shadow-sm" : "text-ink-500"
                }`}
              >
                {valor === "entrar" ? "Entrar" : "Criar conta"}
              </button>
            ))}
          </div>

          <form onSubmit={onSubmit} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-apoio text-ink-500">E-mail</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-apoio text-ink-500">Senha</span>
              <input
                type="password"
                required
                minLength={6}
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
              />
            </label>
            {aba === "criar" && (
              <label className="flex flex-col gap-1">
                <span className="text-apoio text-ink-500">Confirmar senha</span>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={confirmar}
                  onChange={(e) => setConfirmar(e.target.value)}
                  className="h-9 rounded-btn border border-line bg-surface px-3 text-corpo text-ink-700 outline-none focus:border-action focus:ring-[3px] focus:ring-action-soft"
                />
              </label>
            )}

            {erro && <p className="text-apoio text-wrong">{erro}</p>}

            <button
              type="submit"
              disabled={enviando}
              className="mt-2 h-10 rounded-btn bg-action text-sm font-medium text-white transition-hover hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-line disabled:text-ink-300"
            >
              {aba === "entrar" ? "Entrar" : "Criar conta"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
