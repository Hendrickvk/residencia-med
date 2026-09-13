interface Props {
  children: React.ReactNode;
  // Dentro de um botão primário (fundo --ink): fundo translúcido em vez de borda.
  sobreTinta?: boolean;
}

export function Kbd({ children, sobreTinta = false }: Props) {
  return (
    <kbd
      className={`rounded-col px-[7px] py-1 font-sans text-[11.5px] font-semibold leading-none ${
        sobreTinta ? "bg-white/15 text-onink dark:bg-black/10" : "border border-line bg-line-soft text-ink-2"
      }`}
    >
      {children}
    </kbd>
  );
}
