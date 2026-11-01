import { Lock } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Avatar } from "../../components/Avatar";
import { ApiError } from "../../lib/api";
import { BOTAO_PEQUENO } from "../../lib/estilos";
import { equiparItem } from "../../lib/progresso";
import type { Me, Progresso } from "../../lib/types";

interface Props {
  me: Me | undefined;
  nivel: number;
  patentes: Progresso["patentes"];
}

const AVATAR = 48;
// A caixa com a moldura (Avatar.tsx); o fio da trilha passa na metade dela.
const CAIXA = Math.round(AVATAR / 0.74);

export function TrilhaNiveis({ me, nivel, patentes }: Props) {
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const trilha = useRef<HTMLOListElement>(null);
  const atual = useRef<HTMLLIElement>(null);
  const emUso = me?.equipados?.moldura ?? null;

  // No celular a trilha corre de lado: abre com a patente atual à vista. Só na horizontal,
  // porque `scrollIntoView` também rolaria a página até aqui.
  useEffect(() => {
    if (!trilha.current || !atual.current) return;
    trilha.current.scrollLeft = atual.current.offsetLeft - (trilha.current.clientWidth - atual.current.offsetWidth) / 2;
  }, []);

  async function usar(id: string | null) {
    setErro(null);
    setOcupado(true);
    try {
      await equiparItem("moldura", id);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não deu para trocar agora.");
    } finally {
      setOcupado(false);
    }
  }

  const indiceAtual = patentes.reduce((ultimo, p, i) => (nivel >= p.nivel ? i : ultimo), 0);

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-bloco">Trilha de níveis</h2>
      {erro && (
        <p role="alert" className="text-apoio font-medium text-t1">
          {erro}
        </p>
      )}
      <ol
        ref={trilha}
        className="relative flex overflow-x-auto rounded-caso border border-line bg-surface px-2 py-4 lg:grid lg:grid-cols-8 lg:overflow-visible"
      >
        {patentes.map((p, i) => {
          const alcancada = i <= indiceAtual;
          const ehAtual = i === indiceAtual;
          return (
            <li
              key={p.nome}
              ref={ehAtual ? atual : undefined}
              aria-current={ehAtual ? "step" : undefined}
              className="relative flex w-[112px] shrink-0 flex-col items-center gap-2 text-center lg:w-auto"
            >
              {i > 0 && (
                <span
                  aria-hidden="true"
                  className={`absolute left-0 h-0.5 w-1/2 ${alcancada ? "bg-ink" : "bg-line"}`}
                  style={{ top: CAIXA / 2 - 1 }}
                />
              )}
              {i < patentes.length - 1 && (
                <span
                  aria-hidden="true"
                  className={`absolute right-0 h-0.5 w-1/2 ${i < indiceAtual ? "bg-ink" : "bg-line"}`}
                  style={{ top: CAIXA / 2 - 1 }}
                />
              )}
              <span
                className={`relative flex items-center justify-center rounded-pill bg-surface ${alcancada ? "" : "opacity-50"}`}
                style={{ width: CAIXA, height: CAIXA }}
              >
                <Avatar me={me} tamanho={AVATAR} moldura={p.moldura} />
              </span>
              <span className="flex flex-col">
                <span className={`text-corpo [overflow-wrap:anywhere] ${ehAtual ? "font-bold text-ink" : alcancada ? "font-semibold text-ink-2" : "font-semibold text-muted"}`}>
                  {p.nome}
                </span>
                <span className="flex items-center justify-center gap-1 text-apoio tabular-nums text-muted">
                  {!alcancada && <Lock size={12} strokeWidth={2.5} aria-label="Bloqueada" />}
                  Nível {p.nivel}
                </span>
              </span>
              <span className="flex min-h-9 items-center">
                {alcancada && p.moldura && (
                  emUso === p.moldura ? (
                    <button type="button" disabled={ocupado} onClick={() => usar(null)} className={BOTAO_PEQUENO}>
                      Tirar
                    </button>
                  ) : (
                    <button type="button" disabled={ocupado} onClick={() => usar(p.moldura)} className={BOTAO_PEQUENO}>
                      Usar
                    </button>
                  )
                )}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
