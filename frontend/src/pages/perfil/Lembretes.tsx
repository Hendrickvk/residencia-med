import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Interruptor } from "../../components/Interruptor";
import { api } from "../../lib/api";
import type { Me } from "../../lib/types";

// O lembrete de revisão por e-mail é opcional e nasce desligado: só a própria
// aluna liga (decisão do usuário, 26/09 — "que não seja forçado"). Quem manda é
// a rotina diária do servidor (scripts/rotina_diaria.py), às 8h, e só nos dias
// com revisão vencida.
export function Lembretes({ me }: { me: Me | undefined }) {
  const queryClient = useQueryClient();
  // O "Desligar o lembrete" do e-mail chega em /perfil#lembretes: a página rola
  // até aqui. Num setTimeout porque o AppShell volta ao topo a cada troca de
  // tela, e o efeito dele (o pai) roda depois deste.
  const { hash } = useLocation();
  useEffect(() => {
    if (hash !== "#lembretes") return;
    const timer = setTimeout(() => document.getElementById("lembretes")?.scrollIntoView({ block: "center" }), 0);
    return () => clearTimeout(timer);
  }, [hash]);
  // O interruptor responde no toque; se o servidor recusar, volta.
  const [escolha, setEscolha] = useState<boolean | null>(null);
  const ligado = escolha ?? me?.lembrete_revisao ?? false;

  async function mudar(ativo: boolean) {
    setEscolha(ativo);
    try {
      await api.patch("/me/lembrete", { ativo });
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    } catch {
      setEscolha(!ativo);
    }
  }

  return (
    <section id="lembretes" className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
      <h2 className="text-bloco text-ink">Lembretes</h2>
      <Interruptor ligado={ligado} onMudar={(ativo) => void mudar(ativo)}>
        Avisar por e-mail quando houver revisão vencida
      </Interruptor>
      <p className="text-apoio text-muted">
        No máximo um e-mail por dia, às 8h, e só nos dias em que há casos ou cartões para revisar.
        {me && ` Vai para ${me.email}.`}
      </p>
      {me && !me.email_confirmado && ligado && (
        <p className="text-apoio text-muted">Confirme o seu e-mail para começar a receber.</p>
      )}
    </section>
  );
}
