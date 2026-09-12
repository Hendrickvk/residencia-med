import { PanelLeftClose, PanelLeftOpen, ArrowRight } from "lucide-react";
import { NavLink } from "react-router-dom";
import { NAV } from "../../lib/nav";

const STORAGE_KEY = "residencia-med:rail-expandida";

interface RailProps {
  expandida: boolean;
  onToggle: () => void;
  aberta: boolean;
  onFechar: () => void;
  contadores?: { questoes: number; materiais: number };
}

export function lerPreferenciaRail(): boolean {
  const salvo = localStorage.getItem(STORAGE_KEY);
  return salvo === null ? true : salvo === "1";
}

export function salvarPreferenciaRail(expandida: boolean) {
  localStorage.setItem(STORAGE_KEY, expandida ? "1" : "0");
}

const grupos = ["Estudo", "Acervo"] as const;

export function Rail({ expandida, onToggle, aberta, onFechar, contadores }: RailProps) {
  return (
    <>
      {/* Abaixo de 768px o rail vira gaveta sobreposta (REDESIGN.md §8) */}
      {aberta && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={onFechar}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-full flex-col bg-railbg transition-toggle ease-brand
          ${expandida ? "w-rail" : "w-rail-collapsed"}
          ${aberta ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        <div className="flex h-14 items-center justify-between px-3">
          <div className="flex items-center gap-2 overflow-hidden">
            <span className="h-4 w-[3px] shrink-0 bg-action" />
            {expandida && (
              <span className="truncate text-[15px] font-semibold text-white">Residência Med</span>
            )}
          </div>
          <button
            type="button"
            onClick={onToggle}
            className="hidden shrink-0 rounded-btn p-1.5 text-white/70 transition-hover hover:bg-white/[.06] hover:text-white md:block"
            aria-label={expandida ? "Recolher menu" : "Expandir menu"}
          >
            {expandida ? <PanelLeftClose size={18} strokeWidth={1.5} /> : <PanelLeftOpen size={18} strokeWidth={1.5} />}
          </button>
        </div>

        <div className="px-3 pb-3">
          <NavLink
            to="/praticar"
            onClick={onFechar}
            className="flex h-10 items-center justify-center gap-2 rounded-btn bg-action px-3 text-sm font-medium text-white transition-hover hover:bg-action-hover"
          >
            <ArrowRight size={16} strokeWidth={1.5} />
            {expandida && "Praticar agora"}
          </NavLink>
        </div>

        <div className="mx-3 border-t border-white/[.08]" />

        <nav className="flex-1 overflow-y-auto px-3 py-3">
          {grupos.map((grupo) => (
            <div key={grupo} className="mb-4">
              {expandida && (
                <div className="mb-1 px-3 text-apoio uppercase tracking-wide text-ink-300/80">
                  {grupo}
                </div>
              )}
              {NAV.filter((item) => item.grupo === grupo).map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onFechar}
                  className={({ isActive }) =>
                    `group/tooltip relative flex h-10 items-center gap-3 rounded-btn px-3 text-sm transition-hover ${
                      isActive
                        ? "bg-white/10 text-white"
                        : "text-white/70 hover:bg-white/[.06] hover:text-white"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute inset-y-0 left-0 w-[3px] rounded-r bg-action" />
                      )}
                      <item.icon size={18} strokeWidth={1.5} className="shrink-0" />
                      {expandida ? (
                        <span className="truncate">{item.label}</span>
                      ) : (
                        // Colapsada: rótulo vira tooltip 300ms após o hover (REDESIGN.md §3)
                        <span className="pointer-events-none invisible absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-btn bg-railbg px-2 py-1 text-apoio text-white opacity-0 transition-opacity delay-300 group-hover/tooltip:visible group-hover/tooltip:opacity-100">
                          {item.label}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {expandida && (
          <div className="border-t border-white/[.08] px-4 py-3 text-apoio text-ink-300/80">
            {contadores ? `${contadores.questoes} questões · ${contadores.materiais} materiais` : "— questões · — materiais"}
          </div>
        )}
      </aside>
    </>
  );
}
