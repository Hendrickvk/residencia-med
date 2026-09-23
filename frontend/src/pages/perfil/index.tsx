import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useMe } from "../../lib/auth";
import type { QuestaoMarcada } from "../../lib/types";
import { Identidade } from "./Identidade";
import { Marcadas } from "./Marcadas";
import { ProvaAlvo } from "./ProvaAlvo";

// Página da conta: quem ela é aqui, quando é a prova dela e o que ela guardou
// para rever. Não é um segundo Painel — nada aqui mede desempenho, que é
// assunto de lá.
export default function Perfil() {
  const { data: me } = useMe();
  const marcadas = useQuery({
    queryKey: ["marcadas"],
    queryFn: () => api.get<{ questoes: QuestaoMarcada[] }>("/me/marcadas"),
  });

  return (
    <div className="flex flex-col gap-7">
      <div>
        <div className="rotulo text-muted">Sua conta</div>
        <h1 className="mt-1 text-titulo text-ink">Perfil</h1>
      </div>

      <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Identidade me={me} />
        <ProvaAlvo me={me} />
      </div>

      <Marcadas
        questoes={marcadas.data?.questoes}
        isError={marcadas.isError}
        isPaused={marcadas.isPaused}
        isLoading={marcadas.isLoading}
        onTentarDeNovo={() => void marcadas.refetch()}
      />
    </div>
  );
}
