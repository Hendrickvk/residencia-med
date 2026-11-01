import { Check, Lock, Shield, Zap } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Avatar } from "../../components/Avatar";
import { EstadoFalha } from "../../components/EstadoFalha";
import { Moeda } from "../../components/Moeda";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { CenaDoTema } from "../../components/Tracos";
import { ApiError } from "../../lib/api";
import { useMe } from "../../lib/auth";
import { temaDaMoldura } from "../../lib/cosmeticos";
import { BOTAO_SECUNDARIO } from "../../lib/estilos";
import { formatarNumeroBR } from "../../lib/format";
import { nomeExibido } from "../../lib/perfil";
import { comprarItem, equiparItem, useLoja } from "../../lib/progresso";
import type { ItemLoja, Loja as DadosLoja, Me } from "../../lib/types";

const BOTAO_PEQUENO =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-btn border border-line bg-surface px-3 text-[14px] font-medium text-ink-2 transition duration-hover ease-brand hover:border-muted hover:text-ink active:scale-[0.97] disabled:cursor-not-allowed disabled:text-faint disabled:active:scale-100";
const BOTAO_PAGAR =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-btn bg-ink px-3 text-[14px] font-semibold tabular-nums text-onink transition duration-hover ease-brand hover:opacity-90 active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-line disabled:text-faint disabled:active:scale-100";

function Preco({ valor, className = "" }: { valor: number; className?: string }) {
  return (
    <span className={`flex items-center gap-1 font-bold tabular-nums ${className}`}>
      <Moeda tamanho={14} />
      {formatarNumeroBR(valor)}
    </span>
  );
}

// O que uma ação da loja precisa: quem está sendo confirmado agora, e o que fazer.
interface Acoes {
  confirmando: string | null;
  ocupado: boolean;
  pedir: (id: string) => void;
  voltar: () => void;
  pagar: (id: string) => void;
  usar: (tipo: string, id: string | null) => void;
}

// Comprar pede dois toques, sem diálogo: gastar moedas não é irreversível o bastante
// para interromper, mas um toque errado num item de 1.200 moedas seria ruim.
function PedirOuPagar({ id, preco, saldo, acoes }: { id: string; preco: number; saldo: number; acoes: Acoes }) {
  if (acoes.confirmando === id) {
    return (
      <span className="flex items-center gap-1.5">
        <button type="button" disabled={acoes.ocupado} onClick={() => acoes.pagar(id)} className={BOTAO_PAGAR}>
          Pagar {formatarNumeroBR(preco)}
        </button>
        <button type="button" disabled={acoes.ocupado} onClick={acoes.voltar} className="h-9 px-2 text-[14px] font-medium text-muted hover:text-ink">
          Voltar
        </button>
      </span>
    );
  }
  if (saldo < preco) {
    return <span className="text-apoio tabular-nums text-muted">Faltam {formatarNumeroBR(preco - saldo)}</span>;
  }
  return (
    <button type="button" onClick={() => acoes.pedir(id)} className={BOTAO_PEQUENO}>
      Comprar
    </button>
  );
}

function RodapeDoItem({ item, saldo, acoes }: { item: ItemLoja; saldo: number; acoes: Acoes }) {
  if (item.em_uso) {
    return (
      <>
        <span className="flex items-center gap-1 text-apoio font-semibold text-ink">
          <Check size={14} strokeWidth={2.5} />
          Em uso
        </span>
        <button type="button" disabled={acoes.ocupado} onClick={() => acoes.usar(item.tipo, null)} className={BOTAO_PEQUENO}>
          Tirar
        </button>
      </>
    );
  }
  if (item.seu) {
    return (
      <>
        <span className="text-apoio font-semibold text-ink-2">Sua</span>
        <button type="button" disabled={acoes.ocupado} onClick={() => acoes.usar(item.tipo, item.id)} className={BOTAO_PEQUENO}>
          Usar
        </button>
      </>
    );
  }
  if (!item.liberado) {
    return (
      <>
        <span className="flex min-w-0 items-start gap-1 text-apoio font-semibold text-muted">
          <Lock size={13} strokeWidth={2.5} className="mt-[3px] shrink-0" />
          {item.exige}
        </span>
        {item.de_patente ? (
          <span className="text-apoio text-muted">Vem com a patente</span>
        ) : (
          <Preco valor={item.preco} className="text-apoio text-muted" />
        )}
      </>
    );
  }
  return (
    <>
      {acoes.confirmando !== item.id && <Preco valor={item.preco} className="text-corpo" />}
      <PedirOuPagar id={item.id} preco={item.preco} saldo={saldo} acoes={acoes} />
    </>
  );
}

