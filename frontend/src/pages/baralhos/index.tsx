import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderPlus, Pencil, Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Dialog } from "../../components/Dialog";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import {
  atualizarPasta, criarBaralho, criarPasta, excluirBaralho,
  excluirPasta, listarPastas, type Pasta, plural,
} from "../../lib/cartoes";
import { SeletorCor } from "../../components/SeletorCor";
import { COR_PADRAO, corCheia, normalizarCor } from "../../lib/paleta";
import { CartaoBaralho } from "./CartaoBaralho";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";
import Estudo from "./Estudo";

const contarCartoes = (pasta: Pasta) => pasta.baralhos.reduce((n, b) => n + b.cartoes, 0);

// Os baralhos dela. Pasta é o assunto grande ("Ginecologia"), baralho é o
// recorte ("Vulvovaginites"), cartão é o par frente/verso.
export default function Baralhos() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, isPaused, refetch } = useQuery({
    queryKey: ["pastas"],
    queryFn: listarPastas,
  });
  const [editando, setEditando] = useState<{ pasta?: Pasta } | null>(null);
  const [novoBaralhoEm, setNovoBaralhoEm] = useState<Pasta | null>(null);
  // `?estudar=tudo` vem do passo "Cartões" da Conduta de hoje, no Painel: quem
  // clicou "Estudar" lá já disse o que quer (o mesmo `?estudar=1` do baralho).
  const [params, setParams] = useSearchParams();
  const [estudandoTudo, setEstudandoTudo] = useState(() => params.get("estudar") === "tudo");
  // Apagar leva junto o que está dentro e não tem desfazer: a confirmação diz o
  // que some, numa caixa do próprio app. O `window.confirm` de antes vinha com
  // a cara e o endereço do navegador, fora do sistema visual.
  const [apagando, setApagando] = useState<{ titulo: string; texto: string; confirmar: () => void } | null>(null);

  const recarregar = () => queryClient.invalidateQueries({ queryKey: ["pastas"] });
  const apagarPasta = useMutation({ mutationFn: excluirPasta, onSuccess: recarregar });
  const apagarBaralho = useMutation({ mutationFn: excluirBaralho, onSuccess: recarregar });

  const pastas = data?.pastas;
  const vencidosHoje = (pastas ?? []).reduce(
    (n, p) => n + p.baralhos.reduce((m, b) => m + b.vencidos, 0),
    0,
  );

  if (estudandoTudo) {
    return (
      <Estudo
        baralhoId={null}
        nome="Todos os baralhos"
        onSair={() => {
          setEstudandoTudo(false);
          // Sem isto, recarregar depois de encerrar voltaria para o estudo.
          if (params.get("estudar")) setParams({}, { replace: true });
          recarregar();
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="rotulo text-muted">Seus baralhos</div>
          <h1 className="mt-1 text-titulo text-ink">Cartões</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setEditando({})} className={BOTAO_SECUNDARIO}>
            <FolderPlus size={18} strokeWidth={2} />
            Nova pasta
          </button>
          {/* Estudar tudo numa sessão só: sem isto, oito baralhos vencidos
              custam oito sessões, que é o atrito que mata o hábito diário. */}
          {vencidosHoje > 0 && (
            <button type="button" onClick={() => setEstudandoTudo(true)} className={BOTAO_PRIMARIO}>
              <Play size={18} strokeWidth={2} />
              Estudar tudo ({vencidosHoje})
            </button>
          )}
        </div>
      </div>

      {isLoading && <div className="h-[240px] animate-pulse rounded-card bg-line-soft" />}

      {/* Falha não é vazio: sem isto, uma conexão caída diria que ela não tem
          nenhum baralho. */}
      {!isLoading && (isError || isPaused) && !pastas && (
        <EstadoFalha
          mensagem="Não deu para carregar os seus baralhos. Pode ser a conexão."
          pausado={isPaused}
          onTentarDeNovo={() => void refetch()}
        />
      )}

      {pastas?.length === 0 && (
        <EstadoVazio
          mensagem="Nenhuma pasta ainda. Crie uma por assunto — Ginecologia, Clínica — e dentro dela os baralhos."
          cta={{ label: "Criar a primeira", onClick: () => setEditando({}) }}
        />
      )}

      <div className="flex flex-col gap-6">
        {pastas?.map((pasta) => (
          <section key={pasta.id} className="overflow-hidden rounded-card border border-line bg-surface">
            {/* Cabeçalho no tom suave da cor: é o que faz cada pasta parecer
                um objeto seu, e não mais uma linha de lista. A cor cheia fica
                só na faixa, para o texto continuar sendo tinta sobre papel. */}
            {/* A faixa inteira na cor da pasta. O texto sobre ela é o `on` do
                tom, medido contra 4,5:1 (tests/test_paleta.py) — branco fixo
                falharia nos tons claros. Os secundários usam opacidade em cima
                dessa mesma cor, em vez de `text-muted`, que é tinta e sumiria aqui. */}
            <header className="flex flex-wrap items-center gap-3 px-5 py-4" style={corCheia(pasta.cor, "pasta")}>
              <div className="min-w-0 flex-1 basis-full sm:basis-auto">
                <h2 className="truncate text-bloco">{pasta.nome}</h2>
                <p className="text-apoio opacity-75">
                  {pasta.baralhos.length === 0
                    ? "Sem baralhos"
                    : `${pasta.baralhos.length} baralho${
                        pasta.baralhos.length === 1 ? "" : "s"
                      } · ${plural(contarCartoes(pasta))}`}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setNovoBaralhoEm(pasta)}
                className="flex items-center gap-1.5 rounded-btn border border-current/30 px-2.5 py-1.5 text-apoio font-medium transition duration-hover ease-brand hover:border-current/60 active:scale-[0.97]"
              >
                <Plus size={14} strokeWidth={2} />
                Baralho
              </button>
              <button
                type="button"
                onClick={() => setEditando({ pasta })}
                aria-label={`Editar ${pasta.nome}`}
                className="rounded-btn p-1.5 opacity-70 transition duration-hover hover:opacity-100"
              >
                <Pencil size={14} strokeWidth={2} />
              </button>
              <button
                type="button"
                onClick={() => {
                  const n = pasta.baralhos.length;
                  setApagando({
                    titulo: `Apagar "${pasta.nome}"?`,
                    texto:
                      n === 0
                        ? "A pasta está vazia."
                        : `${n === 1 ? "O baralho dentro dela vai" : `Os ${n} baralhos dentro dela vão`} junto, com os cartões. Não dá para desfazer.`,
                    confirmar: () => apagarPasta.mutate(pasta.id),
                  });
                }}
                aria-label={`Apagar ${pasta.nome}`}
                className="rounded-btn p-1.5 opacity-70 transition duration-hover hover:opacity-100"
              >
                <Trash2 size={14} strokeWidth={2} />
              </button>
            </header>

            {pasta.baralhos.length === 0 ? (
              <button
                type="button"
                onClick={() => setNovoBaralhoEm(pasta)}
                className="flex w-full items-center justify-center gap-2 px-5 py-8 text-apoio text-muted transition duration-hover hover:bg-ground hover:text-ink"
              >
                <Plus size={16} strokeWidth={2} />
                Criar o primeiro baralho desta pasta
              </button>
            ) : (
              // `grid-cols-1` (minmax(0, 1fr)) e não a coluna implícita: essa
              // cresce até a largura mínima do conteúdo, e um nome longo com
              // `truncate` empurrava o bloco para fora da pasta no celular.
              <div className="grid grid-cols-1 gap-x-4 gap-y-5 bg-ground p-4 sm:grid-cols-2 lg:grid-cols-3">
                {pasta.baralhos.map((b) => (
                  <CartaoBaralho
                    key={b.id}
                    baralho={b}
                    cor={pasta.cor}
                    onApagar={() =>
                      setApagando({
                        titulo: `Apagar "${b.nome}"?`,
                        texto:
                          b.cartoes === 0
                            ? "O baralho está vazio."
                            : `${b.cartoes === 1 ? "O cartão dele vai" : `Os ${plural(b.cartoes)} dele vão`} junto. Não dá para desfazer.`,
                        confirmar: () => apagarBaralho.mutate(b.id),
                      })
                    }
                  />
                ))}
              </div>
            )}
          </section>
        ))}
      </div>

      <Dialog titulo={apagando?.titulo ?? ""} aberto={apagando !== null} onFechar={() => setApagando(null)}>
        <div className="flex flex-col gap-5">
          <p className="text-corpo text-ink-2">{apagando?.texto}</p>
          {/* "Cancelar" primeiro: é nele que o foco cai ao abrir. */}
          <div className="flex flex-wrap justify-end gap-2">
            <button type="button" onClick={() => setApagando(null)} className={BOTAO_SECUNDARIO}>
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => {
                apagando?.confirmar();
                setApagando(null);
              }}
              className={BOTAO_PRIMARIO}
            >
              Apagar
            </button>
          </div>
        </div>
      </Dialog>
      <FormularioPasta
        aberto={editando !== null}
        pasta={editando?.pasta}
        onFechar={() => setEditando(null)}
        onSalvo={recarregar}
      />
      <FormularioBaralho
        pasta={novoBaralhoEm}
        onFechar={() => setNovoBaralhoEm(null)}
        onSalvo={recarregar}
      />
    </div>
  );
}

