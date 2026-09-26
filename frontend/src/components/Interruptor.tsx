// O interruptor da plataforma: Configurador do Praticar e Lembretes do Perfil.
export function Interruptor({
  ligado,
  onMudar,
  children,
}: {
  ligado: boolean;
  onMudar: (ligado: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={ligado}
      onClick={() => onMudar(!ligado)}
      className="group flex items-center gap-3 text-left text-corpo text-ink"
    >
      <span
        className={`relative h-5 w-9 shrink-0 rounded-pill transition-colors duration-toggle ease-brand ${
          ligado ? "bg-ink" : "bg-line"
        }`}
      >
        {/* O pino alarga um pouco enquanto pressionado, como um interruptor físico. */}
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-pill bg-surface shadow-[0_1px_2px_rgba(0,0,0,0.3)] transition-[transform,width] duration-desliza ease-suave group-active:w-5 ${
            ligado ? "translate-x-[18px] group-active:translate-x-[14px]" : "translate-x-0.5"
          }`}
        />
      </span>
      {children}
    </button>
  );
}