function CartaoDoItem({ item, me, saldo, acoes }: { item: ItemLoja; me: Me | undefined; saldo: number; acoes: Acoes }) {
  const tema = item.tipo === "moldura" ? temaDaMoldura(item.id) : null;
  return (
    <article className="flex min-w-0 flex-col gap-3 rounded-card border border-line bg-surface p-3 max-sm:w-[220px] max-sm:shrink-0 max-sm:snap-start">
      {item.tipo === "moldura" ? (
        <div className="[container-type:inline-size]">
          <div
            className={`relative flex h-[calc(39cqw+56px)] items-center justify-center overflow-hidden rounded-col ${tema ? "bg-surface" : "bg-ground"}`}
            style={tema?.variaveis as React.CSSProperties | undefined}
          >
            {tema ? (
              <>
                {/* Um crachá em miniatura. A cena é desenhada com o avatar em (150, 117) de
                    300 por 104: é por isso que ele fica a 39% da largura, e não no meio. */}
                <span className="absolute inset-x-0 top-0 aspect-[300/104]" style={{ color: tema.marca }}>
                  <CenaDoTema tema={tema} />
                  <span className="absolute left-1/2 top-[3.4cqw] h-[3.3cqw] w-[17cqw] -translate-x-1/2 rounded-pill bg-ground" />
                  <span className="marca-texto absolute inset-x-0 top-[10.5cqw] text-center text-[5.7cqw]">Conduta</span>
                </span>
                <span className="absolute left-1/2 top-[39cqw] -translate-x-1/2 -translate-y-1/2 rounded-pill bg-surface p-0.5">
                  <Avatar me={me} tamanho={64} moldura={item.id} />
                </span>
              </>
            ) : (
              <Avatar me={me} tamanho={64} moldura={item.id} />
            )}
          </div>
        </div>
      ) : (
        <div className="flex h-[124px] items-center justify-center overflow-hidden rounded-col bg-ground">
          <span className="flex flex-col items-center gap-0.5 px-2.5 text-center">
            <span className="text-bloco [overflow-wrap:anywhere]">{nomeExibido(me)}</span>
            <span className="text-apoio text-ink-2">{item.nome}</span>
          </span>
        </div>
      )}
      {item.tipo === "moldura" && (
        <span className="flex flex-col">
          <span className="text-corpo font-semibold [overflow-wrap:anywhere]">{item.nome}</span>
          {tema && <span className="text-apoio text-muted">Muda também o crachá e o perfil</span>}
        </span>
      )}
      <div className="mt-auto flex min-h-9 flex-wrap items-center justify-between gap-2">
        <RodapeDoItem item={item} saldo={saldo} acoes={acoes} />
      </div>
    </article>
  );
}

function LinhaConsumivel({
  icone, nome, descricao, id, preco, saldo, acoes, encerrado,
}: {
  icone: React.ReactNode;
  nome: string;
  descricao: string;
  id: string;
  preco: number;
  saldo: number;
  acoes: Acoes;
  // A guarda cheia, ou o dobro já valendo: não há o que comprar agora.
  encerrado: string | null;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-line-soft px-4 py-3.5 last:border-0 sm:px-5">
      <span className="shrink-0 text-ink">{icone}</span>
      <div className="flex min-w-0 flex-[1_1_180px] flex-col">
        <span className="text-corpo font-semibold">{nome}</span>
        <span className="text-apoio tabular-nums text-muted">{descricao}</span>
      </div>
      {encerrado ? (
        <span className="ml-auto text-apoio font-semibold text-ink">{encerrado}</span>
      ) : (
        <span className="ml-auto flex items-center gap-3">
          {acoes.confirmando !== id && <Preco valor={preco} className="text-corpo" />}
          <PedirOuPagar id={id} preco={preco} saldo={saldo} acoes={acoes} />
        </span>
      )}
    </div>
  );
}

