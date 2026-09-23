import { queryClient } from "./queryClient";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include", // envia/recebe o cookie httpOnly de sessão
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    // Sessão revogada ou expirada em QUALQUER requisição, não só no /me: antes
    // disto o `/me` era a única porta de autenticação, e um 401 no meio de uma
    // sessão de estudo aparecia como "pode ser a conexão", com um "Tentar de
    // novo" que ia falhar para sempre. Invalidar o ["me"] faz o `RequireAuth`
    // reperguntar e mandar para o login. Fora do React de propósito — é o
    // mesmo caminho que o `respostasQueue` já usa. `/auth/*` fica de fora:
    // senha errada no login é 401 e não tem sessão nenhuma a derrubar.
    if (res.status === 401 && !path.startsWith("/auth/")) {
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
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
