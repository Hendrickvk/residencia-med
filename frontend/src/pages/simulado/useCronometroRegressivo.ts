import { useEffect, useRef, useState } from "react";

// Cronômetro regressivo do Simulado (REDESIGN.md §4.3) — calcula a partir
// de `iniciado_em` (não de um contador local) pra sobreviver a um reload
// da aba sem perder a conta do tempo real decorrido.
export function useCronometroRegressivo(iniciadoEm: string, tempoLimiteMin: number, onEsgotado: () => void) {
  const onEsgotadoRef = useRef(onEsgotado);
  onEsgotadoRef.current = onEsgotado;
  const disparadoRef = useRef(false);

  function calcular() {
    const limiteSeg = tempoLimiteMin * 60;
    const decorridoSeg = (Date.now() - new Date(iniciadoEm).getTime()) / 1000;
    return Math.max(0, Math.round(limiteSeg - decorridoSeg));
  }

  const [restanteSeg, setRestanteSeg] = useState(calcular);

  useEffect(() => {
    const id = setInterval(() => {
      const r = calcular();
      setRestanteSeg(r);
      if (r <= 0 && !disparadoRef.current) {
        disparadoRef.current = true;
        onEsgotadoRef.current();
      }
    }, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [iniciadoEm, tempoLimiteMin]);

  return restanteSeg;
}
