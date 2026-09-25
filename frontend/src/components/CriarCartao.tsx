import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Layers } from "lucide-react";
import { useState } from "react";
import { criarBaralho, criarCartao, criarPasta, listarPastas } from "../lib/cartoes";
import { corDeFundo } from "../lib/paleta";
import { BOTAO_PRIMARIO, CAMPO, PRESSAO } from "../lib/estilos";
import { Dialog } from "./Dialog";

const CHAVE_ULTIMO_BARALHO = "conduta:ultimo-baralho";

interface Props {
  questaoId: number;
  /** A alternativa correta, que costuma ser o fato que ela quer no verso. */
  respostaCorreta?: string;
}

// "Virar cartão" na discussão do caso, ao lado de "Relatar erro" — e pelos
// mesmos motivos de lugar: só onde o gabarito já apareceu (Praticar, Revisão e
// resultado do Simulado), **nunca durante a prova**.
//
// O verso já vem preenchido com a alternativa correta, que é o fato; a frente
// fica vazia porque a pista é ela quem inventa, e um enunciado inteiro de 900
// caracteres seria um cartão impossível de responder.
export function CriarCartao({ questaoId, respostaCorreta }: Props) {
  const queryClient = useQueryClient();
  const [aberto, setAberto] = useState(false);
  const [frente, setFrente] = useState("");
  const [verso, setVerso] = useState("");
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Só busca os baralhos quando ela abre: no meio de uma sessão de estudo,
  // ninguém paga por uma requisição que talvez não use.
  const { data } = useQuery({ queryKey: ["pastas"], queryFn: listarPastas, enabled: aberto });
  const baralhos = (data?.pastas ?? []).flatMap((p) =>
    p.baralhos.map((b) => ({ ...b, pasta: p.nome, cor: p.cor })),
  );

  // O último baralho usado vem do `localStorage`: quem está fazendo cartões
  // costuma mandar vários para o mesmo lugar, e escolher toda vez cansa.
  // Conveniência por navegador, então uma aba privada sem storage só cai no
  // primeiro da lista.
  //
  // Derivado durante o render, e não num efeito: o valor sai do que já está em
  // mãos, e um efeito aqui só somaria um render a mais a cada abertura.
  const [ultimoUsado] = useState<number | null>(() => {
    try {
      const bruto = localStorage.getItem(CHAVE_ULTIMO_BARALHO);
      return bruto ? Number(bruto) : null;
    } catch {
      return null;
    }
  });
  const baralhoId =
    escolhido ??
    (baralhos.some((b) => b.id === ultimoUsado) ? ultimoUsado : baralhos[0]?.id ?? null);

  function abrir() {
    setFrente("");
    setVerso(respostaCorreta ?? "");
    setErro(null);
    setAberto(true);
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!baralhoId || !frente.trim() || !verso.trim()) return;
    setSalvando(true);
    setErro(null);
    try {
      await criarCartao(baralhoId, frente, verso, questaoId);
      try {
        localStorage.setItem(CHAVE_ULTIMO_BARALHO, String(baralhoId));
      } catch {
        // Navegador sem storage (aba privada): perder a preferência não é
        // motivo para o cartão não ser salvo.
      }
      setAberto(false);
      setSalvo(true);
    } catch {
      setErro("Não consegui salvar agora. Tente de novo em instantes.");
    } finally {
      setSalvando(false);
    }
  }

  // Depois de salvar, o botão vira confirmação — mesma ideia do "Relatar
  // erro": evita mandar o mesmo cartão três vezes achando que não foi.
  if (salvo) {
    return <span className="text-apoio text-muted">Cartão criado.</span>;
  }

  return (
    <>
      <button
        type="button"
        onClick={abrir}
        className={`inline-flex items-center gap-1.5 self-start text-apoio text-muted transition duration-hover ease-brand hover:text-ink-2 ${PRESSAO}`}
      >
        <Layers size={13} strokeWidth={2} />
        Virar cartão
      </button>

      <Dialog titulo="Novo cartão deste caso" aberto={aberto} onFechar={() => setAberto(false)}>
        {baralhos.length === 0 ? (
          // Mandar ela sair para criar um baralho e voltar seria perder o caso
          // que está na tela. O primeiro baralho nasce aqui mesmo.
          <PrimeiroBaralho onCriado={() => queryClient.invalidateQueries({ queryKey: ["pastas"] })} />
        ) : (
          <form onSubmit={salvar} className="flex flex-col gap-4">
            <label htmlFor="cartao-baralho" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">Baralho</span>
              <div className="flex items-center gap-2">
                <span
                  className="h-8 w-1.5 shrink-0 rounded-pill"
                  style={corDeFundo(baralhos.find((b) => b.id === baralhoId)?.cor, "pasta")}
                  aria-hidden="true"
                />
                <select
                  id="cartao-baralho"
                  value={baralhoId ?? ""}
                  onChange={(e) => setEscolhido(Number(e.target.value))}
                  className={CAMPO}
                >
                  {baralhos.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.pasta} · {b.nome}
                    </option>
                  ))}
                </select>
              </div>
            </label>

            <label htmlFor="cartao-frente-caso" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">Frente</span>
              <textarea
                id="cartao-frente-caso"
                value={frente}
                onChange={(e) => setFrente(e.target.value)}
                maxLength={2000}
                rows={3}
                autoFocus
                placeholder="A pista que deve fazer você lembrar da resposta"
                className={`${CAMPO} h-auto py-2 leading-normal`}
              />
            </label>

            <label htmlFor="cartao-verso-caso" className="flex flex-col gap-1.5">
              <span className="rotulo text-muted">Verso</span>
              <textarea
                id="cartao-verso-caso"
                value={verso}
                onChange={(e) => setVerso(e.target.value)}
                maxLength={2000}
                rows={3}
                className={`${CAMPO} h-auto py-2 leading-normal`}
              />
              <span className="text-apoio text-muted">Já veio com a conduta correta deste caso.</span>
            </label>

            {erro && (
              <p role="alert" className="text-apoio font-medium text-t1">
                {erro}
              </p>
            )}

            <button
              type="submit"
              disabled={salvando || !frente.trim() || !verso.trim()}
              className={`${BOTAO_PRIMARIO} w-full`}
            >
              {salvando ? "Salvando…" : "Criar cartão"}
            </button>
          </form>
        )}
      </Dialog>
    </>
  );
}


