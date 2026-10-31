// O desenho de cada item da loja, por id. O servidor só guarda o id
// (progressao.CATALOGO): nenhum desenho vem de fora, pelo mesmo motivo de a cor do
// avatar ser uma chave da paleta e não um hex.

export interface TracoMoldura {
  d: string;
  largura: number;
  ouro?: boolean;
  tracejado?: string;
}

// O desenho vive num quadrado de 100, com o avatar ocupando o miolo (Avatar.tsx).
function ponto(raio: number, graus: number): [number, number] {
  const angulo = ((graus - 90) * Math.PI) / 180;
  return [50 + raio * Math.cos(angulo), 50 + raio * Math.sin(angulo)];
}

function anel(raio: number): string {
  return `M50 ${50 - raio}A${raio} ${raio} 0 1 1 49.99 ${50 - raio}Z`;
}

function risco(de: number, ate: number, graus: number, inclina = 0): string {
  const [x1, y1] = ponto(de, graus);
  const [x2, y2] = ponto(ate, graus + inclina);
  return `M${x1.toFixed(2)} ${y1.toFixed(2)}L${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

function riscos(passo: number, f: (graus: number) => string): string {
  let d = "";
  for (let g = 0; g < 360; g += passo) d += f(g);
  return d;
}

// O traçado do ECG correndo em volta do avatar: onda P, QRS e onda T no alto.
function ecg(raio: number): string {
  let d = "";
  for (let g = -180; g <= 180; g += 1) {
    let f = 0;
    if (g >= -38 && g <= -24) f = 1.7 * Math.sin((Math.PI * (g + 38)) / 14);
    else if (g > -8 && g <= -4) f = (-1.6 * (g + 8)) / 4;
    else if (g > -4 && g <= 0) f = -1.6 + ((g + 4) / 4) * 8.4;
    else if (g > 0 && g <= 4) f = 6.8 - (g / 4) * 9.8;
    else if (g > 4 && g <= 8) f = -3 + ((g - 4) / 4) * 3;
    else if (g >= 16 && g <= 36) f = 2.3 * Math.sin((Math.PI * (g - 16)) / 20);
    const [x, y] = ponto(raio + f, g);
    d += `${d ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`;
  }
  return d;
}

function estetoscopio(): TracoMoldura[] {
  const [ax, ay] = ponto(42, 152);
  const [bx, by] = ponto(42, 124);
  const [cx, cy] = ponto(42, 138);
  return [
    { d: `M${ax.toFixed(2)} ${ay.toFixed(2)}A42 42 0 1 1 ${bx.toFixed(2)} ${by.toFixed(2)}`, largura: 2.2 },
    { d: `M${(cx + 6.4).toFixed(2)} ${cy.toFixed(2)}A6.4 6.4 0 1 1 ${(cx + 6.39).toFixed(2)} ${(cy - 0.01).toFixed(2)}Z`, largura: 2.2 },
  ];
}

const MOLDURAS: Record<string, () => TracoMoldura[]> = {
  // As das patentes.
  ciclo: () => [{ d: anel(42), largura: 1.8 }],
  sutura: () => [
    { d: anel(42), largura: 0.9 },
    { d: riscos(15, (g) => risco(38.5, 45.5, g, 7)), largura: 1.8 },
  ],
  residencia: () => [
    { d: anel(40.5), largura: 1.8 },
    { d: anel(45.5), largura: 0.9 },
  ],
  r2: () => [
    { d: anel(40.5), largura: 1.8 },
    { d: anel(45.5), largura: 0.9 },
    { d: riscos(90, (g) => risco(40.5, 45.5, g)), largura: 2.4 },
  ],
  r3: () => [
    { d: anel(40.5), largura: 1.8 },
    { d: anel(45.5), largura: 0.9 },
    { d: riscos(30, (g) => risco(40.5, 45.5, g)), largura: 1.8 },
  ],
  preceptoria: () => [
    { d: anel(44), largura: 2.8, ouro: true },
    { d: anel(39), largura: 0.8, ouro: true },
  ],
  chefia: () => [
    { d: anel(45.5), largura: 1.4, ouro: true },
    { d: anel(39), largura: 2.2, ouro: true },
    { d: riscos(30, (g) => risco(39, 45.5, g)), largura: 1.6, ouro: true },
  ],
  // As da loja.
  pontos: () => [{ d: anel(42.5), largura: 2.6, tracejado: "0.1 6.6" }],
  milimetrado: () => [
    { d: riscos(5, (g) => (g % 30 === 0 ? risco(39, 46.5, g) : "")), largura: 1.2 },
    { d: riscos(5, (g) => (g % 30 === 0 ? "" : risco(41.5, 44.5, g))), largura: 0.7 },
  ],
  plantao: () => [
    { d: riscos(15, (g) => (g % 90 === 0 ? risco(38.5, 46.5, g) : "")), largura: 2.4 },
    { d: riscos(15, (g) => (g % 90 === 0 ? "" : risco(41, 45, g))), largura: 1.3 },
  ],
  estetoscopio,
  monitor: () => [{ d: ecg(42), largura: 1.5 }],
  "monitor-ouro": () => [
    { d: ecg(42), largura: 1.8, ouro: true },
    { d: anel(38.4), largura: 0.6, ouro: true },
  ],
};

// Id desconhecido não desenha nada: é o caso de um item novo chegar antes do front.
export function desenhoDaMoldura(id: string): TracoMoldura[] {
  return MOLDURAS[id]?.() ?? [];
}
