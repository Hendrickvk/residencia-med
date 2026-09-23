import { useQueryClient } from "@tanstack/react-query";
import { Flag, ImageIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EstadoFalha } from "../../components/EstadoFalha";
import { EstadoVazio } from "../../components/EstadoVazio";
import { api } from "../../lib/api";
import { BOTAO_PRIMARIO } from "../../lib/estilos";
import type { QuestaoMarcada } from "../../lib/types";

interface Props {
  questoes: QuestaoMarcada[] | undefined;
  isLoading: boolean;
  isError: boolean;
  isPaused: boolean;
  onTentarDeNovo: () => void;
}

// A lista que faltava: marcar uma questão com "M" existia desde sempre, e não
// havia tela nenhuma que a mostrasse de volta.
//
// Aqui só o enunciado e a classificação — o gabarito e a explicação não saem
// por esta porta. Rever de verdade é pelo botão, que abre uma sessão de
// Praticar só com as marcadas e passa pelo teto diário como qualquer outra.
export function Marcadas({ questoes, isLoading, isError, isPaused, onTentarDeNovo }: Props) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  async function desmarcar(id: number) {
    await api.delete(`/questoes/${id}/marcar`);
    await queryClient.invalidateQueries({ queryKey: ["marcadas"] });
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-bloco text-ink">Questões marcadas</h2>
          <p className="mt-0.5 text-apoio text-muted">
            O que você guardou para rever, da mais recente para a mais antiga.
          </p>
        </div>
        {!!questoes?.length && (
          <button
            type="button"
            onClick={() =>
              // Mesmo caminho do "Praticar 10" do Painel: estado de navegação
              // e a sessão já começa, sem passar pelo Configurador.
              navigate("/praticar", { state: { iniciarImediato: true, apenasMarcadas: true } })
            }
            className={BOTAO_PRIMARIO}
          >
            Praticar as {questoes.length}
          </button>
        )}
      </div>

      {isLoading && <div className="h-[200px] animate-pulse rounded-card bg-line-soft" />}

      {/* Falha não é vazio: sem esta ramificação, uma conexão que caiu diria
          que ela nunca marcou nada. */}
      {!isLoading && (isError || isPaused) && !questoes && (
        <EstadoFalha
          mensagem="Não deu para carregar as suas marcadas. Pode ser a conexão."
          pausado={isPaused}
          onTentarDeNovo={onTentarDeNovo}
        />
      )}

      {questoes?.length === 0 && (
        <EstadoVazio mensagem="Você ainda não marcou nenhuma questão. Durante um caso, a tecla M guarda ele aqui." />
      )}

      {!!questoes?.length && (
        <ul className="flex flex-col gap-2.5">
          {questoes.map((q) => (
            <li
              key={q.id}
              className="flex flex-col gap-2 rounded-card border border-line bg-surface p-4 sm:flex-row sm:items-start sm:gap-4"
            >
              <div className="min-w-0 flex-1">
                <div className="rotulo flex flex-wrap items-center gap-x-2 gap-y-1 text-muted">
                  <span>{q.area}</span>
                  {q.tema && <span>· {q.tema}</span>}
                  {q.banca && (
                    <span>
                      · {q.banca}
                      {q.ano ? ` ${q.ano}` : ""}
                    </span>
                  )}
                  {q.tem_imagem && <ImageIcon size={13} strokeWidth={2} aria-label="tem figura" />}
                </div>
                {/* Só o enunciado, cortado: a lista é para reconhecer a
                    questão, não para responder a partir dela. */}
                <p className="mt-1.5 line-clamp-2 text-corpo text-ink-2">{q.enunciado}</p>
              </div>
              <button
                type="button"
                onClick={() => desmarcar(q.id)}
                className="flex shrink-0 items-center gap-1.5 self-start rounded-btn px-2 py-1.5 text-apoio text-muted transition duration-hover hover:bg-ground hover:text-ink"
              >
                <Flag size={14} strokeWidth={2} />
                Desmarcar
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
