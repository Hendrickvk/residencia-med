import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { useMe } from "../lib/auth";
import { BOTAO_PRIMARIO, CAMPO } from "../lib/estilos";
import { CORES_PERFIL, COR_PADRAO } from "../lib/perfil";
import { Dialog } from "./Dialog";

interface Props {
  aberto: boolean;
  onFechar: () => void;
}

export function Perfil({ aberto, onFechar }: Props) {
  const { data: me } = useMe();
  const queryClient = useQueryClient();
  // Rascunho local: o campo não pode piscar de volta ao valor salvo enquanto
  // ela digita, e fechar sem salvar tem de descartar de verdade. A chave por
  // abertura remonta o estado com o valor atual do servidor.
  const [nome, setNome] = useState(me?.nome ?? "");
  const [cor, setCor] = useState(me?.cor_perfil ?? COR_PADRAO);
  const [salvando, setSalvando] = useState(false);

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await api.patch("/me/perfil", { nome, cor });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
      onFechar();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Dialog titulo="Seu perfil" aberto={aberto} onFechar={onFechar}>
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
          <span className="text-apoio text-muted">
            Aparece no menu da conta. Em branco, fica o seu e-mail.
          </span>
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
        </fieldset>

        <button type="submit" disabled={salvando} className={`${BOTAO_PRIMARIO} w-full`}>
          {salvando ? "Salvando…" : "Salvar"}
        </button>
      </form>
    </Dialog>
  );
}
