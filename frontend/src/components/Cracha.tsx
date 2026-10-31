import { corCheia } from "../lib/paleta";
import { nomeExibido } from "../lib/perfil";
import type { Me } from "../lib/types";
import { Avatar } from "./Avatar";

interface Props {
  me: Me | undefined;
  nivel: number;
  patente: string;
}

// O crachá é a identidade da aluna na progressão (DESIGN_TRIAGEM.md §6): a faixa na
// cor dela, a fenda do cordão, patente e nível. A cor não muda com o tema, e o nome
// quebra onde precisar, porque quem não tem nome aparece aqui com o e-mail inteiro.
export function Cracha({ me, nivel, patente }: Props) {
  const nome = nomeExibido(me);
  return (
    <article
      aria-label={`Crachá de ${nome}: nível ${nivel}, ${patente}`}
      className="w-full max-w-[300px] overflow-hidden rounded-caso border border-line bg-surface"
    >
      <div className="flex h-[104px] flex-col items-center gap-3.5 pt-3.5" style={corCheia(me?.cor_perfil, "perfil")}>
        <span className="h-2.5 w-[52px] rounded-pill bg-ground" aria-hidden="true" />
        <span className="marca-texto text-[17px]">Conduta</span>
      </div>
      <div className="-mt-10 flex flex-col items-center gap-3.5 px-5 pb-5 text-center">
        <span className="rounded-pill bg-surface p-1">
          <Avatar me={me} tamanho={84} />
        </span>
        <span className="w-full text-subtitulo [overflow-wrap:anywhere]">{nome}</span>
        <div className="grid w-full grid-cols-2 border-y border-line-soft">
          <div className="flex flex-col gap-1 border-r border-line-soft py-3">
            <span className="rotulo text-muted">Patente</span>
            <span className="flex min-h-8 items-center justify-center text-bloco">{patente}</span>
          </div>
          <div className="flex flex-col gap-1 py-3">
            <span className="rotulo text-muted">Nível</span>
            <span className="num-md">{nivel}</span>
          </div>
        </div>
        <span className="cracha-barras block h-7 w-full" aria-hidden="true" />
      </div>
    </article>
  );
}
