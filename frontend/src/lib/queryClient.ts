import { QueryClient } from "@tanstack/react-query";

// Instância compartilhada — precisa ser a mesma usada pelo QueryClientProvider
// em main.tsx para que módulos fora de componentes React (respostasQueue.ts)
// também consigam invalidar cache (ex: refletir ofensiva/contadores após
// responder uma questão).
export const queryClient = new QueryClient();
