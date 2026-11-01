import { Link } from "react-router-dom";
import { Avatar } from "../../components/Avatar";
import { BarraNivel } from "../../components/BarraNivel";
import { Carimbo } from "../../components/Carimbo";
import { Cracha } from "../../components/Cracha";
import { EstadoFalha } from "../../components/EstadoFalha";
import { Moeda } from "../../components/Moeda";
import { useMe } from "../../lib/auth";
import { BOTAO_SECUNDARIO } from "../../lib/estilos";
import { formatarNumeroBR } from "../../lib/format";
import { useProgresso } from "../../lib/progresso";
import type { Progresso } from "../../lib/types";

// O mapa cobre 26 semanas e fecha no sábado desta: como no GitHub e no Anki, cada
// coluna é uma semana, de domingo a sábado.
const DIAS_NO_MAPA = 26 * 7;

// Em tons de tinta: t1–t5 só dizem nível de triagem (DESIGN_TRIAGEM.md §1). Classes
// inteiras, porque o Tailwind só gera o que encontra escrito por extenso.
const TONS = ["bg-line-soft", "bg-ink opacity-[.22]", "bg-ink opacity-[.42]", "bg-ink opacity-[.68]", "bg-ink"];

function tomDoDia(xp: number): string {
  if (xp <= 0) return TONS[0];
  if (xp < 50) return TONS[1];
  if (xp < 150) return TONS[2];
  if (xp < 300) return TONS[3];
  return TONS[4];
}

// Meio-dia, para a conta de dias não atravessar a meia-noite em nenhum fuso. `hoje`
// vem do servidor, que é quem sabe que dia é em Brasília.
function celulasDoMapa({ hoje, dias }: Pick<Progresso, "hoje" | "dias">) {
  const porDia = new Map(dias.map((d) => [d.dia, d.xp]));
  const agora = new Date(`${hoje}T12:00:00`);
  const fim = new Date(agora);
  fim.setDate(agora.getDate() + (6 - agora.getDay()));
  return Array.from({ length: DIAS_NO_MAPA }, (_, i) => {
    const dia = new Date(fim);
    dia.setDate(fim.getDate() - (DIAS_NO_MAPA - 1 - i));
    if (dia > agora) return { chave: i, classe: "" };
    return { chave: i, classe: tomDoDia(porDia.get(dia.toISOString().slice(0, 10)) ?? 0) };
  });
}