export default function PaginaLoja() {
  const { data: me } = useMe();
  const { data, isLoading, isPaused, refetch } = useLoja();
  const [confirmando, setConfirmando] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function agir(acao: () => Promise<DadosLoja>) {
    setErro(null);
    setOcupado(true);
    try {
      await acao();
      setConfirmando(null);
    } catch (e) {
      // A frase do servidor diz o que faltou (nível, saldo). Sem ela, é a conexão.
      setErro(e instanceof ApiError ? e.message : "Não deu para concluir agora. Pode ser a conexão.");
    } finally {
      setOcupado(false);
    }
  }

  const acoes: Acoes = {
    confirmando,
    ocupado,
    pedir: setConfirmando,
    voltar: () => setConfirmando(null),
    pagar: (id) => void agir(() => comprarItem(id)),
    usar: (tipo, id) => void agir(() => equiparItem(tipo, id)),
  };

  if (isLoading) {
    return (
      <div className="flex flex-col gap-7">
        <div className="h-[46px] w-72 animate-pulse rounded-card bg-line-soft" />
        <div className="h-[150px] animate-pulse rounded-caso bg-line-soft" />
        <div className="h-[260px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  if (!data) {
    return (
      <EstadoFalha
        mensagem="Não deu para carregar a loja. Pode ser a conexão."
        pausado={isPaused}
        onTentarDeNovo={() => refetch()}
      />
    );
  }

  const { protecao, xp_dobro: dobro } = data;

  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-wrap items-center justify-between gap-3.5">
        <div className="flex items-center gap-3">
          <Moeda tamanho={34} />
          <h1 className="text-titulo tabular-nums">
            <NumeroAnimado valor={data.moedas} chave="saldo-moedas" formatar={(v) => formatarNumeroBR(Math.round(v))} />{" "}
            moeda{data.moedas !== 1 ? "s" : ""}
          </h1>
        </div>
        <Link to="/perfil" className={BOTAO_SECUNDARIO}>
          Editar seu perfil
        </Link>
      </div>

      {erro && (
        <p role="alert" className="text-apoio font-medium text-t1">
          {erro}
        </p>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-bloco">Para a ofensiva</h2>
        <div className="rounded-caso border border-line bg-surface">
          <LinhaConsumivel
            icone={<Shield size={20} strokeWidth={2} />}
            nome="Proteção de ofensiva"
            descricao={`Segura sozinha um dia sem estudo. Você tem ${protecao.tem} de ${protecao.maximo}.`}
            id={protecao.id}
            preco={protecao.preco}
            saldo={data.moedas}
            acoes={acoes}
            encerrado={protecao.tem >= protecao.maximo ? "Guarda cheia" : null}
          />
          <LinhaConsumivel
            icone={<Zap size={20} strokeWidth={2} />}
            nome="XP em dobro"
            descricao={`Por ${dobro.minutos} minutos, a partir de quando você comprar. Não dobra as moedas.`}
            id={dobro.id}
            preco={dobro.preco}
            saldo={data.moedas}
            acoes={acoes}
            encerrado={dobro.ate ? `Valendo até as ${dobro.ate.slice(11, 16)}` : null}
          />
        </div>
      </section>

      {data.secoes.map((secao) => (
        <section key={secao.tipo} className="flex flex-col gap-3">
          <h2 className="text-bloco">{secao.nome}</h2>
          {/* No celular a fileira corre de lado: em duas colunas, a loja dava 4 mil pixels de rolagem. */}
          <div className="grid gap-3 sm:grid-cols-[repeat(auto-fill,minmax(196px,1fr))] max-sm:-mx-4 max-sm:flex max-sm:snap-x max-sm:snap-proximity max-sm:scroll-px-4 max-sm:overflow-x-auto max-sm:px-4 max-sm:pb-1.5">
            {secao.itens.map((item) => (
              <CartaoDoItem key={item.id} item={item} me={me} saldo={data.moedas} acoes={acoes} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
