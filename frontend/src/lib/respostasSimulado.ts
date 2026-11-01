import { useEffect, useState } from "react";
import { ApiError, esperarOuConexao, recusaDefinitiva } from "./api";
import { responderSimulado } from "./simulados";

/**
 * As respostas de uma prova a caminho do servidor. Até 31/10 a tela marcava a alternativa
 * e ignorava a falha do envio: com a rede ruim, a prova inteira podia sair em branco com
 * tudo marcado na tela.
 *
 * Uma entrada por questão, e não uma fila de envios: trocar de alternativa substitui o que
 * esperava, então a última escolha é a que fica, sem chegar fora de ordem. Fica no
 * `localStorage` até o servidor confirmar, para sobreviver à aba fechada. A resposta é dela
 * e o gabarito não está aqui, então não há o que vazar. Outra conta no mesmo navegador não
 * grava por cima: o servidor recusa a prova que não é dela.
 */

const ESPERA_MAXIMA_MS = 15_000;

type Pendentes = Record<number, string>;

interface Fila {
  pendentes: Pendentes;
  rodando: boolean;
  falhas: number;
  ouvintes: Set<() => void>;
}

const filas = new Map<number, Fila>();

const chave = (simuladoId: number) => `conduta:simulado:${simuladoId}:pendentes`;

function ler(simuladoId: number): Pendentes {
  try {
    return JSON.parse(localStorage.getItem(chave(simuladoId)) ?? "{}");
  } catch {
    return {};
  }
}

function filaDe(simuladoId: number) {
  let fila = filas.get(simuladoId);
  if (!fila) {
    fila = { pendentes: ler(simuladoId), rodando: false, falhas: 0, ouvintes: new Set() };
    filas.set(simuladoId, fila);
  }
  return fila;
}

function guardar(simuladoId: number, fila: Fila) {
  try {
    if (Object.keys(fila.pendentes).length) localStorage.setItem(chave(simuladoId), JSON.stringify(fila.pendentes));
    else localStorage.removeItem(chave(simuladoId));
  } catch {
    // Sem armazenamento (janela privada), segue só na memória.
  }
}

function avisar(fila: Fila) {
  fila.ouvintes.forEach((ouvinte) => ouvinte());
}

async function rodar(simuladoId: number) {
  const fila = filaDe(simuladoId);
  if (fila.rodando) return;
  fila.rodando = true;
  try {
    for (;;) {
      const proxima = Object.keys(fila.pendentes)[0];
      if (proxima === undefined) return;
      const questaoId = Number(proxima);
      const letra = fila.pendentes[questaoId];
      try {
        await responderSimulado(simuladoId, questaoId, letra);
        fila.falhas = 0;
      } catch (erro) {
        if (!recusaDefinitiva(erro)) {
          fila.falhas += 1;
          avisar(fila);
          // Sessão vencida: repetir não adianta. Ao entrar de novo, a tela retoma.
          if (erro instanceof ApiError && erro.status === 401) return;
          await esperarOuConexao(Math.min(1000 * 2 ** fila.falhas, ESPERA_MAXIMA_MS));
          continue;
        }
        // Recusa de vez (prova já finalizada ou de outra conta): não há o que reenviar.
        fila.falhas = 0;
      }
      // Se ela trocou de alternativa durante o envio, a nova ainda precisa ir.
      if (fila.pendentes[questaoId] === letra) {
        delete fila.pendentes[questaoId];
        guardar(simuladoId, fila);
      }
      avisar(fila);
    }
  } finally {
    fila.rodando = false;
  }
}

export function enviarRespostaSimulado(simuladoId: number, questaoId: number, letra: string) {
  const fila = filaDe(simuladoId);
  fila.pendentes[questaoId] = letra;
  guardar(simuladoId, fila);
  avisar(fila);
  void rodar(simuladoId);
}

/** O que ficou guardado de antes, para a tela mostrar e a fila voltar a enviar. */
export function retomarRespostasSimulado(simuladoId: number) {
  void rodar(simuladoId);
  return { ...filaDe(simuladoId).pendentes };
}

/** Espera a fila acabar ou falhar de novo. Devolve quantas ainda não foram. */
export function esvaziarRespostasSimulado(simuladoId: number) {
  const fila = filaDe(simuladoId);
  const contar = () => Object.keys(fila.pendentes).length;
  if (!contar()) return Promise.resolve(0);
  const falhasAntes = fila.falhas;
  return new Promise<number>((resolve) => {
    const ouvinte = () => {
      if (contar() && fila.falhas <= falhasAntes) return;
      fila.ouvintes.delete(ouvinte);
      resolve(contar());
    };
    fila.ouvintes.add(ouvinte);
    void rodar(simuladoId);
  });
}

/** `comFalha` só depois de uma falha de verdade: o envio normal dura milissegundos, e
 * cada resposta piscaria na tela. */
export function useRespostasSimuladoPendentes(simuladoId: number) {
  const [estado, setEstado] = useState(() => {
    const fila = filaDe(simuladoId);
    return { pendentes: { ...fila.pendentes }, comFalha: fila.falhas > 0 };
  });
  useEffect(() => {
    const fila = filaDe(simuladoId);
    const ouvinte = () => setEstado({ pendentes: { ...fila.pendentes }, comFalha: fila.falhas > 0 });
    fila.ouvintes.add(ouvinte);
    ouvinte();
    return () => {
      fila.ouvintes.delete(ouvinte);
    };
  }, [simuladoId]);
  return estado;
}
