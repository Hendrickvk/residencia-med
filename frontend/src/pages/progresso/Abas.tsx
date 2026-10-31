import { NavLink } from "react-router-dom";

const ABAS = [
  { para: "/progresso", rotulo: "Progresso" },
  { para: "/progresso/loja", rotulo: "Loja" },
];

// As seções do Progresso, em links e não em estado: cada uma tem endereço próprio,
// e é para a Loja que o fim da sessão e o Painel mandam.
export function Abas() {
  return (
    <nav aria-label="Seções do progresso" className="inline-flex gap-0.5 rounded-card bg-line-soft p-[3px]">
      {ABAS.map((aba) => (
        <NavLink
          key={aba.para}
          to={aba.para}
          end
          className={({ isActive }) =>
            `flex h-9 items-center rounded-col border px-3.5 text-[14.5px] font-semibold transition-colors duration-hover ${
              isActive ? "border-line bg-surface text-ink" : "border-transparent text-muted hover:text-ink"
            }`
          }
        >
          {aba.rotulo}
        </NavLink>
      ))}
    </nav>
  );
}
