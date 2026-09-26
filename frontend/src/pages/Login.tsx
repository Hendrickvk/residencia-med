import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
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
  // Terceiro estado da tela, além de entrar/criar: pedir o link de
  // redefinição. Fica aqui em vez de virar rota porque é o mesmo cartão.
  const [esqueci, setEsqueci] = useState(false);
  const [pedido, setPedido] = useState(false);
  const { entrar, cadastrar, pedirRedefinicao } = useAuthActions();
  const navigate = useNavigate();
  // Volta para onde ela ia antes de cair aqui (RequireAuth). Só caminho
  // interno: o endereço não pode servir de redirecionamento para fora.
  const de = (useLocation().state as { de?: string } | null)?.de;
  const destino = de && de.startsWith("/") && !de.startsWith("//") && !de.startsWith("/login") ? de : "/painel";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (aba === "criar" && senha !== confirmar) {
      setErro("As senhas não coincidem.");
      return;
    }
    setEnviando(true);
    try {
      if (esqueci) {
        await pedirRedefinicao(email);
        setPedido(true);
        return;
      }
      if (aba === "entrar") await entrar(email, senha);
      else await cadastrar(email, senha);
      navigate(destino, { replace: true });
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
          <p className="text-corpo text-ink-2">Sua plataforma de estudos para residência médica</p>
        </div>

        <div className="flex flex-col gap-5 rounded-caso border border-line bg-surface p-6 md:p-7">
          {/* Fundo da aba ativa desliza entre as duas colunas (iguais). */}
          <div role="tablist" aria-label="Acesso" className="relative grid grid-cols-2 gap-1 rounded-btn bg-ground p-1">
            <span
              aria-hidden="true"
              className="absolute inset-y-1 left-1 w-[calc(50%-6px)] rounded-col border border-line bg-surface transition-transform duration-desliza ease-suave"
              style={{ transform: aba === "criar" ? "translateX(calc(100% + 4px))" : "none" }}
            />
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
                className={`relative h-9 rounded-col text-[14px] font-semibold transition-colors duration-toggle ${
                  aba === valor ? "text-ink" : "text-muted hover:text-ink"
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
            {!esqueci && (
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
            )}
            {aba === "criar" && !esqueci && (
              <label htmlFor="login-confirmar" className="flex animate-entrar flex-col gap-1.5">
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
              <p role="alert" className="animate-entrar text-apoio font-medium text-t1">
                {erro}
              </p>
            )}

            {/* Mensagem de propósito vaga: dizer "não existe conta com esse
                e-mail" contaria a um estranho quem tem cadastro aqui. */}
            {pedido && (
              <p role="status" className="animate-entrar rounded-card border border-line bg-ground p-3 text-apoio text-ink-2">
                Se existe uma conta com esse e-mail, o link para criar uma senha nova já está a caminho. Ele vale
                por uma hora e só pode ser usado uma vez.
              </p>
            )}

            <button type="submit" disabled={enviando} className={`${BOTAO_PRIMARIO} mt-1 w-full`}>
              {esqueci ? "Enviar o link" : aba === "entrar" ? "Entrar" : "Criar conta"}
            </button>

            {aba === "entrar" && (
              <button
                type="button"
                onClick={() => {
                  setEsqueci((v) => !v);
                  setErro(null);
                  setPedido(false);
                }}
                className="self-center text-apoio text-muted underline-offset-2 transition-colors duration-hover hover:text-ink hover:underline"
              >
                {esqueci ? "Voltar para o login" : "Esqueci minha senha"}
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
