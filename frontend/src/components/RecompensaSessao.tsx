import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useMe } from "../lib/auth";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../lib/estilos";
import { formatarNumeroBR } from "../lib/format";
import { resumirGanhos, useGanhos } from "../lib/ganhos";
import { verificarCarimbos } from "../lib/progresso";
import { useRespostasPendentes } from "../lib/respostasQueue";
import type { CarimboNovo, ResumoGanhos } from "../lib/types";
import { BarraNivel } from "./BarraNivel";
import { Carimbo } from "./Carimbo";
import { Cracha } from "./Cracha";
import { Dialog } from "./Dialog";
import { Moeda } from "./Moeda";
import { NumeroAnimado } from "./NumeroAnimado";

// O bloco do fim da sessão: é aqui que a progressão aparece com força, porque o
// caso em si fica sóbrio (DESIGN_TRIAGEM.md §6). Subir de nível acontece quase todo
// dia no começo, então o número só carimba; a troca de patente, que são sete na
// carreira inteira, é a única que abre um diálogo.
export function RecompensaSessao({ resumo }: { resumo: ResumoGanhos }) {
  const { xp, moedas, areas, antes, depois } = resumo;
  const subiu = depois.nivel > antes.nivel;
  const proxima = depois.proxima_patente;
  const [fechouDialogo, setFechouDialogo] = useState(false);
  const CLASSE_LINK =
    "text-apoio font-semibold text-ink underline decoration-line underline-offset-[3px] transition-colors duration-hover hover:decoration-ink";

  return (
    <>
      <section
        aria-label="O que esta sessão rendeu"
        className="flex animate-entrar flex-col gap-5 rounded-caso border border-line bg-surface p-6"
      >
        <div className="flex flex-col gap-2.5">
          <div className="flex items-baseline gap-2">
            <NumeroAnimado className="num-lg" valor={xp} formatar={(v) => `+${formatarNumeroBR(Math.round(v))}`} />
            <span className="text-subtitulo">XP</span>
          </div>
          {moedas > 0 && (
            <span className="flex items-center gap-2 text-bloco tabular-nums">
              <Moeda tamanho={18} />+{formatarNumeroBR(moedas)} moeda{moedas !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
            {/* A chave faz o número carimbar quando o nível sobe. */}
            <span key={depois.nivel} className={`text-bloco ${subiu ? "inline-block animate-marcar" : ""}`}>
              Nível {depois.nivel} · {depois.patente}
            </span>
            <span className="text-apoio tabular-nums text-muted">
              Faltam {formatarNumeroBR(depois.falta)} XP para o nível {depois.nivel + 1}
            </span>
          </div>
          {/* Subiu de nível: a barra recomeça do zero do nível novo. */}
          <BarraNivel
            de={subiu ? 0 : antes.pct}
            pct={depois.pct}
            rotulo={`${Math.round(depois.pct)}% do caminho até o nível ${depois.nivel + 1}`}
          />
        </div>

        {areas.length > 0 && (
          <div className="flex flex-wrap gap-x-5 gap-y-1.5">
            {areas.map((area) => (
              <span key={area.nome} className="text-apoio text-muted">
                {area.nome} <strong className="font-bold tabular-nums text-ink">+{area.xp}</strong>
              </span>
            ))}
          </div>
        )}

        <CarimbosDaSessao />

        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-t border-line-soft pt-4">
          {depois.libera ? (
            <>
              <span className="text-apoio text-ink-2">
                No nível {depois.libera.nivel} você libera {depois.libera.frase}.
              </span>
              <Link to="/progresso/loja" className={CLASSE_LINK}>
                Ver na loja
              </Link>
            </>
          ) : (
            <Link to="/progresso" className={CLASSE_LINK}>
              Ver meu progresso
            </Link>
          )}
        </div>
      </section>

      <TrocaDePatente
        aberto={antes.patente !== depois.patente && !fechouDialogo}
        patenteAntes={antes.patente}
        nivel={depois.nivel}
        patente={depois.patente}
        proxima={proxima}
        onFechar={() => setFechouDialogo(true)}
      />
    </>
  );
}

// O carimbo sai aqui e não durante o caso, que fica sóbrio. Só pergunta depois de a
// fila de respostas esvaziar: antes disso a última resposta ainda não conta.
function CarimbosDaSessao() {
  const livre = useRespostasPendentes() === 0;
  const [novos, setNovos] = useState<CarimboNovo[]>([]);

  useEffect(() => {
    if (!livre) return;
    let ativo = true;
    verificarCarimbos()
      .then((chegaram) => {
        if (!ativo || !chegaram.length) return;
        setNovos((atuais) => [...atuais, ...chegaram.filter((c) => !atuais.some((a) => a.id === c.id))]);
      })
      .catch(() => {
        // Sem carimbo agora: a caderneta confere de novo ao abrir, e nada se perde.
      });
    return () => {
      ativo = false;
    };
  }, [livre]);

  const moedas = novos.reduce((soma, c) => soma + c.moedas, 0);
  return (
    <div aria-live="polite">
      {novos.length > 0 && (
        <div className="flex flex-col gap-3 border-t border-line-soft pt-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-4">
            {novos.map((c, i) => (
              <Carimbo key={c.id} nome={c.nome} grau={c.grau} obtidaEm={c.obtida_em} ordem={i} bate />
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
            <span className="flex items-center gap-1.5 text-apoio font-semibold tabular-nums text-ink">
              <Moeda tamanho={14} />+{moedas} moeda{moedas !== 1 ? "s" : ""}
            </span>
            <Link
              to="/progresso/conquistas"
              className="text-apoio font-semibold text-ink underline decoration-line underline-offset-[3px] transition-colors duration-hover hover:decoration-ink"
            >
              Ver a caderneta
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function TrocaDePatente({
  aberto, patenteAntes, nivel, patente, proxima, onFechar,
}: {
  aberto: boolean;
  patenteAntes: string;
  nivel: number;
  patente: string;
  proxima: ResumoGanhos["depois"]["proxima_patente"];
  onFechar: () => void;
}) {
  const { data: me } = useMe();
  return (
    <Dialog titulo="Nova patente" aberto={aberto} onFechar={onFechar} larga>
      <div className="flex flex-wrap justify-center gap-7">
        <div className="w-[300px] max-w-full shrink-0">
          <Cracha me={me} nivel={nivel} patente={patente} />
        </div>
        <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-4">
          <h3 className="text-titulo">
            Nível {nivel}. {patente}.
          </h3>
          <p className="text-corpo text-ink-2">
            {patenteAntes} ficou para trás.
            {proxima && ` A próxima patente, ${proxima.nome}, vem no nível ${proxima.nivel}.`}
            {" "}A moldura desta já é sua.
          </p>
          <div className="mt-auto flex flex-wrap gap-2.5">
            <button type="button" onClick={onFechar} className={BOTAO_PRIMARIO}>
              Continuar
            </button>
            <Link to="/progresso/loja" onClick={onFechar} className={BOTAO_SECUNDARIO}>
              Ver a loja
            </Link>
          </div>
        </div>
      </div>
    </Dialog>
  );
}

// A versão para as sessões que acumulam ganho a ganho: Praticar, Revisão e Baralhos.
export function RecompensaDaSessao() {
  const resumo = resumirGanhos(useGanhos());
  return resumo ? <RecompensaSessao resumo={resumo} /> : null;
}
