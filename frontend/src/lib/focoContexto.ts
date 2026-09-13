import { createContext, useContext } from "react";

// Estado do modo foco (DESIGN_TRIAGEM.md §5). Fica separado de `foco.tsx`
// para aquele arquivo exportar só componentes (fast refresh).
export interface FocoCtx {
  ativo: boolean;
  slot: HTMLElement | null;
  setAtivo: (ativo: boolean) => void;
  setSlot: (el: HTMLElement | null) => void;
}

export const FocoContexto = createContext<FocoCtx | null>(null);

export function useFoco(): FocoCtx {
  const ctx = useContext(FocoContexto);
  if (!ctx) throw new Error("useFoco precisa estar dentro de <FocoProvider>");
  return ctx;
}