function FormularioPasta({
  aberto, pasta, onFechar, onSalvo,
}: {
  aberto: boolean;
  pasta?: Pasta;
  onFechar: () => void;
  onSalvo: () => void;
}) {
  const [nome, setNome] = useState("");
  const [cor, setCor] = useState<string>(COR_PADRAO.pasta);
  const [salvando, setSalvando] = useState(false);
  // Remonta o formulário a cada abertura, com os valores da pasta em edição.
  const chave = `${aberto}-${pasta?.id ?? "nova"}`;
  const [ultimaChave, setUltimaChave] = useState(chave);
  if (chave !== ultimaChave) {
    setUltimaChave(chave);
    setNome(pasta?.nome ?? "");
    setCor(normalizarCor(pasta?.cor, "pasta"));
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      if (pasta) await atualizarPasta(pasta.id, nome, cor);
      else await criarPasta(nome, cor);
      onSalvo();
      onFechar();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Dialog titulo={pasta ? "Editar pasta" : "Nova pasta"} aberto={aberto} onFechar={onFechar}>
      <form onSubmit={salvar} className="flex flex-col gap-5">
        <label htmlFor="pasta-nome" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Nome</span>
          <input
            id="pasta-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            maxLength={60}
            placeholder="Ginecologia"
            autoFocus
            className={CAMPO}
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="rotulo mb-1 text-muted">Cor</legend>
          <SeletorCor valor={cor} onChange={setCor} tamanho={32} />
          <span className="text-apoio text-muted">Toque numa cor para ver os tons.</span>
        </fieldset>

        <button type="submit" disabled={salvando} className={`${BOTAO_PRIMARIO} w-full`}>
          {salvando ? "Salvando…" : "Salvar"}
        </button>
      </form>
    </Dialog>
  );
}

function FormularioBaralho({
  pasta, onFechar, onSalvo,
}: {
  pasta: Pasta | null;
  onFechar: () => void;
  onSalvo: () => void;
}) {
  const [nome, setNome] = useState("");
  const [salvando, setSalvando] = useState(false);
  const chave = String(pasta?.id ?? "");
  const [ultimaChave, setUltimaChave] = useState(chave);
  if (chave !== ultimaChave) {
    setUltimaChave(chave);
    setNome("");
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!pasta) return;
    setSalvando(true);
    try {
      await criarBaralho(pasta.id, nome);
      onSalvo();
      onFechar();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Dialog titulo={`Novo baralho em ${pasta?.nome ?? ""}`} aberto={pasta !== null} onFechar={onFechar}>
      <form onSubmit={salvar} className="flex flex-col gap-4">
        <label htmlFor="baralho-nome" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Nome</span>
          <input
            id="baralho-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            maxLength={60}
            placeholder="Vulvovaginites"
            autoFocus
            className={CAMPO}
          />
        </label>
        <button type="submit" disabled={salvando} className={`${BOTAO_PRIMARIO} w-full`}>
          {salvando ? "Criando…" : "Criar baralho"}
        </button>
      </form>
    </Dialog>
  );
}
