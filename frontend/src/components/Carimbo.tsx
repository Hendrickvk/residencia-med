import type { GrauCarimbo } from "../lib/types";

// Cada carimbo cai um pouco torto, e sempre do mesmo jeito: o giro vem da posição, e
// não do acaso, para não dançar a cada visita.
const GIROS = [-3, 2, -1.5, 3, -2, 1.5, -2.5, 2.5];
const CLASSE_GRAU: Record<GrauCarimbo, string> = { bronze: "", prata: "carimbo-prata", ouro: "carimbo-ouro" };
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

// O timestamp é o horário de Brasília sem fuso: lido como texto, não muda de dia.
function dataDoCarimbo(iso: string) {
  const [ano, mes, dia] = iso.slice(0, 10).split("-").map(Number);
  return `${dia} ${MESES[mes - 1]} ${ano}`;
}

export function Carimbo({
  nome, grau, obtidaEm, ordem = 0, bate = false,
}: {
  nome: string;
  grau: GrauCarimbo;
  // Sem data, é o espaço do carimbo que ainda não veio.
  obtidaEm?: string | null;
  ordem?: number;
  bate?: boolean;
}) {
  if (!obtidaEm) return <div className="carimbo carimbo-vazio">{nome}</div>;
  return (
    <div
      className={`carimbo ${CLASSE_GRAU[grau]} ${bate ? "carimbo-bate" : ""}`}
      style={{ "--giro": `${GIROS[ordem % GIROS.length]}deg` } as React.CSSProperties}
    >
      {nome}
      <span className="carimbo-data">{dataDoCarimbo(obtidaEm)}</span>
      <span className="sr-only">Grau {grau}.</span>
    </div>
  );
}
