import { API_URL } from "../lib/api";
import { desenhoDaMoldura } from "../lib/cosmeticos";
import type { Me } from "../lib/types";
import { corCheia } from "../lib/paleta";
import { inicial } from "../lib/perfil";
import { Tracos } from "./Tracos";

interface Props {
  me: Me | undefined;
  /** Lado em pixels. 36 na barra superior, 64 na tela de perfil. */
  tamanho?: number;
  className?: string;
  /** Id da moldura. Ela fica em volta do avatar, então a caixa cresce: o `tamanho`
   *  continua sendo o do círculo. Abaixo de uns 64px o desenho vira ruído, e a barra
   *  superior usa o anel de nível no lugar. */
  moldura?: string | null;
}

// A foto quando existe, a inicial sobre a cor escolhida quando não.
//
// A cor fica de fundo mesmo com foto: é o que aparece enquanto a imagem
// carrega, e o que sobra se ela falhar. A URL carrega a versão da foto, então
// trocar a foto troca a URL — o servidor pode mandar cachear por um ano sem
// que a nova demore a aparecer.
export function Avatar({ me, tamanho = 36, className = "", moldura }: Props) {
  // A letra vai na cor `on` do tom, e não em branco fixo: nos tons claros da
  // paleta o branco some.
  const estilo = {
    width: tamanho,
    height: tamanho,
    fontSize: Math.round(tamanho * 0.36),
    ...corCheia(me?.cor_perfil, "perfil"),
  };

  const circulo = (
    <span
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-pill border border-black/15 dark:border-white/15 font-bold ${className}`}
      style={estilo}
    >
      {me?.foto_versao ? (
        <img
          src={`${API_URL}/me/foto?v=${me.foto_versao}`}
          alt=""
          className="h-full w-full object-cover"
          draggable={false}
        />
      ) : (
        inicial(me)
      )}
    </span>
  );

  const tracos = moldura ? desenhoDaMoldura(moldura) : [];
  if (tracos.length === 0) return circulo;

  const caixa = Math.round(tamanho / 0.74);
  return (
    <span className="relative flex shrink-0 items-center justify-center text-ink" style={{ width: caixa, height: caixa }}>
      <svg
        viewBox="0 0 100 100"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className="absolute inset-0 h-full w-full overflow-visible"
      >
        <Tracos tracos={tracos} />
      </svg>
      {circulo}
    </span>
  );
}
