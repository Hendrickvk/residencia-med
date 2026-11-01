import { useEffect, useState } from "react";
import { ApiError, api, esperarOuConexao, recusaDefinitiva } from "./api";
import { registrarGanho } from "./ganhos";
import { queryClient } from "./queryClient";
import type { Ganho, Me, RespostaPayload } from "./types";

/**
 * MIGRACAO.md §2: "POST /respostas é fire-and-forget do ponto de vista da
 * interface: o cliente não espera a resposta para mostrar o feedback.
 * Enfileire as gravações e trate falha com retry silencioso e um aviso
 * discreto se a fila não drenar." O feedback em si nunca depende desta
 * fila — ele já foi mostrado localmente comparando com o gabarito embutido
 * na sessão, antes desta função sequer ser chamada.
 *
 * Até 31/10 a fila vivia só na memória e desistia depois de 6 tentativas: uns minutos
 * sem sinal, ou a aba fechada, e a resposta sumia sem aviso. Agora fica no `localStorage`
 * até o servidor confirmar, por conta (o navegador entra em mais de uma), e só sai antes
 * disso se o servidor recusar de vez. Cada resposta leva um `envio`: se a volta se
 * perdeu com a resposta já gravada, repetir não grava de novo.
 */

const ESPERA_MAXIMA_MS = 30_000;

interface ItemFila {
  envio: string;
  payload: RespostaPayload;
}

const fila: ItemFila[] = [];
let processando = false;
const ouvintes = new Set<(pendentes: number) => void>();

const chave = (usuarioId: number) => `conduta:respostas:${usuarioId}`;

function contaAtual() {
  return queryClient.getQueryData<Me>(["me"])?.id;
}

function lerGuardados(usuarioId: number): ItemFila[] {
  try {
    return JSON.parse(localStorage.getItem(chave(usuarioId)) ?? "[]");
  } catch {
    return [];
  }
}

// Sempre relê antes de escrever: outra aba pode ter guardado as dela.
function alterarGuardados(usuarioId: number | undefined, mudar: (itens: ItemFila[]) => ItemFila[]) {
  if (usuarioId === undefined) return;
  try {
    const itens = mudar(lerGuardados(usuarioId));
    if (itens.length) localStorage.setItem(chave(usuarioId), JSON.stringify(itens));
    else localStorage.removeItem(chave(usuarioId));
  } catch {
    // Sem armazenamento (janela privada), segue só na memória.
  }
}

function notificar() {
  ouvintes.forEach((ouvinte) => ouvinte(fila.length));
}

async function processar() {
  if (processando) return;
  processando = true;
  const usuarioId = contaAtual();
  while (fila.length > 0) {
    const item = fila[0];
    let tentativas = 0;
    for (;;) {
      try {
        const resposta = await api.post<{ ganho: Ganho | null }>("/respostas", { ...item.payload, envio: item.envio });
        registrarGanho(resposta.ganho);
        // Ofensiva/contadores no topbar (`/me`) dependem de respostas
        // recém-gravadas — sem isso ficam presos ao valor de antes da sessão
        // até o staleTime da query expirar por conta própria.
        void queryClient.invalidateQueries({ queryKey: ["me"] });
        break;
      } catch (erro) {
        if (recusaDefinitiva(erro)) break;
        // Sessão vencida: repetir não adianta. Fica guardada para quando ela entrar.
        if (erro instanceof ApiError && erro.status === 401) {
          fila.length = 0;
          processando = false;
          notificar();
          return;
        }
        tentativas += 1;
        await esperarOuConexao(Math.min(2 ** tentativas * 500, ESPERA_MAXIMA_MS));
      }
    }
    fila.shift();
    alterarGuardados(usuarioId, (itens) => itens.filter((i) => i.envio !== item.envio));
    notificar();
  }
  processando = false;
}

export function enfileirarResposta(payload: RespostaPayload) {
  const item = { envio: crypto.randomUUID(), payload };
  fila.push(item);
  alterarGuardados(contaAtual(), (itens) => [...itens, item]);
  notificar();
  void processar();
}

/** Ao abrir o app: o que ficou de uma aba fechada ou de antes de a sessão vencer. Se outra
 * aba estiver enviando o mesmo item, o `envio` impede a gravação dobrada. */
export function retomarRespostas() {
  const usuarioId = contaAtual();
  if (usuarioId === undefined) return;
  const naFila = new Set(fila.map((i) => i.envio));
  const novos = lerGuardados(usuarioId).filter((i) => !naFila.has(i.envio));
  if (!novos.length) return;
  fila.push(...novos);
  notificar();
  void processar();
}

export function useRespostasPendentes(): number {
  const [pendentes, setPendentes] = useState(fila.length);
  useEffect(() => {
    ouvintes.add(setPendentes);
    return () => {
      ouvintes.delete(setPendentes);
    };
  }, []);
  return pendentes;
}
