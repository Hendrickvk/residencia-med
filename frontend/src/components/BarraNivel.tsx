import { useEffect, useState } from "react";

interface Props {
  // Onde a barra termina, de 0 a 100.
  pct: number;
  // Onde a sessão começou. Com ele, o trecho rendido aparece em ouro e enche.
  de?: number;
  fina?: boolean;
  // Sem rótulo, a barra é só desenho do número que está ao lado dela.
  rotulo?: string;
}

// `scaleX` e não `width`: só transform anima, sem refazer o layout (DESIGN_TRIAGEM.md
// §3). Transição e não keyframe, porque a última resposta da fila pode chegar com a
// barra já enchendo, e a transição segue dali até o valor novo.
export function BarraNivel({ pct, de, fina = false, rotulo }: Props) {
  const [mostrado, setMostrado] = useState(de ?? pct);
  useEffect(() => {
    if (de === undefined) return;
    const espera = setTimeout(() => setMostrado(pct), 250);
    return () => clearTimeout(espera);
  }, [de, pct]);

  return (
    <span
      role={rotulo ? "img" : undefined}
      aria-label={rotulo}
      aria-hidden={rotulo ? undefined : true}
      className={`relative block overflow-hidden bg-line-soft ${fina ? "h-1 rounded-[2px]" : "h-2 rounded-[3px]"}`}
    >
      {de !== undefined && (
        <span
          className="absolute inset-0 origin-left bg-ouro transition-transform duration-cresce ease-suave"
          style={{ transform: `scaleX(${mostrado / 100})` }}
        />
      )}
      <span
        className="absolute inset-0 origin-left bg-ink"
        style={{ transform: `scaleX(${(de ?? pct) / 100})` }}
      />
    </span>
  );
}
