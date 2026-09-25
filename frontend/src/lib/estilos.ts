// Classes de botão compartilhadas (DESIGN_TRIAGEM.md §4). Strings literais
// inteiras para o Tailwind enxergar as classes na varredura do código.

// `active:scale-[0.97]`: o botão cede ao clique (DESIGN_TRIAGEM.md §3).
export const BOTAO_PRIMARIO =
  "inline-flex h-11 items-center justify-center gap-2.5 rounded-btn bg-ink px-5 text-[15px] font-semibold text-onink transition duration-hover ease-brand hover:opacity-90 active:scale-[0.97] disabled:cursor-not-allowed disabled:bg-line disabled:text-faint disabled:hover:opacity-100 disabled:active:scale-100";

export const BOTAO_SECUNDARIO =
  "inline-flex h-11 items-center justify-center gap-2 rounded-btn border border-line bg-surface px-4 text-[15px] font-medium text-ink-2 transition duration-hover ease-brand hover:border-muted hover:text-ink active:scale-[0.97] disabled:cursor-not-allowed disabled:text-faint disabled:active:scale-100";

// Botões pequenos da barra superior e do modo foco.
export const PRESSAO = "active:scale-[0.94]";

// A ação da vez nas sessões de Praticar e Revisão (Confirmar, Próximo caso, as
// notas). No celular ela gruda no pé da tela enquanto o cartão do caso rola, e
// no fim do cartão volta ao lugar, como rodapé dele: antes, cada caso pedia
// rolar a discussão inteira até achar o botão. `-mx-6` estica a faixa até a
// borda do cartão (`p-6` no celular), para o texto rolar por baixo sem vazar
// dos lados; `sticky`, e não `fixed`, porque o caso entra com `transform`, e
// `fixed` dentro dele deixaria de ser relativo à tela durante a entrada.
export const ACAO_DA_VEZ =
  "max-sm:sticky max-sm:bottom-0 max-sm:z-10 max-sm:-mx-6 max-sm:border-t max-sm:border-line max-sm:bg-surface max-sm:px-4 max-sm:py-3";

export const CAMPO =
  "h-10 w-full rounded-btn border border-line bg-surface px-3 text-corpo text-ink outline-none transition duration-hover ease-brand focus:border-ink disabled:cursor-not-allowed disabled:bg-ground disabled:text-faint";
