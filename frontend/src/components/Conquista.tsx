import { Award, Medal, Trophy } from "lucide-react";
import { dataDaConquista } from "../lib/format";
import type { GrauConquista } from "../lib/types";

// O grau está no metal e também no ícone, para não depender só da cor.
const GRAUS: Record<GrauConquista, { Icone: typeof Award; fundo: string; nome: string }> = {
  bronze: { Icone: Award, fundo: "bg-bronze", nome: "bronze" },
  prata: { Icone: Medal, fundo: "bg-prata", nome: "prata" },
  ouro: { Icone: Trophy, fundo: "bg-ouro", nome: "ouro" },
};

export function MedalhaConquista({
  grau, obtida, tamanho = 48, nova = false,
}: {
  grau: GrauConquista;
  obtida: boolean;
  tamanho?: number;
  nova?: boolean;
}) {
  const { Icone, fundo, nome } = GRAUS[grau];
  return (
    <span
      style={{ width: tamanho, height: tamanho }}
      className={`flex shrink-0 items-center justify-center rounded-pill ${
        obtida ? `${fundo} text-surface` : "border border-line text-faint"
      } ${nova ? "animate-marcar" : ""}`}
    >
      <Icone size={Math.round(tamanho * 0.5)} strokeWidth={2} aria-hidden="true" />
      {obtida && <span className="sr-only">Grau {nome}.</span>}
    </span>
  );
}

// A forma deitada: nome e data ao lado da medalha, no perfil e no fim da sessão.
export function LinhaConquista({
  nome, grau, obtidaEm, nova = false,
}: {
  nome: string;
  grau: GrauConquista;
  obtidaEm: string;
  nova?: boolean;
}) {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <MedalhaConquista grau={grau} obtida tamanho={40} nova={nova} />
      <div className="flex min-w-0 flex-col">
        <span className="text-corpo font-semibold [overflow-wrap:anywhere]">{nome}</span>
        <span className="text-apoio tabular-nums text-muted">{dataDaConquista(obtidaEm)}</span>
      </div>
    </div>
  );
}
