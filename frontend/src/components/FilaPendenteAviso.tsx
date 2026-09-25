import { useEffect, useState } from "react";
import { usePresenca } from "../lib/movimento";
import { useRespostasPendentes } from "../lib/respostasQueue";

const ATRASO_PARA_AVISAR_MS = 4000;

// Aviso discreto só quando a fila de respostas NÃO drena rápido (MIGRACAO.md
// §2) — a maioria das gravações termina em milissegundos e nunca deveria
// piscar um toast pra isso.
export function FilaPendenteAviso() {
  const pendentes = useRespostasPendentes();
  const [mostrar, setMostrar] = useState(false);
  // Fila vazia rearma a espera, para o próximo atraso também esperar 4s.
  if (pendentes === 0 && mostrar) setMostrar(false);

  useEffect(() => {
    if (pendentes === 0) return;
    const timer = setTimeout(() => setMostrar(true), ATRASO_PARA_AVISAR_MS);
    return () => clearTimeout(timer);
  }, [pendentes]);

  const visivel = mostrar && pendentes > 0;
  const { montado, saindo } = usePresenca(visivel);
  // Durante a saída a fila já está vazia: sem guardar o último número, o aviso
  // sairia escrito "0 respostas aguardando envio".
  const [ultimo, setUltimo] = useState(pendentes);
  if (visivel && pendentes !== ultimo) setUltimo(pendentes);

  if (!montado) return null;

  return (
    <div
      role="status"
      data-saindo={saindo || undefined}
      // Sobe ao entrar e desce ao sair, pelo mesmo caminho (`.presenca`, no
      // theme.css). Abaixo de 1024px o rodapé é da barra de abas e, na sessão,
      // da ação da vez: o aviso vai para baixo da barra superior e entra de cima.
      className={`presenca fixed bottom-4 right-4 z-50 max-lg:bottom-auto max-lg:top-20 max-lg:[--presenca-y:-8px] flex items-center gap-2.5 rounded-card border border-line bg-surface px-4 py-3 text-apoio text-ink-2 transition-[opacity,transform] ${
        saindo ? "duration-hover ease-brand" : "duration-toggle ease-suave"
      }`}
    >
      <span className="h-2 w-2 animate-pulse rounded-pill bg-t2" aria-hidden="true" />
      {ultimo} resposta{ultimo !== 1 && "s"} aguardando envio…
    </div>
  );
}
