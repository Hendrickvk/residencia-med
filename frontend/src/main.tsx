import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import { BarreiraErro } from "./components/BarreiraErro";
import { queryClient } from "./lib/queryClient";
import { aplicarTema, temaInicial } from "./lib/theme";
import "./styles/theme.css";

// Antes do primeiro quadro, e fora do AppShell de propósito: o login e a
// redefinição de senha ficam fora dele e apareciam sempre no tema claro, mesmo
// para quem escolheu o escuro. Também evita o pisca-claro no carregamento.
aplicarTema(temaInicial());

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
