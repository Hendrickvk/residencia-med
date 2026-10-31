// A moeda: um círculo com as barras da marca descendo, no metal das conquistas.
export function Moeda({ tamanho = 16, className = "" }: { tamanho?: number; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={tamanho}
      height={tamanho}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      aria-hidden="true"
      className={`shrink-0 text-ouro ${className}`}
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 15.5v-7" />
      <path d="M12 15.5v-4.5" />
      <path d="M15.5 15.5v-2" />
    </svg>
  );
}
