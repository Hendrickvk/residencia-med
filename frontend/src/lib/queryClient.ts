import { QueryClient } from "@tanstack/react-query";

// Instância compartilhada — precisa ser a mesma usada pelo QueryClientProvider
// em main.tsx para que módulos fora de componentes React (respostasQueue.ts)
// também consigam invalidar cache (ex: refletir ofensiva/contadores após
// responder uma questão).
// `retry` só para o que adianta repetir: 4xx é resposta do servidor sobre o
// pedido (401, 404, o 429 do teto diário de prática), e repeti-la três vezes
// só atrasa a mensagem que a tela precisa mostrar.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (tentativas, erro) => {
        const status = (erro as { status?: number })?.status;
        if (status && status >= 400 && status < 500) return false;
        return tentativas < 3;
      },
    },
  },
});
