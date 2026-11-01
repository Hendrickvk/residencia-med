import { useEffect, useRef, useState } from "react";

// Cronômetro por questão (REDESIGN.md §4.2): atualiza a cada 1s pra exibição
// (numerais tabulares, sem jitter), mas `tempoDecorridoMs()` lê o relógio
// direto — não espera o próximo tick — pra carimbar o tempo real de resposta.
// `inicialMs` é o que já tinha passado antes de a tela abrir, numa sessão retomada. Vale
// só para a primeira chave: o caso seguinte começa do zero.
export function useCronometro(chaveDeReset: unknown, inicialMs = 0) {
  const inicioRef = useRef(Date.now() - inicialMs);
  const ultimaChave = useRef(chaveDeReset);
  const [decorridoMs, setDecorridoMs] = useState(inicialMs);

  useEffect(() => {
    if (ultimaChave.current !== chaveDeReset) {
      ultimaChave.current = chaveDeReset;
      inicioRef.current = Date.now();
      setDecorridoMs(0);
    }
    const id = setInterval(() => setDecorridoMs(Date.now() - inicioRef.current), 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveDeReset]);

  return {
    decorridoMs,
    tempoDecorridoMs: () => Date.now() - inicioRef.current,
  };
}
