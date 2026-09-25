import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";
import { PRESSAO } from "../lib/estilos";
import { usePresenca } from "../lib/movimento";

interface RelatoResolvido {
  id: number;
  questao_id: number;
  parte: string;
  banca: string | null;
  ano: number | null;
  edicao: string | null;
  numero_prova: number | null;
}

// Fecha o ciclo do "Relatar erro": quem apontou um problema fica sabendo que
// ele foi corrigido. Sem essa volta o aluno relata no escuro e para de relatar,
// que é justamente o sinal mais barato de erro de conteúdo que a plataforma tem.
export function RelatoResolvidoAviso() {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["relatos-resolvidos"],
    queryFn: () => api.get<RelatoResolvido[]>("/me/relatos-resolvidos"),
    // Só muda quando o admin corrige algo: não vale ficar perguntando.
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const dispensar = useMutation({
    mutationFn: () => api.post("/me/relatos-resolvidos/vistos"),
    onSuccess: () => queryClient.setQueryData(["relatos-resolvidos"], []),
  });

  const { montado, saindo } = usePresenca(!!data?.length);
  // Na saída a lista já veio vazia: o aviso sai mostrando o que dizia.
  const [lista, setLista] = useState<RelatoResolvido[]>(data ?? []);
  if (data?.length && data !== lista) setLista(data);

  if (!montado) return null;

  const n = lista.length;
  return (
    // Some encolhendo, e não de uma vez: é o primeiro bloco do Painel, e sumir
    // de uma vez puxava a tela inteira para cima num salto. A altura vai por
    // `grid-template-rows` (0fr → 1fr), que anima a altura sem medir. O `-mb-7`
    // anula o vão do Painel (`gap-7`) e o `pb-7` o devolve por dentro, para o
    // vão encolher junto e nada pular quando o aviso desmonta. Curva `brand`
    // (entra e sai devagar), e não `suave`: o que se move é o Painel inteiro
    // subindo, e com `suave` ele andava 87px no primeiro quadro — um salto.
    // 120ms para terminar antes dos 160ms em que o `usePresenca` desmonta.
    <div
      className={`-mb-7 grid transition-[grid-template-rows,opacity] ${
        saindo ? "grid-rows-[0fr] opacity-0 duration-hover ease-brand" : "grid-rows-[1fr]"
      }`}
    >
      <div className="overflow-hidden">
        <div className="pb-7">
          <div
            role="status"
            className="flex animate-entrar items-start gap-3 rounded-card border border-line bg-surface px-4 py-3"
          >
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-pill bg-t5-soft text-t5">
              <Check size={13} strokeWidth={2.5} />
            </span>
            <div className="flex flex-col gap-1">
              <span className="text-corpo text-ink">
                {n === 1
                  ? "A questão que você reportou foi corrigida."
                  : `${n} questões que você reportou foram corrigidas.`}
              </span>
              <span className="text-apoio text-muted">
                {lista
                  .slice(0, 3)
                  .map((r) => `${nomeProva(r)} · ${r.parte.toLowerCase()}`)
                  .join(" · ")}
                {n > 3 && ` · e mais ${n - 3}`}
              </span>
            </div>
            <button
              type="button"
              onClick={() => dispensar.mutate()}
              disabled={dispensar.isPending}
              aria-label="Dispensar aviso"
              className={`ml-auto shrink-0 text-muted transition duration-hover ease-brand hover:text-ink ${PRESSAO}`}
            >
              <X size={16} strokeWidth={2} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function nomeProva(r: RelatoResolvido) {
  const prova = r.edicao ? `${r.banca} ${r.edicao}` : [r.banca, r.ano].filter(Boolean).join(" ");
  return r.numero_prova ? `${prova}, questão ${r.numero_prova}` : prova || "questão";
}
