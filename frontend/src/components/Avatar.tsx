import { API_URL } from "../lib/api";
import type { Me } from "../lib/types";
import { fundoDaCor, inicial } from "../lib/perfil";

interface Props {
  me: Me | undefined;
  /** Lado em pixels. 36 na barra superior, 64 na tela de perfil. */
  tamanho?: number;
  className?: string;
}

// A foto quando existe, a inicial sobre a cor escolhida quando não.
//
// A cor fica de fundo mesmo com foto: é o que aparece enquanto a imagem
// carrega, e o que sobra se ela falhar. A URL carrega a versão da foto, então
// trocar a foto troca a URL — o servidor pode mandar cachear por um ano sem
// que a nova demore a aparecer.
export function Avatar({ me, tamanho = 36, className = "" }: Props) {
  const estilo = { width: tamanho, height: tamanho, fontSize: Math.round(tamanho * 0.36) };

  return (
    <span
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-pill font-bold text-white ${fundoDaCor(
        me?.cor_perfil,
      )} ${className}`}
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
}
