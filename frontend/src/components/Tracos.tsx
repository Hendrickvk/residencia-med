import type { TemaDoPerfil, TracoMoldura } from "../lib/cosmeticos";

function estiloDoMovimento(t: TracoMoldura): React.CSSProperties | undefined {
  if (t.atraso !== undefined) return { animationDelay: `${t.atraso}s` };
  if (!t.movimento) return undefined;
  const { segundos, centro, atraso } = t.movimento;
  return {
    animationDuration: `${segundos}s`,
    animationDelay: atraso ? `${atraso}s` : undefined,
    transformOrigin: centro ? `${centro[0]}px ${centro[1]}px` : undefined,
  };
}

// O desenho de uma moldura ou de uma cena. O SVG em volta é de quem chama.
export function Tracos({ tracos }: { tracos: TracoMoldura[] }) {
  return tracos.map((t, i) => {
    const preenchido = t.largura === undefined;
    let classe: string | undefined;
    if (t.atraso !== undefined) classe = "brilho-folha";
    else if (t.movimento) classe = `moldura-${t.movimento.nome}`;
    return (
      <path
        key={i}
        d={t.d}
        strokeWidth={t.largura}
        strokeDasharray={t.tracejado}
        stroke={preenchido ? "none" : t.cor ?? (t.ouro ? "var(--ouro)" : "currentColor")}
        fill={t.preenche ?? (preenchido ? t.cor : "none")}
        opacity={t.opacidade}
        className={classe}
        style={estiloDoMovimento(t)}
      />
    );
  });
}

// A cena do tema enche a caixa de quem chama, que precisa ser `relative overflow-hidden`.
export function CenaDoTema({ tema }: { tema: TemaDoPerfil }) {
  return (
    <svg
      viewBox="0 0 300 104"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      strokeLinecap="round"
      aria-hidden="true"
      className="absolute inset-0 h-full w-full"
    >
      <Tracos tracos={tema.cena} />
    </svg>
  );
}
