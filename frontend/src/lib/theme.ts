const STORAGE_KEY = "residencia-med:tema";

export type Tema = "light" | "dark";

export function temaInicial(): Tema {
  const salvo = localStorage.getItem(STORAGE_KEY);
  if (salvo === "light" || salvo === "dark") return salvo;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Distingue "só caiu no padrão do sistema" de "já existe uma preferência
// concreta" (local ou já sincronizada do backend) — sem isso, todo reload
// reaplicaria o tema da conta e ignoraria uma escolha manual no navegador.
export function temaJaTemPreferencia(): boolean {
  return localStorage.getItem(STORAGE_KEY) !== null;
}

export function aplicarTema(tema: Tema) {
  document.documentElement.classList.toggle("dark", tema === "dark");
}

export function persistirTema(tema: Tema) {
  localStorage.setItem(STORAGE_KEY, tema);
}
