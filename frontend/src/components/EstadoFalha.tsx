import { BOTAO_PRIMARIO } from "../lib/estilos";

interface Props {
  mensagem?: string;
  // Tentativa em curso: o botão não pode convidar a um segundo clique.
  ocupado?: boolean;
  // Query pausada pelo React Query, não falhada: em `networkMode: "online"` ele
  // suspende a retentativa quando o navegador está offline ou a aba está em
  // segundo plano, e volta sozinho quando a conexão ou o foco voltam. Nesse
  // estado `refetch()` é no-op — um botão aqui seria um botão que mente.
  pausado?: boolean;
  onTentarDeNovo: () => void;
}

// Falha não é vazio. Sem esta caixa, uma requisição que não voltou caía no
// mesmo galho do `EstadoVazio` e a tela dizia que a aluna não tinha dados —
// no celular, onde a rede cai, ela leria "nenhuma revisão vencida hoje" com 30
// casos vencidos no banco. Borda cheia (a tracejada é a do vazio) e sem cor de
// triagem, que no DESIGN_TRIAGEM.md §2 só codifica nível.
export function EstadoFalha({
  mensagem = "Não deu para carregar isto. Pode ser a conexão.",
  ocupado = false,
  pausado = false,
  onTentarDeNovo,
}: Props) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-card border border-line px-6 py-12 text-center">
      <p className="max-w-[52ch] text-corpo text-ink-2">
        {pausado ? "Sem conexão agora. Assim que ela voltar, isto carrega sozinho." : mensagem}
      </p>
      {!pausado && (
        <button type="button" onClick={onTentarDeNovo} disabled={ocupado} className={BOTAO_PRIMARIO}>
          {ocupado ? "Tentando…" : "Tentar de novo"}
        </button>
      )}
    </div>
  );
}
