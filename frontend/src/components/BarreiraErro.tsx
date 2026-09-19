import { Component, type ErrorInfo, type ReactNode } from "react";
import { BOTAO_PRIMARIO } from "../lib/estilos";

interface Props {
  children: ReactNode;
}

interface State {
  erro: Error | null;
}

// Última rede da interface: antes disto, um erro de renderização em qualquer
// tela deixava a página em branco — sem saída, e num celular sem console para
// descobrir o motivo. React só oferece isto em classe, não existe hook.
export class BarreiraErro extends Component<Props, State> {
  state: State = { erro: null };

  static getDerivedStateFromError(erro: Error): State {
    return { erro };
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    // Fica no console do navegador: é o que sobra para investigar depois, já
    // que a plataforma não manda erro de front para o servidor.
    console.error("[conduta] erro não tratado na interface:", erro, info.componentStack);
  }

  render() {
    if (!this.state.erro) return this.props.children;
    return (
      <div className="flex min-h-dvh items-center justify-center bg-ground p-4">
        <div className="flex w-full max-w-md flex-col gap-4 rounded-caso border border-line bg-surface p-6">
          <h1 className="text-subtitulo">Esta tela quebrou.</h1>
          <p className="text-corpo text-ink-2">
            Recarregar costuma resolver. Se voltar a acontecer na mesma tela, me avise o que você estava fazendo.
          </p>
          <button type="button" onClick={() => location.reload()} className={BOTAO_PRIMARIO}>
            Recarregar
          </button>
          {import.meta.env.DEV && (
            <pre className="overflow-auto rounded-card bg-line-soft p-3 text-apoio text-ink-2">
              {this.state.erro.message}
            </pre>
          )}
        </div>
      </div>
    );
  }
}
