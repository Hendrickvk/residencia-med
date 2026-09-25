import type { Me } from "./types";

// Identidade da conta: nome e cor do avatar. A cor vem da paleta compartilhada
// com as pastas (`lib/paleta.ts`, contexto "perfil") e não muda com o tema: é a
// cor da pessoa.

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
