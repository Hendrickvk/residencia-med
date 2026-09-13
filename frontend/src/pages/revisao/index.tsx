import { RotateCcw } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { API_URL } from "../../lib/api";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../../lib/estilos";
import { BarraFoco } from "../../lib/foco";
import { avaliarRevisao, useLevaRevisao } from "../../lib/revisao";
import type { Questao } from "../../lib/types";
import { AlternativaLinha } from "../praticar/AlternativaLinha";

// Índice de JS Date.getDay() (0=domingo), diferente do weekday() do Python
// que o app.py original usava (0=segunda) — cuidado se algum dia comparar.
const NOME_DIA_SEMANA = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

// DESIGN_TRIAGEM.md §6: cada intervalo leva a cor do nível equivalente.
const OPCOES_INTERVALO = [
  { label: "Errei", prazo: "10 min", qualidade: 1, cor: "bg-t1" },
  { label: "Difícil", prazo: "1 dia", qualidade: 3, cor: "bg-t2" },
  { label: "Bom", prazo: "4 dias", qualidade: 4, cor: "bg-t4" },
  { label: "Fácil", prazo: "10 dias", qualidade: 5, cor: "bg-t5" },
];

export default function Revisao() {
  const { data, isLoading, refetch } = useLevaRevisao();
  const navigate = useNavigate();
  // Cópia local só depois que o aluno muda a ordem ("Errei" reinsere o caso
  // mais adiante); até lá a fila exibida é a do servidor.
  const [filaSessao, setFilaSessao] = useState<Questao[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [revelado, setRevelado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  function recomecar() {
    setIdx(0);
    setRevelado(false);
    setFilaSessao(null);
    refetch();
  }

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-[840px] flex-col gap-5">
        <div className="h-[72px] w-32 animate-pulse rounded-card bg-line-soft" />
        <div className="h-[360px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  const fila = filaSessao ?? data?.fila ?? [];
  const restantes = Math.max(fila.length - idx, 0);
  const q = fila[idx];

  async function avaliar(qualidade: number) {
    if (!q) return;
    setEnviando(true);
    try {
      await avaliarRevisao(q.id, qualidade);
    } finally {
      setEnviando(false);
      if (qualidade === 1) {
        // "Errei" volta a aparecer daqui a pouco NESTA sessão: o backend já
        // agenda de verdade pra 10 minutos (repeticao_espacada.py), mas a
        // fila que o cliente já buscou não saberia disso sozinha — sem
        // isso, o item some da sessão de hoje inteira.
        const copia = [...fila];
        copia.splice(Math.min(idx + 4, copia.length), 0, q);
        setFilaSessao(copia);
      }
      setIdx((i) => i + 1);
      setRevelado(false);
    }
  }

  if (!q) {
    return (
      <div className="mx-auto max-w-[840px]">
        <EstadoVazio
          mensagem={
            data?.proxima_leva
              ? `Nenhuma revisão vencida hoje. As próximas ${data.proxima_leva.total} vencem ${
                  NOME_DIA_SEMANA[new Date(`${data.proxima_leva.dia}T00:00:00`).getDay()]
                }.`
              : "Nenhuma revisão vencida hoje."
          }
          cta={{ label: "Praticar casos novos", onClick: () => navigate("/praticar") }}
        />
      </div>
    );
  }

  const recorte = [q.area, q.subtopico].filter(Boolean).join(" · ");

  return (
    <>
      <BarraFoco>
        <span className="hidden text-[14.5px] text-ink-2 xl:block">Revisão espaçada</span>
        <span className="ml-auto shrink-0 text-[14px] font-semibold tabular-nums">
          {restantes} restante{restantes !== 1 ? "s" : ""}
        </span>
        <button
          type="button"
          onClick={recomecar}
          className="flex h-9 shrink-0 items-center gap-1.5 rounded-btn border border-line px-3 text-[14px] font-medium text-ink-2 transition duration-hover hover:border-muted hover:text-ink"
        >
          <RotateCcw size={15} strokeWidth={2} />
          Recomeçar fila
        </button>
      </BarraFoco>

      <div className="mx-auto flex max-w-[840px] flex-col gap-5">
        <div className="flex items-end justify-between gap-6">
          <div className="flex flex-col gap-1">
            <span className="rotulo text-muted">Caso</span>
            <span className="num-lg">{String(idx + 1).padStart(2, "0")}</span>
          </div>
          {recorte && <span className="text-right text-[15px] font-semibold">{recorte}</span>}
        </div>

        <div className="flex flex-col gap-6 rounded-caso border border-line bg-surface p-6 md:px-11 md:py-9">
          <p className="max-w-[68ch] text-enunciado text-ink">{q.enunciado}</p>
          {q.tem_imagem && (
            <img src={`${API_URL}/questoes/${q.id}/imagem`} alt="Imagem do caso" className="max-w-full rounded-card border border-line" />
          )}

          {!revelado ? (
            <button type="button" onClick={() => setRevelado(true)} className={`${BOTAO_PRIMARIO} w-full`}>
              Mostrar resposta
            </button>
          ) : (
            <>
              <div className="flex flex-col gap-2">
                {Object.entries(q.alternativas).map(([letra, texto]) => (
                  <AlternativaLinha
                    key={letra}
                    letra={letra}
                    texto={texto}
                    estado={letra === q.resposta_correta ? "correta" : "neutra"}
                    disabled
                  />
                ))}
              </div>

              {q.explicacao && (
                <div className="flex flex-col gap-3 border-t border-line-soft pt-6">
                  <span className="rotulo text-muted">Discussão do caso</span>
                  <p className="max-w-[66ch] text-[16.5px] leading-[1.7] text-ink-2">{q.explicacao}</p>
                </div>
              )}

              <div className="flex flex-col gap-3 border-t border-line-soft pt-6">
                <span className="text-apoio text-muted">Quão fácil foi lembrar?</span>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {OPCOES_INTERVALO.map((op) => (
                    <button
                      key={op.qualidade}
                      type="button"
                      disabled={enviando}
                      onClick={() => avaliar(op.qualidade)}
                      className={BOTAO_SECUNDARIO}
                    >
                      <span className={`h-2.5 w-2.5 shrink-0 rounded-[2px] ${op.cor}`} aria-hidden="true" />
                      {op.label} — {op.prazo}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