export default function PaginaProgresso() {
  const { data: me } = useMe();
  const { data, isLoading, isPaused, refetch } = useProgresso();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-7">
        <div className="h-[46px] w-56 animate-pulse rounded-card bg-line-soft" />
        <div className="h-[460px] animate-pulse rounded-caso bg-line-soft" />
        <div className="h-[320px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  // A ordem de sempre: com dado em cache a tela segue, e falha não é "nível 1".
  if (!data) {
    return (
      <EstadoFalha
        mensagem="Não deu para carregar o seu progresso. Pode ser a conexão."
        pausado={isPaused}
        onTentarDeNovo={() => refetch()}
      />
    );
  }

  const { nivel, patentes, areas, dias, maior_sequencia: maiorSequencia, vitrine } = data;
  const ofensiva = me?.ofensiva_dias ?? 0;

  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-wrap items-center justify-between gap-3.5">
        <h1 className="text-titulo">Seu perfil</h1>
        <Link to="/perfil" className={BOTAO_SECUNDARIO}>
          Editar seu perfil
        </Link>
      </div>

      <section className="flex flex-wrap items-start gap-7">
        <div className="mx-auto w-full max-w-[300px] shrink-0 sm:mx-0">
          <Cracha me={me} nivel={nivel.nivel} patente={nivel.patente} />
        </div>

        <div className="flex min-w-0 flex-[1_1_320px] flex-col gap-6">
          <div className="flex flex-col gap-3">
            <h2 className="text-[34px] font-extrabold leading-[1.08] tracking-[-0.03em]">
              Faltam {formatarNumeroBR(nivel.falta)} XP para o nível {nivel.nivel + 1}.
            </h2>
            <BarraNivel pct={nivel.pct} rotulo={`${Math.round(nivel.pct)}% do caminho até o nível ${nivel.nivel + 1}`} />
            <p className="flex flex-wrap items-center gap-x-5 gap-y-1 text-apoio tabular-nums text-muted">
              <span>
                <strong className="font-semibold text-ink">{formatarNumeroBR(nivel.xp)} XP</strong> no total
              </span>
              <span className="flex items-center gap-1.5">
                <Moeda tamanho={15} />
                <strong className="font-semibold text-ink">{formatarNumeroBR(me?.moedas ?? 0)}</strong> moedas
              </span>
              {ofensiva > 0 && (
                <span>
                  <strong className="font-semibold text-ink">
                    {ofensiva} dia{ofensiva !== 1 ? "s" : ""}
                  </strong>{" "}
                  de ofensiva
                  {me?.protecoes_ofensiva
                    ? `, com ${me.protecoes_ofensiva} ${me.protecoes_ofensiva === 1 ? "proteção guardada" : "proteções guardadas"}`
                    : ""}
                </span>
              )}
            </p>
          </div>

          {nivel.libera && (
            <div className="flex flex-col gap-3 rounded-caso border border-line bg-surface px-5 py-4">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="text-bloco">O nível {nivel.libera.nivel} libera</h3>
                <Link
                  to="/progresso/loja"
                  className="text-apoio font-semibold text-ink underline decoration-line underline-offset-[3px] hover:decoration-ink"
                >
                  Ver a loja
                </Link>
              </div>
              <div className="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-3">
                {nivel.libera.itens.map((item) => (
                  <div key={item.id} className="flex min-w-0 items-center gap-2.5">
                    {item.tipo === "moldura" ? (
                      <Avatar me={me} tamanho={36} moldura={item.id} />
                    ) : (
                      <span className="flex h-[49px] w-[49px] shrink-0 items-center justify-center rounded-card border border-line text-[11px] font-bold leading-tight text-muted">
                        Título
                      </span>
                    )}
                    <div className="flex min-w-0 flex-col">
                      <span className="text-corpo font-semibold [overflow-wrap:anywhere]">
                        {item.tipo === "moldura" ? "Moldura" : "Título"} {item.nome}
                      </span>
                      <span className="text-apoio tabular-nums text-muted">
                        {item.de_patente ? "Vem com a patente" : `${formatarNumeroBR(item.preco)} moedas`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
              <h3 className="text-bloco">Carimbos</h3>
              <Link
                to="/progresso/conquistas"
                className="text-apoio font-semibold tabular-nums text-ink underline decoration-line underline-offset-[3px] hover:decoration-ink"
              >
                Ver a caderneta, {vitrine.obtidos} de {vitrine.total}
              </Link>
            </div>
            {vitrine.itens.length > 0 ? (
              <div className="flex flex-wrap items-center gap-x-6 gap-y-5 py-1">
                {vitrine.itens.map((c, i) => (
                  <Carimbo key={c.id} nome={c.nome} grau={c.grau} obtidaEm={c.obtida_em} ordem={i} />
                ))}
              </div>
            ) : (
              <p className="text-apoio text-muted">O primeiro sai com o primeiro caso respondido.</p>
            )}
          </div>

          <div className="flex flex-col gap-3">
            <h3 className="text-bloco">Patentes</h3>
            <ol className="grid grid-cols-4 gap-y-4 md:grid-cols-8">
              {patentes.map((p) => {
                const alcancada = nivel.nivel >= p.nivel;
                const atual = p.nome === nivel.patente;
                return (
                  <li
                    key={p.nome}
                    aria-current={atual ? "step" : undefined}
                    className={`flex flex-col gap-2 border-t-2 pr-2 pt-3 ${
                      alcancada ? "border-ink" : "border-line"
                    } ${atual ? "text-ink" : alcancada ? "text-ink-2" : "text-muted"}`}
                  >
                    <span className="rotulo text-inherit">{p.nome}</span>
                    <span className="text-apoio tabular-nums">Nível {p.nivel}</span>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-bloco">Experiência por área</h2>
        <div className="rounded-caso border border-line bg-surface">
          {areas.map((a) => (
            <div
              key={a.id}
              className="grid grid-cols-[minmax(0,1fr)_44px] items-center gap-x-4 gap-y-1.5 border-b border-line-soft px-4 py-3.5 last:border-0 md:grid-cols-[minmax(0,1.2fr)_44px_minmax(120px,2fr)_minmax(0,1.2fr)] md:px-5"
            >
              <span className="min-w-0 text-corpo font-semibold">{a.nome}</span>
              <span className="num-md text-right" aria-label={`Nível ${a.nivel}`}>
                {a.nivel}
              </span>
              <span className="max-md:col-span-2">
                <BarraNivel pct={a.pct} fina />
              </span>
              <span className="text-apoio tabular-nums text-muted max-md:col-span-2">
                {a.falta > 0
                  ? `Faltam ${formatarNumeroBR(a.falta)} XP para o nível ${a.nivel + 1}`
                  : "Nível máximo"}
              </span>
            </div>
          ))}
        </div>
        <p className="text-apoio text-muted">
          O nível de área mede o quanto você estudou cada uma. Como você está indo nelas continua no{" "}
          <Link to="/painel" className="font-semibold text-ink underline decoration-line underline-offset-[3px] hover:decoration-ink">
            quadro de triagem do Painel
          </Link>
          .
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
          <h2 className="text-bloco">Dias de estudo</h2>
          <span className="text-apoio tabular-nums text-muted">
            {dias.length} dia{dias.length !== 1 ? "s" : ""} nos últimos 6 meses
            {maiorSequencia > 1 && `, a maior sequência com ${maiorSequencia}`}
          </span>
        </div>
        <div className="flex flex-col gap-2.5 rounded-caso border border-line bg-surface p-4 md:p-5">
          {/* A grade encolhe com a tela, até o limite em que os dias ficam do tamanho certo. */}
          <div
            role="img"
            aria-label={`${dias.length} dias de estudo nos últimos 6 meses`}
            className="grid max-w-[420px] grid-flow-col grid-cols-[repeat(26,minmax(0,1fr))] grid-rows-7 gap-0.5"
          >
            {celulasDoMapa(data).map((celula) => (
              <span key={celula.chave} className={`aspect-square rounded-[2px] ${celula.classe}`} />
            ))}
          </div>
          <div className="flex items-center gap-1 text-apoio text-muted" aria-hidden="true">
            Menos
            {TONS.map((tom) => (
              <span key={tom} className={`h-[11px] w-[11px] rounded-[2px] first:ml-1 last:mr-1 ${tom}`} />
            ))}
            Mais
          </div>
        </div>
      </section>
    </div>
  );
}
