// Classes de botão compartilhadas (DESIGN_TRIAGEM.md §4). Strings literais
// inteiras para o Tailwind enxergar as classes na varredura do código.

export const BOTAO_PRIMARIO =
  "inline-flex h-11 items-center justify-center gap-2.5 rounded-btn bg-ink px-5 text-[15px] font-semibold text-onink transition duration-hover ease-brand hover:opacity-90 disabled:cursor-not-allowed disabled:bg-line disabled:text-faint disabled:hover:opacity-100";

export const BOTAO_SECUNDARIO =
  "inline-flex h-11 items-center justify-center gap-2 rounded-btn border border-line bg-surface px-4 text-[15px] font-medium text-ink-2 transition duration-hover ease-brand hover:border-muted hover:text-ink disabled:cursor-not-allowed disabled:text-faint";

export const CAMPO =
  "h-10 w-full rounded-btn border border-line bg-surface px-3 text-corpo text-ink outline-none transition duration-hover ease-brand focus:border-ink disabled:cursor-not-allowed disabled:bg-ground disabled:text-faint";