function PrimeiroBaralho({ onCriado }: { onCriado: () => void }) {
  const [nome, setNome] = useState("");
  const [criando, setCriando] = useState(false);

  async function criar(e: React.FormEvent) {
    e.preventDefault();
    if (!nome.trim()) return;
    setCriando(true);
    try {
      // Uma pasta genérica junto: pasta é organização, e exigir que ela
      // invente a hierarquia antes do primeiro cartão é pedir demais no meio
      // de uma sessão de estudo. Renomear depois é um clique em Baralhos.
      const pasta = await criarPasta("Meus cartões", "ardosia");
      await criarBaralho(pasta.id, nome);
      onCriado();
    } finally {
      setCriando(false);
    }
  }

  return (
    <form onSubmit={criar} className="flex flex-col gap-4">
      <p className="text-corpo text-ink-2">
        Você ainda não tem baralhos. Dê um nome ao primeiro e o cartão já vai para dentro dele.
      </p>
      <label htmlFor="primeiro-baralho" className="flex flex-col gap-1.5">
        <span className="rotulo text-muted">Nome do baralho</span>
        <input
          id="primeiro-baralho"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          maxLength={60}
          autoFocus
          placeholder="Ginecologia"
          className={CAMPO}
        />
      </label>
      <button type="submit" disabled={criando || !nome.trim()} className={`${BOTAO_PRIMARIO} w-full`}>
        {criando ? "Criando…" : "Criar baralho"}
      </button>
    </form>
  );
}
