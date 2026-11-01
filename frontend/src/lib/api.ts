import { queryClient } from "./queryClient";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** O servidor recusou de vez: tentar de novo dá o mesmo. 401 fica de fora (ela entra de
 * novo e a fila continua), e 408 e 429 passam com o tempo. */
export function recusaDefinitiva(erro: unknown) {
  return erro instanceof ApiError && erro.status >= 400 && erro.status < 500 && ![401, 408, 429].includes(erro.status);
}

/** Espera antes de tentar de novo, e acaba antes se a conexão voltar. */
export function esperarOuConexao(ms: number) {
  return new Promise<void>((resolve) => {
    const fim = () => {
      clearTimeout(timer);
      window.removeEventListener("online", fim);
      resolve();
    };
    const timer = setTimeout(fim, ms);
    window.addEventListener("online", fim);
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include", // envia/recebe o cookie httpOnly de sessão
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    // Sem isto, uma conexão que pendura deixava a tela esperando para sempre.
    signal: AbortSignal.timeout?.(60_000),
    ...init,
  });
  if (!res.ok) {
    // Sessão revogada ou expirada em QUALQUER requisição, não só no /me: antes
    // disto o `/me` era a única porta de autenticação, e um 401 no meio de uma
    // sessão de estudo aparecia como "pode ser a conexão", com um "Tentar de
    // novo" que ia falhar para sempre. Invalidar o ["me"] faz o `RequireAuth`
    // reperguntar e mandar para o login. Fora do React de propósito — é o
    // mesmo caminho que o `respostasQueue` já usa. `/auth/*` fica de fora:
    // senha errada no login é 401 e não tem sessão nenhuma a derrubar. O próprio
    // `/me` também: invalidar a consulta que está em curso a cancela e pergunta
    // de novo, e a aba repetia o `/me` sem parar, sem nunca chegar ao login.
    if (res.status === 401 && !path.startsWith("/auth/") && path !== "/me") {
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    }
    const corpo = await res.json().catch(() => ({}));
    const detalhe = Array.isArray(corpo.detail)
      ? corpo.detail.map((d: { msg?: string }) => d.msg).join("; ")
      : corpo.detail;
    throw new ApiError(res.status, detalhe || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function comQuery(path: string, params?: Record<string, unknown>): string {
  if (!params) return path;
  const usp = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== null && valor !== "") usp.set(chave, String(valor));
  }
  const qs = usp.toString();
  return qs ? `${path}?${qs}` : path;
}

export const api = {
  get: <T>(path: string, params?: Record<string, unknown>) => request<T>(comQuery(path, params)),
  post: <T>(path: string, data?: unknown, init?: RequestInit) =>
    request<T>(path, { method: "POST", body: data !== undefined ? JSON.stringify(data) : undefined, ...init }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data) }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
