import { useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { BOTAO_PRIMARIO } from "../lib/estilos";
import { NOVIDADE_ATUAL, ROTULO_TIPO, type Novidade } from "../lib/novidades";
import { Dialog } from "./Dialog";

interface Props {
  aberto: boolean;
  entradas: Novidade[];
  onFechar: () => void;
}

// O que mudou na plataforma, numa caixa. Sem cor de triagem: a escala só
// codifica nível de aproveitamento (DESIGN_TRIAGEM.md §2), e "novo" não é um
// nível. Os tipos viram rótulo em caixa alta, que é como o sistema marca
// metadado.
export function Novidades({ aberto, entradas, onFechar }: Props) {
  const queryClient = useQueryClient();

  function fechar() {
    onFechar();
    // Fecha primeiro, grava depois: a caixa não pode esperar a rede para
    // sumir, e se a gravação falhar o pior que acontece é a novidade aparecer
    // de novo na próxima visita.
    api
      .patch("/me/novidades", { visto: NOVIDADE_ATUAL })
      .then(() => queryClient.invalidateQueries({ queryKey: ["me"] }))
      .catch(() => {});
  }

  return (
    <Dialog titulo="O que mudou" aberto={aberto} onFechar={fechar}>
      <div className="flex flex-col gap-5">
        {entradas.map((entrada) => (
          <section key={entrada.id} className="flex flex-col gap-2.5">
            <div>
              <div className="rotulo text-muted">{entrada.data}</div>
              <h3 className="mt-0.5 text-bloco text-ink">{entrada.titulo}</h3>
            </div>
            <ul className="flex flex-col gap-2.5">
              {entrada.itens.map((item, i) => (
                <li key={i} className="flex gap-2.5">
                  <span className="rotulo mt-1 w-[76px] shrink-0 whitespace-nowrap text-muted">
                    {ROTULO_TIPO[item.tipo]}
                  </span>
                  <span className="text-corpo text-ink-2">{item.texto}</span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      <button type="button" onClick={fechar} className={`${BOTAO_PRIMARIO} mt-6 w-full`}>
        Voltar ao estudo
      </button>
    </Dialog>
  );
}
