import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pencil, Play, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Dialog } from "../../components/Dialog";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import {
  atualizarCartao, type Cartao, criarCartao, excluirCartao, fundoDaPasta, listarPastas,
  moverBaralho, obterBaralho,
} from "../../lib/cartoes";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";
import Estudo from "./Estudo";

export default function Baralho() {
  const { id = "" } = useParams();
  const baralhoId = Number(id);
  const queryClient = useQueryClient();
  const { data, isLoading, isError, isPaused, refetch } = useQuery({
    queryKey: ["baralho", baralhoId],
    queryFn: () => obterBaralho(baralhoId),
    enabled: Number.isFinite(baralhoId),
  });
  const [editando, setEditando] = useState<{ cartao?: Cartao } | null>(null);
  // `?estudar=1` vem do botão da lista de pastas: quem clicou "Estudar" lá já
  // disse o que quer, e não deve cair na lista de cartões antes.
  const [params, setParams] = useSearchParams();
  const [estudando, setEstudando] = useState(() => params.get("estudar") === "1");
  const [ajustando, setAjustando] = useState(false);

  const recarregar = () => {
    queryClient.invalidateQueries({ queryKey: ["baralho", baralhoId] });
    // A contagem de vencidos na lista de pastas muda junto.
    queryClient.invalidateQueries({ queryKey: ["pastas"] });
  };
  const apagar = useMutation({ mutationFn: excluirCartao, onSuccess: recarregar });

  if (estudando) {
    return (
      <Estudo
        baralhoId={baralhoId}
        nome={data?.baralho.nome ?? ""}
        cor={data?.baralho.cor}
        onSair={() => {
          setEstudando(false);
          // Tira o `?estudar=1` da URL: sem isso, recarregar a página depois
          // de encerrar jogaria ela de volta para dentro do estudo.
          if (params.get("estudar")) setParams({}, { replace: true });
          recarregar();
        }}
      />
    );
  }

  const cartoes = data?.cartoes;
  // Cartão sem agendamento é novo, e novo conta como vencido — a mesma regra
  // do servidor (`db.cartoes_para_estudar`).
  const vencidos = (cartoes ?? []).filter(
    (c) => !c.proxima_revisao || new Date(c.proxima_revisao) <= new Date(),
  ).length;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          to="/baralhos"
          className="inline-flex items-center gap-1.5 text-apoio text-muted transition duration-hover hover:text-ink"
        >
          <ArrowLeft size={14} strokeWidth={2} />
          Baralhos
        </Link>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
          <div className="flex items-center gap-3">
            <span
              className={`h-9 w-1.5 shrink-0 rounded-pill ${fundoDaPasta(data?.baralho.cor)}`}
              aria-hidden="true"
            />
            <div>
              <div className="rotulo text-muted">{data?.baralho.pasta}</div>
              <h1 className="mt-0.5 text-subtitulo text-ink">{data?.baralho.nome ?? "…"}</h1>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setAjustando(true)}
              className={BOTAO_SECUNDARIO}
              aria-label="Renomear ou mover este baralho"
            >
              <Pencil size={18} strokeWidth={2} />
              Ajustar
            </button>
            <button type="button" onClick={() => setEditando({})} className={BOTAO_SECUNDARIO}>
              <Plus size={18} strokeWidth={2} />
              Novo cartão
            </button>
            {/* Desabilitado quando não há nada vencido, em vez de abrir o
                modo de estudo para dizer que não há nada: era um beco de dois
                cliques e uma troca de tela. */}
            <button
              type="button"
              disabled={vencidos === 0}
              onClick={() => setEstudando(true)}
              className={BOTAO_PRIMARIO}
            >
              <Play size={18} strokeWidth={2} />
              {vencidos > 0 ? `Estudar ${vencidos}` : "Tudo em dia"}
            </button>
          </div>
        </div>
      </div>

      {isLoading && <div className="h-[200px] animate-pulse rounded-card bg-line-soft" />}

      {!isLoading && (isError || isPaused) && !cartoes && (
        <EstadoFalha
          mensagem="Não deu para carregar este baralho. Pode ser a conexão."
          pausado={isPaused}
          onTentarDeNovo={() => void refetch()}
        />
      )}

      {cartoes?.length === 0 && (
        <EstadoVazio
          mensagem="Baralho vazio. Um cartão é uma pergunta na frente e a resposta no verso."
          cta={{ label: "Escrever o primeiro", onClick: () => setEditando({}) }}
        />
      )}

      {!!cartoes?.length && (
        <ul className="flex flex-col gap-2.5">
          {cartoes.map((c) => (
            <li key={c.id} className="flex items-start gap-4 rounded-card border border-line bg-surface p-4">
              <div className="min-w-0 flex-1">
                <p className="text-corpo font-semibold text-ink">{c.frente}</p>
                <p className="mt-1 text-corpo text-ink-2">{c.verso}</p>
              </div>
              <div className="flex shrink-0 gap-1">
                <button
                  type="button"
                  onClick={() => setEditando({ cartao: c })}
                  aria-label="Editar cartão"
                  className="rounded-btn p-1.5 text-muted transition duration-hover hover:bg-ground hover:text-ink"
                >
                  <Pencil size={14} strokeWidth={2} />
                </button>
                <button
                  type="button"
                  onClick={() => apagar.mutate(c.id)}
                  aria-label="Apagar cartão"
                  className="rounded-btn p-1.5 text-muted transition duration-hover hover:bg-ground hover:text-t1"
                >
                  <Trash2 size={14} strokeWidth={2} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <AjustarBaralho
        aberto={ajustando}
        baralhoId={baralhoId}
        nomeAtual={data?.baralho.nome ?? ""}
        pastaAtualId={data?.baralho.pasta_id}
        onFechar={() => setAjustando(false)}
        onSalvo={recarregar}
      />
      <FormularioCartao
        aberto={editando !== null}
        cartao={editando?.cartao}
        baralhoId={baralhoId}
        onFechar={() => setEditando(null)}
        onSalvo={recarregar}
      />
    </div>
  );
}

function FormularioCartao({
  aberto, cartao, baralhoId, onFechar, onSalvo,
}: {
  aberto: boolean;
  cartao?: Cartao;
  baralhoId: number;
  onFechar: () => void;
  onSalvo: () => void;
}) {
  const [frente, setFrente] = useState("");
  const [verso, setVerso] = useState("");
  const [salvando, setSalvando] = useState(false);
  // Remonta com o cartão em edição a cada abertura.
  const chave = `${aberto}-${cartao?.id ?? "novo"}`;
  const [ultimaChave, setUltimaChave] = useState(chave);
  if (chave !== ultimaChave) {
    setUltimaChave(chave);
    setFrente(cartao?.frente ?? "");
    setVerso(cartao?.verso ?? "");
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!frente.trim() || !verso.trim()) return;
    setSalvando(true);
    try {
      if (cartao) await atualizarCartao(cartao.id, frente, verso);
      else await criarCartao(baralhoId, frente, verso);
      onSalvo();
      // Escrever cartão é trabalho em série: salvar um cartão novo limpa os
      // campos e mantém a caixa aberta, em vez de fechar e pedir outro clique.
      if (cartao) onFechar();
      else {
        setFrente("");
        setVerso("");
      }
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Dialog titulo={cartao ? "Editar cartão" : "Novo cartão"} aberto={aberto} onFechar={onFechar}>
      <form onSubmit={salvar} className="flex flex-col gap-4">
        <label htmlFor="cartao-frente" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Frente</span>
          <textarea
            id="cartao-frente"
            value={frente}
            onChange={(e) => setFrente(e.target.value)}
            maxLength={2000}
            rows={3}
            autoFocus
            placeholder="Corrimento branco, grumoso, com prurido intenso"
            className={`${CAMPO} h-auto py-2 leading-normal`}
          />
        </label>
        <label htmlFor="cartao-verso" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Verso</span>
          <textarea
            id="cartao-verso"
            value={verso}
            onChange={(e) => setVerso(e.target.value)}
            maxLength={2000}
            rows={3}
            placeholder="Candidíase vulvovaginal"
            className={`${CAMPO} h-auto py-2 leading-normal`}
          />
        </label>
        <button
          type="submit"
          disabled={salvando || !frente.trim() || !verso.trim()}
          className={`${BOTAO_PRIMARIO} w-full`}
        >
          {salvando ? "Salvando…" : cartao ? "Salvar" : "Adicionar e escrever outro"}
        </button>
      </form>
    </Dialog>
  );
}


function AjustarBaralho({
  aberto, baralhoId, nomeAtual, pastaAtualId, onFechar, onSalvo,
}: {
  aberto: boolean;
  baralhoId: number;
  nomeAtual: string;
  pastaAtualId: number | undefined;
  onFechar: () => void;
  onSalvo: () => void;
}) {
  const { data } = useQuery({ queryKey: ["pastas"], queryFn: listarPastas, enabled: aberto });
  const [nome, setNome] = useState(nomeAtual);
  const [pastaId, setPastaId] = useState<number | undefined>(pastaAtualId);
  const [salvando, setSalvando] = useState(false);
  // Remonta com os valores atuais a cada abertura: fechar sem salvar descarta.
  const chave = `${aberto}-${nomeAtual}-${pastaAtualId}`;
  const [ultimaChave, setUltimaChave] = useState(chave);
  if (chave !== ultimaChave) {
    setUltimaChave(chave);
    setNome(nomeAtual);
    setPastaId(pastaAtualId);
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!pastaId) return;
    setSalvando(true);
    try {
      // Nome e pasta no mesmo PATCH: mover é trocar a pasta, e renomear ao
      // mesmo tempo é o caso comum de "reorganizei isto aqui".
      await moverBaralho(baralhoId, pastaId, nome);
      onSalvo();
      onFechar();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Dialog titulo="Ajustar baralho" aberto={aberto} onFechar={onFechar}>
      <form onSubmit={salvar} className="flex flex-col gap-4">
        <label htmlFor="baralho-novo-nome" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Nome</span>
          <input
            id="baralho-novo-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            maxLength={60}
            autoFocus
            className={CAMPO}
          />
        </label>
        <label htmlFor="baralho-pasta" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Pasta</span>
          <div className="flex items-center gap-2">
            <span
              className={`h-8 w-1.5 shrink-0 rounded-pill ${fundoDaPasta(
                data?.pastas.find((p) => p.id === pastaId)?.cor,
              )}`}
              aria-hidden="true"
            />
            <select
              id="baralho-pasta"
              value={pastaId ?? ""}
              onChange={(e) => setPastaId(Number(e.target.value))}
              className={CAMPO}
            >
              {(data?.pastas ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </div>
        </label>
        <button type="submit" disabled={salvando} className={`${BOTAO_PRIMARIO} w-full`}>
          {salvando ? "Salvando…" : "Salvar"}
        </button>
      </form>
    </Dialog>
  );
}
