import { API_URL } from "./api";

// Erros do app vão para o servidor (`POST /me/erros`, tela "Uso da plataforma"
// do admin). Antes ficavam só no console, e num celular não há console à mão.
// `fetch` cru, e não o `api`: o `api` manda para o login num 401, e um relato
// de erro não pode tirar ninguém da tela. Sem sessão o servidor recusa e o
// relato se perde, de propósito.

// Por carga da página: a mesma mensagem uma vez só, e no máximo cinco — um laço
// de erro não pode virar uma rajada de requisições.
const enviados = new Set<string>();
const MAXIMO_POR_PAGINA = 5;

// Ruído de navegador que não é defeito do app.
const IGNORAR = [/ResizeObserver loop/i, /^Script error\.?$/i];

export function relatarErro(mensagem: string, pilha?: string) {
  const texto = (mensagem || "Erro sem mensagem").slice(0, 500);
  if (enviados.size >= MAXIMO_POR_PAGINA || enviados.has(texto) || IGNORAR.some((r) => r.test(texto))) return;
  enviados.add(texto);
  void fetch(`${API_URL}/me/erros`, {
    method: "POST",
    credentials: "include",
    // Sobrevive à página sendo fechada logo depois do erro.
    keepalive: true,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensagem: texto, pilha: pilha?.slice(0, 4000), url: location.pathname.slice(0, 300) }),
  }).catch(() => {});
}

export function capturarErros() {
  window.addEventListener("error", (e) => relatarErro(e.message, e.error instanceof Error ? e.error.stack : undefined));
  window.addEventListener("unhandledrejection", (e) => {
    const motivo = e.reason;
    relatarErro(motivo instanceof Error ? motivo.message : String(motivo), motivo instanceof Error ? motivo.stack : undefined);
  });
}
