import { useEffect, useState } from "react";
import { api } from "./api";
import { queryClient } from "./queryClient";
import type { RespostaPayload } from "./types";

/**
 * MIGRACAO.md §2: "POST /respostas é fire-and-forget do ponto de vista da
 * interface: o cliente não espera a resposta para mostrar o feedback.
 * Enfileire as gravações e trate falha com retry silencioso e um aviso
 * discreto se a fila não drenar." O feedback em si nunca depende desta
 * fila — ele já foi mostrado localmente comparando com o gabarito embutido
 * na sessão, antes desta função sequer ser chamada.
 */

const MAX_TENTATIVAS = 6;
const fila: RespostaPayload[] = [];
let processando = false;
const ouvintes = new Set<(pendentes: number) => void>();

function notificar() {
  ouvintes.forEach((ouvinte) => ouvinte(fila.length));
}

function esperar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function processar() {
  if (processando) return;
  processando = true;
  while (fila.length > 0) {
    const payload = fila[0];
    let tentativas = 0;
    let enviado = false;
    while (tentativas < MAX_TENTATIVAS && !enviado) {
      try {
        await api.post("/respostas", payload);
        enviado = true;
        // Ofensiva/contadores no topbar (`/me`) dependem de respostas
        // recém-gravadas — sem isso ficam presos ao valor de antes da sessão
        // até o staleTime da query expirar por conta própria.
        void queryClient.invalidateQueries({ queryKey: ["me"] });
      } catch {
        tentativas += 1;
        if (tentativas < MAX_TENTATIVAS) {
          await esperar(Math.min(2 ** tentativas * 500, 8000));
        }
      }
    }
    // Desiste só deste item depois de várias tentativas (ex: sessão expirou)
    // — não trava a fila inteira por causa de uma gravação problemática.
    fila.shift();
    notificar();
  }
  processando = false;
}

export function enfileirarResposta(payload: RespostaPayload) {
  fila.push(payload);
  notificar();
  void processar();
}

export function usarRespostasPendentes(): number {
  const [pendentes, setPendentes] = useState(fila.length);
  useEffect(() => {
    ouvintes.add(setPendentes);
    return () => {
      ouvintes.delete(setPendentes);
    };
  }, []);
  return pendentes;
}
