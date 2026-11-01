import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { AvisoGabaritoProvisorio } from "../../components/AvisoGabaritoProvisorio";
import { TextoEnunciado } from "../../components/TextoEnunciado";
import { CriarCartao } from "../../components/CriarCartao";
import { ImagemQuestao } from "../../components/ImagemQuestao";
import { RelatarErro } from "../../components/RelatarErro";
import { TemaDoCaso } from "../../components/TemaDoCaso";
import { TextoDiscussao } from "../../components/TextoDiscussao";
import type { Questao, RespondidaResumo } from "../../lib/types";
import { AlternativaLinha, type EstadoAlternativa } from "./AlternativaLinha";

const LETRAS = ["A", "B", "C", "D", "E"];

// Rever o que acabou de responder, como a "Revisão completa" do resultado do simulado. Tudo
// vem do lote da própria sessão: nada novo sai do servidor, então a cota diária não muda.
export function CasosDaSessao({ respondidas, questoes }: { respondidas: RespondidaResumo[]; questoes: Questao[] }) {
  const porId = new Map(questoes.map((q) => [q.id, q]));
  const casos = respondidas.flatMap((r) => {
    const questao = porId.get(r.id);
    return questao ? [{ r, questao }] : [];
  });
  const erros = casos.filter((c) => !c.r.correta).length;
  // Começa nos erros, que é onde rever rende mais.
  const [soErros, setSoErros] = useState(erros > 0);
  const [abertos, setAbertos] = useState<Set<number>>(new Set());
  if (casos.length === 0) return null;
  const visiveis = soErros ? casos.filter((c) => !c.r.correta) : casos;

  function alternar(id: number) {
    setAbertos((prev) => {
      const novo = new Set(prev);
      if (novo.has(id)) novo.delete(id);
      else novo.add(id);
      return novo;
    });
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-bloco">Rever os casos</h2>
        {erros > 0 && erros < casos.length && (
          <div className="inline-flex gap-0.5 rounded-card bg-line-soft p-[3px]" role="group" aria-label="Quais casos mostrar">
            {[
              { valor: true, rotulo: `Erros (${erros})` },
              { valor: false, rotulo: `Todos (${casos.length})` },
            ].map((opcao) => (
              <button
                key={opcao.rotulo}
                type="button"
                aria-pressed={soErros === opcao.valor}
                onClick={() => setSoErros(opcao.valor)}
                className={`flex h-8 items-center rounded-col border px-3 text-[14px] font-semibold tabular-nums transition-colors duration-hover ${
                  soErros === opcao.valor ? "border-line bg-surface text-ink" : "border-transparent text-muted hover:text-ink"
                }`}
              >
                {opcao.rotulo}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        {visiveis.map(({ r, questao: q }) => {
          const aberto = abertos.has(q.id);
          const numero = casos.findIndex((c) => c.questao.id === q.id) + 1;
          return (
            <div
              key={q.id}
              className={`rounded-card border bg-surface transition-colors duration-hover ${aberto ? "border-muted" : "border-line"}`}
            >
              <button
                type="button"
                onClick={() => alternar(q.id)}
                aria-expanded={aberto}
                className={`grid w-full grid-cols-[76px_auto_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 text-left transition-colors duration-hover hover:bg-ground ${
                  aberto ? "rounded-t-card" : "rounded-card"
                }`}
              >
                {r.correta ? (
                  <span className="rotulo rounded-etq bg-t4 px-2 py-1 text-center text-[12px] text-t4-on">Certo</span>
                ) : (
                  <span className="rotulo rounded-etq bg-t1 px-2 py-1 text-center text-[12px] text-t1-on">Errado</span>
                )}
                <span className="text-[14px] font-semibold tabular-nums">Caso {numero}</span>
                <span className="truncate text-corpo text-ink-2">{q.enunciado}</span>
                <ChevronDown
                  size={16}
                  strokeWidth={2}
                  className={`shrink-0 text-muted transition-transform duration-desliza ease-suave ${aberto ? "rotate-180" : ""}`}
                />
              </button>
              {aberto && (
                <div className="flex animate-entrar flex-col gap-5 border-t border-line-soft p-5 md:px-11 md:py-7">
                  <TextoEnunciado texto={q.enunciado} />
                  {q.tem_imagem && <ImagemQuestao questaoId={q.id} alt="Imagem da questão" />}
                  <div className="flex flex-col gap-2">
                    {LETRAS.filter((letra) => letra in q.alternativas).map((letra) => {
                      let estado: EstadoAlternativa = "neutra";
                      if (letra === q.resposta_correta) estado = "correta";
                      else if (letra === r.alternativa) estado = "errada";
                      return <AlternativaLinha key={letra} letra={letra} texto={q.alternativas[letra]} estado={estado} disabled />;
                    })}
                  </div>
                  <div className="flex flex-col gap-2 border-t border-line-soft pt-5">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                      <span className="rotulo text-muted">Discussão do caso</span>
                      <span className="text-apoio text-muted">
                        {/* Sessão salva antes de guardar a alternativa não sabe qual foi. */}
                        {r.alternativa && `Você marcou ${r.alternativa}${r.chute ? ", no chute" : ""}. `}
                        Resposta correta: {q.resposta_correta}.
                      </span>
                    </div>
                    {q.provas?.some((p) => p.gabarito_preliminar) && <AvisoGabaritoProvisorio />}
                    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                      <TemaDoCaso tema={q.subtopico} />
                      <div className="flex flex-wrap items-center gap-4">
                        <CriarCartao questaoId={q.id} respostaCorreta={q.alternativas[q.resposta_correta]} />
                        <RelatarErro questaoId={q.id} />
                      </div>
                    </div>
                    {q.explicacao && <TextoDiscussao texto={q.explicacao} />}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
