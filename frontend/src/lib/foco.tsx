import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { FocoContexto, useFoco } from "./focoContexto";

// Modo foco (DESIGN_TRIAGEM.md §5): durante uma sessão a barra superior troca
// as abas pela barra da própria sessão. A tela da sessão continua dona do
// estado (progresso, cronômetro) e só projeta a barra no slot do shell via
// portal — assim o shell não precisa conhecer Praticar, Simulado ou Revisão.
export function FocoProvider({ children }: { children: ReactNode }) {
  const [ativo, setAtivo] = useState(false);
  const [slot, setSlot] = useState<HTMLElement | null>(null);
  return <FocoContexto.Provider value={{ ativo, slot, setAtivo, setSlot }}>{children}</FocoContexto.Provider>;
}

// Enquanto montado, liga o modo foco e renderiza `children` no lugar das abas.
export function BarraFoco({ children }: { children: ReactNode }) {
  const { slot, setAtivo } = useFoco();

  useEffect(() => {
    setAtivo(true);
    return () => setAtivo(false);
  }, [setAtivo]);

  return slot ? createPortal(children, slot) : null;
}
