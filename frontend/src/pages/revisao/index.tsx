import { RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EstadoVazio } from "../../components/EstadoVazio";
import { avaliarRevisao, useLevaRevisao } from "../../lib/revisao";
import type { Questao } from "../../lib/types";

// Índice de JS Date.getDay() (0=domingo), diferente do weekday() do Python
// que o app.py original usava (0=segunda) — cuidado se algum dia comparar.
const NOME_DIA_SEMANA = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

const OPCOES_INTERVALO: { label: string; qualidade: number }[] = [
  { label: "Errei — 10 min", qualidade: 1 },
  { label: "Difícil — 1 dia", qualidade: 3 },
  { label: "Bom — 4 dias", qualidade: 4 },
  { label: "Fácil — 10 dias", qualidade: 5 },
];

export default function Revisao() {
  const { data, isLoading, refetch } = useLevaRevisao();
  const navigate = useNavigate();
  const [filaSessao, setFilaSessao] = useState<Questao[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [revelado, setRevelado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (data) setFilaSessao(data.fila);
  }, [data]);

  function recomecar() {
    setIdx(0);
    setRevelado(false);
    setFilaSessao(null);
    refetch();
  }

  if (isLoading) {
    return <div className="mx-auto h-72 max-w-lg animate-pulse rounded-panel bg-line/40" />;
  }

  const fila = filaSessao ?? [];
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
        setFilaSessao((atual) => {
          if (!atual) return atual;
          const copia = [...atual];
          copia.splice(Math.min(idx + 4, copia.length), 0, q);
          return copia;
        });
      }
      setIdx((i) => i + 1);
      setRevelado(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-apoio text-ink-500">
          {restantes} ite{restantes === 1 ? "m" : "ns"} restante{restantes !== 1 && "s"}
        </p>
        <button
          type="button"
          onClick={recomecar}
          className="flex items-center gap-1.5 text-apoio text-ink-500 transition-hover hover:text-ink-700"
        >
          <RotateCcw size={14} strokeWidth={1.5} />
          Recomeçar fila
        </button>
      </div>

      {!q ? (
        <EstadoVazio
          mensagem={
            data?.proxima_leva
              ? `Nenhuma revisão vencida hoje. As próximas ${data.proxima_leva.total} vencem ${
                  NOME_DIA_SEMANA[new Date(`${data.proxima_leva.dia}T00:00:00`).getDay()]
                }.`
              : "Nenhuma revisão vencida hoje."
          }
          cta={{ label: "Praticar questões novas", onClick: () => navigate("/praticar") }}
        />
      ) : (
        <div className="mx-auto max-w-lg rounded-panel border border-line bg-surface p-6">
          <p className="text-enunciado text-ink-700">{q.enunciado}</p>

          {!revelado ? (
            <button
              type="button"
              onClick={() => setRevelado(true)}
              className="mt-5 h-10 w-full rounded-btn bg-action text-sm font-medium text-white transition-hover hover:bg-action-hover"
            >
              Mostrar resposta
            </button>
          ) : (
            <div className="mt-5">
              <div className="space-y-2">
                {Object.entries(q.alternativas).map(([letra, texto]) => (
                  <div
                    key={letra}
                    className={`flex min-h-[44px] items-center gap-3 rounded-btn border px-3 text-corpo ${
                      letra === q.resposta_correta
                        ? "border-correct bg-correct-soft text-ink-700"
                        : "border-line text-ink-500"
                    }`}
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-btn border border-current text-apoio font-medium">
                      {letra}
                    </span>
                    {texto}
                  </div>
                ))}
              </div>

              {q.explicacao && (
                <div className="mt-3 rounded-btn border border-line bg-canvas p-3 text-corpo text-ink-700">
                  {q.explicacao}
                </div>
              )}

              <div className="mt-4 text-apoio text-ink-500">Quão fácil foi lembrar?</div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {OPCOES_INTERVALO.map((op) => (
                  <button
                    key={op.qualidade}
                    type="button"
                    disabled={enviando}
                    onClick={() => avaliar(op.qualidade)}
                    className="h-10 rounded-btn border border-line text-apoio text-ink-700 transition-hover hover:border-ink-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {op.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
