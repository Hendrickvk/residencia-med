import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO, CAMPO } from "../../lib/estilos";
import { textoProva } from "../../lib/format";
import type { Me } from "../../lib/types";

// A data que alimenta a contagem regressiva da barra superior e do Painel.
// Existia no banco desde sempre e não tinha onde ser definida — este bloco é
// a primeira vez que ela sai do `UPDATE` manual.
export function ProvaAlvo({ me }: { me: Me | undefined }) {
  const queryClient = useQueryClient();
  const [data, setData] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const carregado = useRef(false);

  useEffect(() => {
    if (!me || carregado.current) return;
    carregado.current = true;
    setData(me.prova_alvo ?? "");
  }, [me]);

  async function gravar(valor: string | null) {
    setErro(null);
    setSalvando(true);
    try {
      await api.patch("/me/prova", { data: valor });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não deu para salvar a data agora.");
    } finally {
      setSalvando(false);
    }
  }

  const contagem = textoProva(data || null);

  return (
    <section className="flex flex-col gap-5 rounded-card border border-line bg-surface p-6">
      <h2 className="text-bloco text-ink">A sua prova</h2>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          gravar(data || null);
        }}
        className="flex flex-col gap-5"
      >
        <label htmlFor="prova-data" className="flex flex-col gap-1.5">
          <span className="rotulo text-muted">Data da prova</span>
          {/* `type="date"` de propósito: o calendário nativo já resolve
              formato, fuso e teclado no celular, e nenhuma biblioteca faria
              melhor. */}
          <input
            id="prova-data"
            type="date"
            value={data}
            onChange={(e) => setData(e.target.value)}
            className={CAMPO}
          />
          <span className="text-apoio text-muted">
            {contagem ?? "Sem data, a barra superior não mostra contagem."}
          </span>
        </label>

        {erro && (
          <p role="alert" className="text-apoio font-medium text-t1">
            {erro}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <button type="submit" disabled={salvando} className={BOTAO_PRIMARIO}>
            {salvando ? "Salvando…" : "Salvar data"}
          </button>
          {me?.prova_alvo && (
            <button
              type="button"
              disabled={salvando}
              onClick={() => {
                setData("");
                gravar(null);
              }}
              className={BOTAO_SECUNDARIO}
            >
              Tirar a data
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
