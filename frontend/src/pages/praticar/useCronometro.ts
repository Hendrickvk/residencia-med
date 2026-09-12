import { useEffect, useRef, useState } from "react";

// Cronômetro por questão (REDESIGN.md §4.2): atualiza a cada 1s pra exibição
// (numerais tabulares, sem jitter), mas `tempoDecorridoMs()` lê o relógio
// direto — não espera o próximo tick — pra carimbar o tempo real de resposta.
export function useCronometro(chaveDeReset: unknown) {
  const inicioRef = useRef(Date.now());
  const [decorridoMs, setDecorridoMs] = useState(0);

  useEffect(() => {
    inicioRef.current = Date.now();
    setDecorridoMs(0);
    const id = setInterval(() => setDecorridoMs(Date.now() - inicioRef.current), 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveDeReset]);

  return {
    decorridoMs,
    tempoDecorridoMs: () => Date.now() - inicioRef.current,
  };
}
