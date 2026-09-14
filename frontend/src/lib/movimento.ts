import { useEffect, useRef, useState } from "react";

// Movimento da interface (DESIGN_TRIAGEM.md §3). As animações em si são
// classes do Tailwind (`animate-entrar`, `animate-surgir`...); aqui fica só o
// que precisa de JavaScript.

export function prefereMenosMovimento(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Duração de `animate-sumir` / `animate-desvanecer-saida` (tailwind.config.js).
const SAIDA_MS = 160;

// Mantém uma camada (menu, diálogo) montada durante a animação de saída.
// `saindo` diz qual classe usar: entrada enquanto aberta, saída ao fechar.
export function usePresenca(aberto: boolean) {
  const [montado, setMontado] = useState(aberto);
  if (aberto && !montado) setMontado(true);

  useEffect(() => {
    if (aberto || !montado) return;
    const timer = setTimeout(() => setMontado(false), SAIDA_MS);
    return () => clearTimeout(timer);
  }, [aberto, montado]);

  return { montado: aberto || montado, saindo: !aberto && montado };
}

// Último valor exibido de cada contador, por sessão da aba: voltar ao Painel
// depois de uma sessão anima o número do valor antigo até o novo, e voltar
// sem mudança nenhuma não reanima nada.
const ultimoExibido = new Map<string, number>();

// Número que conta até `valor`. Sem `chave`, parte sempre do zero.
export function useContagem(valor: number, chave?: string, duracaoMs = 900): number {
  const inicio = chave !== undefined ? (ultimoExibido.get(chave) ?? 0) : 0;
  const [exibido, setExibido] = useState(() => (prefereMenosMovimento() ? valor : inicio));
  const exibidoRef = useRef(exibido);

  useEffect(() => {
    const de = exibidoRef.current;
    if (chave !== undefined) ultimoExibido.set(chave, valor);
    if (de === valor || prefereMenosMovimento()) {
      exibidoRef.current = valor;
      setExibido(valor);
      return;
    }
    const t0 = performance.now();
    let quadro = 0;
    function passo(agora: number) {
      const t = Math.min(1, (agora - t0) / duracaoMs);
      // Desacelera no fim (ease-out cúbico), como a curva `suave`.
      const atual = de + (valor - de) * (1 - (1 - t) ** 3);
      exibidoRef.current = atual;
      setExibido(atual);
      if (t < 1) quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [valor, chave, duracaoMs]);

  return exibido;
}

// Leva o topo da página à vista ao trocar de caso: sem isso, depois de ler uma
// discussão longa o próximo caso abria no meio.
export function rolarParaTopo() {
  if (window.scrollY === 0) return;
  window.scrollTo({ top: 0, behavior: prefereMenosMovimento() ? "auto" : "smooth" });
}

// Atraso de escalonamento para listas que entram em sequência, com teto para
// uma lista longa não demorar a aparecer inteira.
export function atraso(indice: number, passoMs = 35, tetoMs = 420): React.CSSProperties {
  return { animationDelay: `${Math.min(indice * passoMs, tetoMs)}ms` };
}
