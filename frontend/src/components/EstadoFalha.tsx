import { BOTAO_PRIMARIO } from "../lib/estilos";

interface Props {
  mensagem?: string;
  onTentarDeNovo: () => void;
}

// Falha não é vazio. Sem esta caixa, uma requisição que não voltou caía no
// mesmo galho do `EstadoVazio` e a tela dizia que a aluna não tinha dados —
// no celular, onde a rede cai, ela leria "nenhuma revisão vencida hoje" com 30
// casos vencidos no banco. Borda cheia (a tracejada é a do vazio) e sem cor de
// triagem, que no DESIGN_TRIAGEM.md §2 só codifica nível.
export function EstadoFalha({ mensagem = "Não deu para carregar isto. Pode ser a conexão.", onTentarDeNovo }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-card border border-line px-6 py-12 text-center">
      <p className="max-w-[52ch] text-corpo text-ink-2">{mensagem}</p>
      <button type="button" onClick={onTentarDeNovo} className={BOTAO_PRIMARIO}>
        Tentar de novo
      </button>
    </div>
  );
}
