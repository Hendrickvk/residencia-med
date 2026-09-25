import { Play, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { type BaralhoResumo, plural } from "../../lib/cartoes";
import { corDeFundo, veuDaPasta } from "../../lib/paleta";

interface Props {
  baralho: BaralhoResumo;
  cor: string;
  onApagar: () => void;
}

// O baralho é um maço, não uma linha de tabela: as bordas dos cartões de trás
// aparecem acima do bloco, e a faixa do topo é a cor da pasta.
//
// A pilha só é desenhada quando há mais de um cartão — um maço de um cartão só
// seria mentira, e a tela inteira depende de a metáfora ser honesta.
//
// A barra usa os mesmos três estágios da Revisão de casos — novo, aprendendo,
// consolidado (21 dias, o corte "mature" do Anki). É informação, não enfeite:
// um baralho todo claro é um baralho que ela ainda não estudou.
export function CartaoBaralho({ baralho: b, cor, onApagar }: Props) {
  const total = Math.max(b.cartoes, 1);
  const faixas = [
    { chave: "consolidados", n: b.consolidados, classe: "bg-ink" },
    { chave: "aprendendo", n: b.aprendendo, classe: "bg-muted" },
    { chave: "novos", n: b.novos, classe: "bg-line" },
  ];

  return (
    <div className="relative pt-2.5">
      {b.cartoes > 1 && (
        <>
          <span
            className="absolute inset-x-5 top-0 h-3 rounded-t-caso border border-b-0 border-line bg-surface opacity-50"
            aria-hidden="true"
          />
          <span
            className="absolute inset-x-2.5 top-1.5 h-3 rounded-t-caso border border-b-0 border-line bg-surface"
            aria-hidden="true"
          />
        </>
      )}

      <div className="group relative flex flex-col overflow-hidden rounded-caso border border-line bg-surface transition duration-hover ease-brand hover:border-muted">
        <div className="flex items-center gap-2.5 border-b border-line px-4 py-3" style={veuDaPasta(cor)}>
          <span className="h-2.5 w-2.5 shrink-0 rounded-pill" style={corDeFundo(cor, "pasta")} aria-hidden="true" />
          {/* O link cobre o cartão inteiro (`after:inset-0`): mirar só o texto
              num toque de celular é pedir precisão que ninguém tem. */}
          <Link
            to={`/baralhos/${b.id}`}
            className="min-w-0 flex-1 truncate text-bloco text-ink after:absolute after:inset-0 after:content-['']"
          >
            {b.nome}
          </Link>
          <button
            type="button"
            onClick={onApagar}
            aria-label={`Apagar ${b.nome}`}
            // z-10 para ficar acima da área clicável do link. Sem ponteiro que
            // passe por cima (toque), sempre visível: escondida, ela continuava
            // tocável e um toque no canto do baralho abria o "Apagar".
            className="relative z-10 shrink-0 rounded-btn p-1 text-faint opacity-0 transition duration-hover hover:text-t1 focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
          >
            <Trash2 size={14} strokeWidth={2} />
          </button>
        </div>

        <div className="flex flex-col gap-3 p-4">
          <div className="flex items-end gap-2">
            {/* O número grande é o que ela procura ao abrir a tela. */}
            <span className="text-titulo tabular-nums leading-none text-ink">{b.vencidos}</span>
            <span className="pb-1 text-apoio text-muted">para hoje</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="flex h-1.5 overflow-hidden rounded-pill bg-line-soft" aria-hidden="true">
              {faixas.map((f) => (
                <span
                  key={f.chave}
                  className={`${f.classe} transition-[width] duration-cresce ease-suave`}
                  style={{ width: `${(f.n / total) * 100}%` }}
                />
              ))}
            </div>
            <span className="text-apoio text-muted">
              {plural(b.cartoes)}
              {b.consolidados > 0 && ` · ${b.consolidados} na memória`}
            </span>
          </div>

          {b.vencidos > 0 ? (
            <Link
              to={`/baralhos/${b.id}?estudar=1`}
              className="relative z-10 flex items-center justify-center gap-1.5 rounded-btn bg-ink px-3 py-2 text-apoio font-semibold text-onink transition duration-hover ease-brand hover:opacity-90 active:scale-[0.97]"
            >
              <Play size={14} strokeWidth={2} />
              Estudar
            </Link>
          ) : (
            <span className="flex items-center justify-center rounded-btn border border-line px-3 py-2 text-apoio text-faint">
              Tudo em dia
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
