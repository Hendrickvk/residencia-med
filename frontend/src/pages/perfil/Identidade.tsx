import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Avatar } from "../../components/Avatar";
import { api, ApiError } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";
import { FotoInvalida, MIME_SAIDA, prepararFoto } from "../../lib/foto";
import { CORES_PERFIL, COR_PADRAO } from "../../lib/perfil";
import type { Me } from "../../lib/types";

// Foto, nome e cor. A foto salva na hora (é uma escrita de verdade e ver o
// avatar mudar é a confirmação); nome e cor só no "Salvar".
export function Identidade({ me }: { me: Me | undefined }) {
  const queryClient = useQueryClient();
  const [nome, setNome] = useState("");
  const [cor, setCor] = useState(COR_PADRAO);
  const [salvo, setSalvo] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [foto, setFoto] = useState<"parado" | "enviando">("parado");
  const [erro, setErro] = useState<string | null>(null);
  const campoArquivo = useRef<HTMLInputElement>(null);
  // O formulário nasce vazio e recebe os valores quando `/me` chega. Sem isto
  // a página carregaria com os campos em branco por um instante e escreveria
  // vazio por cima se ela fosse rápida no "Salvar".
  const carregado = useRef(false);

  useEffect(() => {
    if (!me || carregado.current) return;
    carregado.current = true;
    setNome(me.nome ?? "");
    setCor(me.cor_perfil);
  }, [me]);

  async function trocarFoto(arquivo: File | undefined) {
    if (!arquivo) return;
    setErro(null);
    setFoto("enviando");
    try {
      const dados = await prepararFoto(arquivo);
      await api.put("/me/foto", { dados, mime: MIME_SAIDA });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    } catch (e) {
      if (e instanceof FotoInvalida) setErro(e.message);
      else setErro(e instanceof ApiError ? e.message : "Não deu para enviar a foto agora.");
    } finally {
      setFoto("parado");
      // Sem isto, escolher o mesmo arquivo de novo não dispara `change`.
      if (campoArquivo.current) campoArquivo.current.value = "";
    }
  }

  async function removerFoto() {
    setFoto("enviando");
    try {
      await api.delete("/me/foto");
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    } finally {
      setFoto("parado");
    }
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      await api.patch("/me/perfil", { nome, cor });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      setSalvo(true);
      setTimeout(() => setSalvo(false), 2400);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não deu para salvar agora.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <section className="flex flex-col gap-5 rounded-card border border-line bg-surface p-6">
      <h2 className="text-bloco text-ink">Identidade</h2>

      <div className="flex items-center gap-4">
        {/* Prévia com a cor escolhida agora, não a salva. */}
        <Avatar me={me && { ...me, cor_perfil: cor }} tamanho={72} />
        <div className="flex flex-wrap gap-2">
          <input
            ref={campoArquivo}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => trocarFoto(e.target.files?.[0])}
          />
          <button
            type="button"
            disabled={foto === "enviando"}
            onClick={() => campoArquivo.current?.click()}
            className={BOTAO_SECUNDARIO}
          >
            {foto === "enviando" ? "Enviando…" : me?.foto_versao ? "Trocar foto" : "Escolher foto"}
          </button>
          {me?.foto_versao && (
            <button type="button" disabled={foto === "enviando"} onClick={removerFoto} className={BOTAO_SECUNDARIO}>
              Remover
            </button>
          )}
        </div>
      </div>

      <form onSubmit={salvar} className="flex flex-col gap-5">
        <label htmlFor="perfil-nome" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Como te chamar</span>
          <input
            id="perfil-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            maxLength={40}
            placeholder={me?.email}
            className={CAMPO}
          />
          <span className="text-apoio text-muted">Em branco, fica o seu e-mail.</span>
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="rotulo mb-1 text-muted">Cor do avatar</legend>
          <div className="flex flex-wrap gap-2.5">
            {CORES_PERFIL.map((opcao) => (
              <button
                key={opcao.chave}
                type="button"
                onClick={() => setCor(opcao.chave)}
                aria-label={opcao.nome}
                aria-pressed={cor === opcao.chave}
                // A escolhida ganha anel de tinta, não borda colorida: a cor
                // do botão já é a informação, e um segundo tom competiria.
                className={`h-9 w-9 rounded-pill transition duration-hover ease-brand active:scale-[0.94] ${opcao.fundo} ${
                  cor === opcao.chave ? "ring-2 ring-ink ring-offset-2 ring-offset-surface" : ""
                }`}
              />
            ))}
          </div>
          <span className="text-apoio text-muted">Aparece atrás da inicial, e enquanto a foto carrega.</span>
        </fieldset>

        {erro && (
          <p role="alert" className="text-apoio font-medium text-t1">
            {erro}
          </p>
        )}

        <div className="flex items-center gap-3">
          <button type="submit" disabled={salvando} className={BOTAO_PRIMARIO}>
            {salvando ? "Salvando…" : "Salvar"}
          </button>
          {salvo && <span className="animate-entrar text-apoio font-medium text-t4">Salvo.</span>}
        </div>
      </form>
    </section>
  );
}
