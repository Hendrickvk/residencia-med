import { useSyncExternalStore } from "react";
import type { Ganho, ResumoGanhos } from "./types";

// O que a sessão em curso rendeu, para o bloco do fim (RecompensaSessao). Fora do
// React como o `respostasQueue`, que é quem traz a maior parte destes ganhos: a
// última resposta da fila costuma chegar depois de o resumo abrir, e o bloco
// precisa se atualizar sozinho.
let ganhos: Ganho[] = [];
const ouvintes = new Set<() => void>();

function avisar() {
  ouvintes.forEach((ouvinte) => ouvinte());
}

export function registrarGanho(ganho: Ganho | null | undefined) {
  if (!ganho) return;
  ganhos = [...ganhos, ganho];
  avisar();
}

export function zerarGanhos() {
  if (ganhos.length === 0) return;
  ganhos = [];
  avisar();
}

export function useGanhos(): Ganho[] {
  return useSyncExternalStore(
    (ouvinte) => {
      ouvintes.add(ouvinte);
      return () => ouvintes.delete(ouvinte);
    },
    () => ganhos,
  );
}

// `null` quando não rendeu nada. Antes e depois pelo XP, e não pela ordem: os
// cartões vão sem esperar a resposta, e elas podem chegar trocadas.
export function resumirGanhos(lista: Ganho[]): ResumoGanhos | null {
  if (lista.length === 0) return null;
  const porArea = new Map<string, number>();
  for (const ganho of lista) {
    for (const [nome, xp] of Object.entries(ganho.areas)) porArea.set(nome, (porArea.get(nome) ?? 0) + xp);
  }
  return {
    xp: lista.reduce((soma, ganho) => soma + ganho.xp, 0),
    moedas: lista.reduce((soma, ganho) => soma + ganho.moedas, 0),
    areas: [...porArea.entries()].map(([nome, xp]) => ({ nome, xp })).sort((a, b) => b.xp - a.xp),
    antes: lista.reduce((menor, ganho) => (ganho.antes.xp < menor.xp ? ganho.antes : menor), lista[0].antes),
    depois: lista.reduce((maior, ganho) => (ganho.depois.xp > maior.xp ? ganho.depois : maior), lista[0].depois),
  };
}

// O resultado do simulado abre logo depois do finalizar, numa tela que não vê a
// resposta dele. Recarregando a página isto se perde, e o resultado mostra só o
// total que o servidor guardou (`simulados.xp_ganho`).
const ganhosDeProva = new Map<number, Ganho[]>();

export function guardarGanhosDeProva(simuladoId: number, lista: Ganho[]) {
  ganhosDeProva.set(simuladoId, lista);
}

export function lerGanhosDeProva(simuladoId: number): Ganho[] | undefined {
  return ganhosDeProva.get(simuladoId);
}
