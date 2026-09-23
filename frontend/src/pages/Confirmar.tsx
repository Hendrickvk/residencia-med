import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Marca } from "../components/shell/Marca";
import { api, ApiError } from "../lib/api";
import { BOTAO_PRIMARIO } from "../lib/estilos";

// Tela do link de confirmação (`/confirmar/:token`). Rota pública: o link
// costuma ser aberto no celular, que não é o navegador onde a conta foi
// criada. Confirmar não dá sessão — por isso o fim do caminho é o login, e
// não o Painel.
export default function Confirmar() {
  const { token = "" } = useParams();
  const [estado, setEstado] = useState<"confirmando" | "pronto" | "falhou">("confirmando");
  const [erro, setErro] = useState<string | null>(null);
  // O StrictMode do React monta o efeito duas vezes em desenvolvimento, e o
  // token é de uso único: sem esta trava a segunda chamada queimava o link e
  // a tela dizia que ele não valia mais.
  const jaPediu = useRef(false);

  useEffect(() => {
    if (jaPediu.current) return;
    jaPediu.current = true;
    api
      .post("/auth/confirmar", { token })
      .then(() => setEstado("pronto"))
      .catch((e) => {
        setErro(e instanceof ApiError ? e.message : "Não foi possível conectar à API.");
        setEstado("falhou");
      });
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-ground px-4 py-10">
      <div className="flex w-full max-w-[400px] animate-entrar flex-col gap-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <Marca grande />
          <p className="text-corpo text-ink-2">
            {estado === "confirmando" ? "Confirmando o seu e-mail…" : "Confirmação de e-mail"}
          </p>
        </div>

        <div className="flex flex-col gap-4 rounded-caso border border-line bg-surface p-6 text-center md:p-7">
          {estado === "confirmando" && (
            <div className="h-11 animate-pulse rounded-btn bg-line-soft" aria-hidden="true" />
          )}

          {estado === "pronto" && (
            <>
              <p className="text-corpo text-ink-2">
                Pronto. A sua conta está confirmada e as questões estão liberadas.
              </p>
              <Link to="/login" className={`${BOTAO_PRIMARIO} w-full`}>
                Entrar e estudar
              </Link>
            </>
          )}

          {estado === "falhou" && (
            <>
              <p role="alert" className="text-corpo font-medium text-t1">
                {erro}
              </p>
              {/* Link vencido ou já usado: o caminho de volta é entrar e pedir
                  outro pelo aviso do Painel, que é onde o botão vive. */}
              <Link to="/login" className={`${BOTAO_PRIMARIO} w-full`}>
                Ir para o login
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
