import { useContagem } from "../lib/movimento";

interface Props {
  valor: number;
  formatar: (valor: number) => string;
  // Com chave, só anima quando o valor mudou desde a última vez que apareceu.
  chave?: string;
  className?: string;
}

// Número grande que conta até o valor. O valor final fica invisível por baixo
// reservando a largura, então nada ao redor se desloca durante a contagem
// (DESIGN_TRIAGEM.md, "nada se desloca quando um dado chega").
export function NumeroAnimado({ valor, formatar, chave, className = "" }: Props) {
  const exibido = useContagem(valor, chave);
  return (
    <span className={`relative inline-block ${className}`}>
      <span className="sr-only">{formatar(valor)}</span>
      <span className="invisible" aria-hidden="true">
        {formatar(valor)}
      </span>
      <span className="absolute inset-0 text-right" aria-hidden="true">
        {formatar(exibido)}
      </span>
    </span>
  );
}
