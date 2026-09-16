import { useEffect, useState } from "react";
import { TELAS, ehConvidada, jaViu, marcarComoVista } from "../lib/brincadeira";
import { BOTAO_PRIMARIO } from "../lib/estilos";
import { Dialog } from "./Dialog";

// Sequência de telas que só aparece para uma convidada específica, uma vez por
// navegador (lib/brincadeira.ts). Para qualquer outra conta, não renderiza nada.
export function BrincadeiraBoasVindas({ email }: { email: string | undefined }) {
  const [aberto, setAberto] = useState(false);
  const [indice, setIndice] = useState(0);

  useEffect(() => {
    if (!email || jaViu()) return;
    let cancelado = false;
    ehConvidada(email)
      .then((sim) => {
        if (sim && !cancelado) setAberto(true);
      })
      .catch(() => {});
    return () => {
      cancelado = true;
    };
  }, [email]);

  function encerrar() {
    // Fechar no meio também encerra: a piada não insiste.
    marcarComoVista();
    setAberto(false);
  }

  function avancar() {
    if (indice + 1 >= TELAS.length) {
      encerrar();
      return;
    }
    setIndice(indice + 1);
  }

  const tela = TELAS[indice];

  return (
    <Dialog titulo={tela.titulo} aberto={aberto} onFechar={encerrar}>
      <p className="text-corpo text-ink-2 [text-wrap:pretty]">{tela.texto}</p>
      <div className="mt-6 flex items-center justify-between gap-3">
        <span className="text-apoio tabular-nums text-muted">
          {indice + 1} de {TELAS.length}
        </span>
        <button type="button" onClick={avancar} className={BOTAO_PRIMARIO}>
          {tela.botao}
        </button>
      </div>
    </Dialog>
  );
}
