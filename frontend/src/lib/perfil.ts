import type { Me } from "./types";

// Identidade da conta: nome e cor do avatar. A cor **não** sai da escala de
// triagem (DESIGN_TRIAGEM.md §2) — t1–t5 significam nível de aproveitamento, e
// um avatar verde leria como "vai bem". Os matizes da escala ficam de fora.
//
// As classes são escritas por extenso porque o Tailwind só gera o que encontra
// literal no código: `bg-perfil-${cor}` montado em tempo de execução não
// existiria no CSS (mesma armadilha do CLASSES_NIVEL, em `triagem.ts`).
export const CORES_PERFIL = [
  { chave: "grafite", nome: "Grafite", fundo: "bg-perfil-grafite" },
  { chave: "ardosia", nome: "Ardósia", fundo: "bg-perfil-ardosia" },
  { chave: "ameixa", nome: "Ameixa", fundo: "bg-perfil-ameixa" },
  { chave: "rosa", nome: "Rosa", fundo: "bg-perfil-rosa" },
  { chave: "turquesa", nome: "Turquesa", fundo: "bg-perfil-turquesa" },
  { chave: "cafe", nome: "Café", fundo: "bg-perfil-cafe" },
] as const;

export const COR_PADRAO = "grafite";

export function fundoDaCor(chave: string | undefined): string {
  return CORES_PERFIL.find((c) => c.chave === chave)?.fundo ?? "bg-perfil-grafite";
}

/** Como a conta se chama na tela: o nome, ou o e-mail enquanto não houver um. */
export function nomeExibido(me: Me | undefined): string {
  return me?.nome?.trim() || me?.email || "";
}

/** A letra do avatar. Do nome quando existe — a inicial do e-mail é uma letra
 *  que a pessoa não escolheu. */
export function inicial(me: Me | undefined): string {
  const base = nomeExibido(me);
  return base ? base[0].toUpperCase() : "?";
}
