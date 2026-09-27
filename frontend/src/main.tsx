import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import { BarreiraErro } from "./components/BarreiraErro";
import { capturarErros } from "./lib/erros";
import { queryClient } from "./lib/queryClient";
import { aplicarTema, temaInicial } from "./lib/theme";
import "./styles/theme.css";

// Antes do primeiro quadro, e fora do AppShell de propósito: o login e a
// redefinição de senha ficam fora dele e apareciam sempre no tema claro, mesmo
// para quem escolheu o escuro. Também evita o pisca-claro no carregamento.
aplicarTema(temaInicial());
// Erro fora do React (evento, promessa sem catch) também vai para o servidor.
capturarErros();

// As telas vêm sob demanda (App.tsx). Depois de um deploy, a aba que já estava
// aberta pede as telas da versão anterior, que saíram do servidor, e a troca de
// aba quebrava; recarregar traz a versão nova (o que o Vite recomenda). No máximo
// uma vez por minuto, e nunca sem rede: offline, recarregar só troca a tela por
// uma página de erro do navegador.
window.addEventListener("vite:preloadError", (evento) => {
  if (!navigator.onLine) return;
  try {
    const ultima = Number(sessionStorage.getItem("conduta:recarregou-em") ?? 0);
    if (Date.now() - ultima < 60_000) return;
    sessionStorage.setItem("conduta:recarregou-em", String(Date.now()));
  } catch {
    return; // sem sessionStorage não há como evitar um laço de recargas
  }
  evento.preventDefault();
  window.location.reload();
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BarreiraErro>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </BarreiraErro>
  </StrictMode>,
);
