// O desenho de cada item da loja, por id. O servidor só guarda o id
// (progressao.CATALOGO): nenhum desenho vem de fora, pelo mesmo motivo de a cor do
// avatar ser uma chave da paleta e não um hex.

export interface TracoMoldura {
  d: string;
  // Sem largura, a forma é preenchida com `cor`.
  largura?: number;
  ouro?: boolean;
  tracejado?: string;
  cor?: string;
  // Para a forma que tem traço e miolo de cores diferentes.
  preenche?: string;
  opacidade?: number;
  // Em segundos. É um reflexo: fica apagado e acende nesse atraso, a cada volta da
  // animação `brilho-folha` (theme.css).
  atraso?: number;
  movimento?: Movimento;
}

export interface Movimento {
  nome: "gira" | "gira-contra" | "pisca";
  segundos: number;
  // O ponto em volta do qual gira, nas coordenadas do desenho.
  centro?: [number, number];
  atraso?: number;
}

// O tema que vem com a moldura: a cena da faixa do crachá e as cores do perfil. As cores
// são da moldura e não mudam com o tema claro ou escuro do app. `variaveis` reescreve os
// tokens só dentro do crachá e do painel do perfil; o resto do app não vê nada disso.
export interface TemaDoPerfil {
  cena: TracoMoldura[];
  marca: string;
  variaveis: Record<string, string>;
}

// O desenho vive num quadrado de 100, com o avatar ocupando o miolo (Avatar.tsx).
function emVolta(cx: number, cy: number, raio: number, graus: number): [number, number] {
  const angulo = ((graus - 90) * Math.PI) / 180;
  return [cx + raio * Math.cos(angulo), cy + raio * Math.sin(angulo)];
}

function ponto(raio: number, graus: number): [number, number] {
  return emVolta(50, 50, raio, graus);
}

function circulo(cx: number, cy: number, r: number): string {
  return `M${cx - r} ${cy}A${r} ${r} 0 1 0 ${cx + r} ${cy}A${r} ${r} 0 1 0 ${cx - r} ${cy}Z`;
}

// Um contorno que varia com o ângulo: as pétalas da flor saem daqui.
function polar(cx: number, cy: number, raio: (graus: number) => number, passo = 2): string {
  let d = "";
  for (let g = 0; g < 360; g += passo) {
    const [x, y] = emVolta(cx, cy, raio(g), g);
    d += `${d ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`;
  }
  return `${d}Z`;
}

// Uma elipse deitada no raio: a pétala da dália. `de` e `ate` são as pontas dela.
function petala(cx: number, cy: number, de: number, ate: number, largura: number, graus: number): string {
  const [x1, y1] = emVolta(cx, cy, de, graus);
  const [x2, y2] = emVolta(cx, cy, ate, graus);
  const raio = (ate - de) / 2;
  const giro = graus - 90;
  const arco = `A${raio} ${largura} ${giro} 1 0`;
  return `M${x1.toFixed(2)} ${y1.toFixed(2)}${arco} ${x2.toFixed(2)} ${y2.toFixed(2)}${arco} ${x1.toFixed(2)} ${y1.toFixed(2)}Z`;
}

function quatroPontas(x: number, y: number, r: number): string {
  return `M${x} ${y - r}Q${x} ${y} ${x + r} ${y}Q${x} ${y} ${x} ${y + r}Q${x} ${y} ${x - r} ${y}Q${x} ${y} ${x} ${y - r}Z`;
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

// A coroa de louros das patentes. Os tons são de metal e não mudam com o tema; as paradas
// claras e escuras se alternam em volta da coroa para dar o reflexo.
interface Metal {
  tons: string[];
  caule: string;
  luz?: string;
}

const GRAFITE: Metal = { tons: ["#9aa0a6", "#6d7278", "#555a60", "#8b9096"], caule: "#555a60" };
const BRONZE: Metal = { tons: ["#d9a673", "#a8733c", "#7a4d22", "#c48f58", "#8f5f2e"], caule: "#7a4d22" };
const PRATA: Metal = { tons: ["#b4bcc4", "#838b93", "#5c646c", "#a2aab2", "#6f777f"], caule: "#5c646c", luz: "#ffffff" };
const OURO: Metal = { tons: ["#ecd07a", "#c79a2c", "#8a6410", "#dfbf5e", "#a97f1c", "#e8cf7c"], caule: "#8a6410", luz: "#fffbe6" };

const RAIO_COROA = 43.5;
const PASSO_FOLHA = 14;
const ULTIMO_NIVEL = 12;

function tomDoMetal(tons: string[], graus: number): string {
  const t = ((graus % 360) / 360) * tons.length;
  const i = Math.floor(t);
  const canais = (hex: string) => [1, 3, 5].map((c) => parseInt(hex.slice(c, c + 2), 16));
  const [a, b] = [canais(tons[i]), canais(tons[(i + 1) % tons.length])];
  return `rgb(${a.map((v, c) => Math.round(v + (b[c] - v) * (t - i))).join(",")})`;
}

// Uma folha nasce no caule, em `graus`, e aponta para o alto do ramo. `lado` é 1 no ramo
// direito e -1 no esquerdo; `abre` é o ângulo dela com o caule. `recuo` e `largura`
// menores desenham o miolo da folha, que é onde o reflexo acende: a borda continua
// escura, e por isso a prata não some no fundo branco.
function folha(graus: number, lado: number, abre: number, comprimento = 8.4, largura = 2.5, recuo = 0): string {
  const [ox, oy] = ponto(RAIO_COROA, graus);
  const giro = ((graus - 90 - lado * 90 + lado * abre) * Math.PI) / 180;
  const p = (x: number, y: number) =>
    `${(ox + x * Math.cos(giro) - y * Math.sin(giro)).toFixed(2)} ${(oy + x * Math.sin(giro) + y * Math.cos(giro)).toFixed(2)}`;
  const fim = recuo + comprimento;
  const meio = recuo + comprimento / 2;
  return `M${p(recuo, 0)}Q${p(meio, -largura)} ${p(fim, 0)}Q${p(meio, largura)} ${p(recuo, 0)}Z`;
}

function coroa(metal: Metal, niveis: number, { cheia = false, estrela = false } = {}): TracoMoldura[] {
  const caule = (de: number, ate: number, varre: number) => {
    const [x1, y1] = ponto(RAIO_COROA, de);
    const [x2, y2] = ponto(RAIO_COROA, ate);
    return `M${x1.toFixed(2)} ${y1.toFixed(2)}A${RAIO_COROA} ${RAIO_COROA} 0 0 ${varre} ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  };
  const curso = PASSO_FOLHA * (niveis - 1) + 2;
  const tracos: TracoMoldura[] = [
    { d: caule(172, 172 - curso, 0), largura: 0.8, cor: metal.caule },
    { d: caule(188, 188 + curso, 1), largura: 0.8, cor: metal.caule },
  ];
  const aberturas = cheia ? [-26, 0, 26] : [-26, 26];
  const reflexos: TracoMoldura[] = [];

  for (let n = 0; n < niveis; n++) {
    const passo = PASSO_FOLHA * n;
    let luz = "";
    for (const [graus, lado, cor] of [
      [174 - passo, 1, tomDoMetal(metal.tons, 172 - passo)],
      [186 + passo, -1, tomDoMetal(metal.tons, 200 + passo)],
    ] as const) {
      for (const abre of aberturas) {
        tracos.push({ d: folha(graus, lado, abre), cor });
        luz += folha(graus, lado, abre, 7, 1.7, 0.7);
      }
    }
    // Um reflexo por andar, e não por folha: todas as do andar acendem juntas, e são 12
    // elementos animados em vez de 48.
    if (metal.luz) reflexos.push({ d: luz, cor: metal.luz, atraso: Number((n * 0.075).toFixed(3)) });
  }

  if (estrela) {
    tracos.push({ d: quatroPontas(50, 4.5, 5), cor: metal.tons[1] });
    if (metal.luz) reflexos.push({ d: quatroPontas(50, 4.5, 3), cor: metal.luz, atraso: ULTIMO_NIVEL * 0.075 });
  }
  return [...tracos, ...reflexos];
}

const OURO_DECO = "#d4aa4a";
const PRETO_DECO = "#111315";
const AZUL_NOITE = "#101a3f";
const ESTRELA = "#f4dc92";

function piscando(i: number): Movimento {
  return { nome: "pisca", segundos: 3.6, atraso: -1.2 * (i % 3) };
}

function molduraLeque(): TracoMoldura[] {
  let cheios = "";
  let vazados = "";
  for (let g = 0; g < 360; g += 10) {
    const [ax, ay] = ponto(38.6, g - 4.2);
    const [bx, by] = ponto(38.6, g + 4.2);
    const [cx, cy] = ponto(g % 30 ? 44 : 47.4, g);
    const d = `M${ax.toFixed(2)} ${ay.toFixed(2)}L${cx.toFixed(2)} ${cy.toFixed(2)}L${bx.toFixed(2)} ${by.toFixed(2)}Z`;
    if (g % 30) vazados += d;
    else cheios += d;
  }
  return [
    { d: anel(43), largura: 11, cor: PRETO_DECO },
    { d: cheios, cor: OURO_DECO },
    { d: vazados, largura: 0.5, cor: OURO_DECO },
    { d: anel(48.6), largura: 0.8, cor: OURO_DECO },
    { d: anel(37.9), largura: 0.5, cor: OURO_DECO },
  ];
}

function molduraOrbita(): TracoMoldura[] {
  return [
    { d: anel(41.5), largura: 0.6 },
    { d: anel(47), largura: 0.5, opacidade: 0.45 },
    { d: circulo(50, 8.5, 3), cor: "#d9a441", movimento: { nome: "gira", segundos: 14, centro: [50, 50] } },
    { d: circulo(50, 3, 1.6), cor: "currentColor", movimento: { nome: "gira-contra", segundos: 22, centro: [50, 50] } },
  ];
}

function molduraFlor(): TracoMoldura[] {
  return [
    { d: polar(50, 50, (g) => 43.5 + 5.6 * Math.abs(Math.cos((g * Math.PI) / 30))), cor: "#f2a7b5" },
    { d: polar(50, 50, (g) => 40 + 5 * Math.abs(Math.cos(((g + 15) * Math.PI) / 30))), cor: "#f9d3d9" },
  ];
}

function molduraDalia(): TracoMoldura[] {
  const coroa = (inicio: number, comprimento: number, largura: number, cor: string): TracoMoldura => {
    let d = "";
    for (let g = inicio; g < inicio + 360; g += 20) d += petala(50, 50, 36.4, 37 + comprimento, largura, g);
    return { d, cor };
  };
  return [coroa(0, 12, 3.4, "#e0603f"), coroa(10, 9.2, 3.1, "#f09a45"), coroa(0, 5.6, 2.4, "#f7c96e")];
}

function molduraNoite(): TracoMoldura[] {
  const estrelas: [number, number][] = [
    [12, 4.4], [47, 2.4], [80, 3.4], [118, 2.2], [150, 4.6], [196, 2.4], [232, 3.8], [268, 2.2], [302, 4.6], [335, 2.4],
  ];
  return [
    { d: anel(43), largura: 11, cor: AZUL_NOITE },
    { d: anel(48.6), largura: 0.7, cor: "#c79a2c" },
    { d: anel(37.6), largura: 0.5, cor: "#c79a2c" },
    ...estrelas.map(([g, r], i) => {
      const [x, y] = ponto(43 + ((i % 3) - 1) * 1.6, g);
      return { d: quatroPontas(Number(x.toFixed(2)), Number(y.toFixed(2)), r), cor: ESTRELA, movimento: piscando(i) };
    }),
  ];
}

// As cenas ficam na faixa do crachá, de 300 por 104; o centro do avatar cai em (150, 117).
const FAIXA = "M0 0H300V104H0Z";
const CX = 150;
const CY = 117;

function florGrande(x: number, y: number, r: number, fora: string, dentro: string, miolo: string): TracoMoldura[] {
  const contorno = (raio: number, giro: number) => (g: number) => raio * (0.78 + 0.22 * Math.abs(Math.cos(((g + giro) * Math.PI) / 36)));
  return [
    { d: polar(x, y, contorno(r, 0), 3), cor: fora },
    { d: polar(x, y, contorno(r * 0.55, 18), 3), cor: dentro },
    { d: circulo(x, y, r * 0.14), cor: miolo },
  ];
}

function daliaGrande(x: number, y: number, r: number, tons: [string, string, string, string]): TracoMoldura[] {
  const coroa = (k: number, inicio: number, passo: number, largura: number, cor: string): TracoMoldura => {
    let d = "";
    for (let g = inicio; g < inicio + 360; g += passo) d += petala(x, y, r * k * 0.2, r * k * 1.04, r * largura, g);
    return { d, cor };
  };
  return [
    coroa(1, 0, 18, 0.132, tons[0]),
    coroa(0.72, 10, 20, 0.114, tons[1]),
    coroa(0.46, 0, 24, 0.096, tons[2]),
    { d: circulo(x, y, r * 0.12), cor: tons[3] },
  ];
}

const QUENTES: [string, string, string, string] = ["#e0603f", "#f09a45", "#f7c96e", "#a83a22"];
const CLARAS: [string, string, string, string] = ["#f7e0a6", "#f7c96e", "#e0603f", "#a83a22"];

function cenaLeque(): TracoMoldura[] {
  let raios = "";
  let finos = "";
  for (let g = -90; g <= 90; g += 7.5) {
    const [x1, y1] = emVolta(CX, CY, 54, g);
    const [x2, y2] = emVolta(CX, CY, 255, g);
    const d = `M${x1.toFixed(2)} ${y1.toFixed(2)}L${x2.toFixed(2)} ${y2.toFixed(2)}`;
    if (g % 15) finos += d;
    else raios += d;
  }
  return [
    { d: FAIXA, cor: PRETO_DECO },
    { d: finos, largura: 0.5, cor: OURO_DECO },
    { d: raios, largura: 1.1, cor: OURO_DECO },
    { d: [87, 123, 159, 195].map((r) => circulo(CX, CY, r)).join(""), largura: 0.9, cor: OURO_DECO },
    // O respiro atrás do nome da marca: sobre os raios ele não se lê.
    { d: "M99 4H201V58H99Z", cor: PRETO_DECO },
  ];
}

function cenaOrbita(): TracoMoldura[] {
  const estrelas: [number, number][] = [[45, 15], [240, 22], [273, 74], [21, 72], [93, 37], [204, 10], [62, 50], [232, 58]];
  return [
    { d: FAIXA, cor: "#0f1420" },
    { d: estrelas.map(([x, y], i) => circulo(x, y, i % 2 ? 1.1 : 1.5)).join(""), cor: "#dfe6f2" },
    { d: [105, 156, 213].map((r) => circulo(CX, CY, r)).join(""), largura: 0.8, cor: "#dfe6f2", opacidade: 0.4 },
    { d: circulo(CX, CY - 105, 5), cor: "#d9a441", movimento: { nome: "gira", segundos: 24, centro: [CX, CY] } },
    { d: circulo(CX, CY - 156, 3.2), cor: "#9cc0ea", movimento: { nome: "gira-contra", segundos: 40, centro: [CX, CY] } },
  ];
}

function cenaFlor(): TracoMoldura[] {
  return [
    { d: FAIXA, cor: "#f7cfd6" },
    ...florGrande(36, 22, 39, "#f2a7b5", "#fbe3e7", "#e6838f"),
    ...florGrande(267, 17, 30, "#f9e3e6", "#f2a7b5", "#ffffff"),
    ...florGrande(255, 89, 36, "#f2a7b5", "#fbe3e7", "#e6838f"),
    ...florGrande(51, 94, 24, "#f9e3e6", "#f2a7b5", "#ffffff"),
  ];
}

function cenaDalia(): TracoMoldura[] {
  return [
    { d: FAIXA, cor: "#f6b64f" },
    ...daliaGrande(33, 27, 57, QUENTES),
    ...daliaGrande(270, 86, 63, QUENTES),
    ...daliaGrande(264, 7, 30, CLARAS),
    ...daliaGrande(45, 104, 27, CLARAS),
  ];
}

function cenaNoite(): TracoMoldura[] {
  const estrelas: [number, number, number][] = [
    [42, 20, 7.5], [78, 50, 4.5], [27, 72, 5], [96, 15, 4.5], [205, 34, 3.6], [219, 72, 5.4], [279, 77, 3.9], [108, 77, 3.3],
  ];
  const pontinhos: [number, number][] = [[60, 34], [105, 27], [162, 74], [201, 18], [240, 92], [18, 42], [132, 62], [291, 37]];
  return [
    { d: FAIXA, cor: AZUL_NOITE },
    { d: "M255 15A21 21 0 1 0 255 49A16.5 16.5 0 1 1 255 15Z", cor: "#f0cf6a" },
    { d: pontinhos.map(([x, y]) => circulo(x, y, 1)).join(""), cor: "#ffffff" },
    ...estrelas.map(([x, y, r], i) => ({ d: quatroPontas(x, y, r), cor: ESTRELA, movimento: piscando(i) })),
  ];
}

interface CoresDoTema {
  fundo: string;
  texto: string;
  texto2: string;
  apagado: string;
  linha: string;
  fenda: string;
  marca: string;
  ouro: string;
}

function tema(cena: () => TracoMoldura[], cores: CoresDoTema): () => TemaDoPerfil {
  return () => ({
    cena: cena(),
    marca: cores.marca,
    variaveis: {
      "--surface": cores.fundo,
      "--ground": cores.fenda,
      "--ink": cores.texto,
      "--ink-2": cores.texto2,
      "--muted": cores.apagado,
      "--faint": cores.apagado,
      "--line": cores.linha,
      "--line-soft": cores.linha,
      "--on-ink": cores.fundo,
      "--ouro": cores.ouro,
    },
  });
}

const TEMAS: Record<string, () => TemaDoPerfil> = {
  flor: tema(cenaFlor, {
    fundo: "#fff7f8", texto: "#4a1f2a", texto2: "#6a3642", apagado: "#8a5763", linha: "#f3dde1",
    fenda: "#fff7f8", marca: "#4a1f2a", ouro: "#8c6a0f",
  }),
  orbita: tema(cenaOrbita, {
    fundo: "#f5f6fa", texto: "#141a2a", texto2: "#2e3548", apagado: "#5b6478", linha: "#dde1ea",
    fenda: "#f5f6fa", marca: "#f0f3f9", ouro: "#8c6a0f",
  }),
  dalia: tema(cenaDalia, {
    fundo: "#fff6ec", texto: "#4a2410", texto2: "#6a3a1e", apagado: "#8a5a3c", linha: "#f3e0cc",
    fenda: "#fff6ec", marca: "#4a2410", ouro: "#8c6a0f",
  }),
  leque: tema(cenaLeque, {
    fundo: "#17181a", texto: "#f3e7c4", texto2: "#e4d8b4", apagado: "#c9a960", linha: "#3a3220",
    fenda: OURO_DECO, marca: "#f3e7c4", ouro: OURO_DECO,
  }),
  "noite-estrelada": tema(cenaNoite, {
    fundo: "#0d1330", texto: "#f0e6c4", texto2: "#dcd2b0", apagado: "#b3a877", linha: "#252c52",
    fenda: "#f0cf6a", marca: "#f0e6c4", ouro: "#d2a94b",
  }),
};

const MOLDURAS: Record<string, () => TracoMoldura[]> = {
  // As das patentes: a coroa cresce com o posto, e o metal diz a altura. O reflexo só
  // existe da prata para cima, então chegar nela é um marco.
  ciclo: () => coroa(GRAFITE, 5),
  sutura: () => coroa(GRAFITE, 8),
  residencia: () => coroa(BRONZE, 10),
  r2: () => coroa(PRATA, ULTIMO_NIVEL),
  r3: () => coroa(OURO, ULTIMO_NIVEL),
  preceptoria: () => coroa(OURO, ULTIMO_NIVEL, { cheia: true }),
  chefia: () => coroa(OURO, ULTIMO_NIVEL, { cheia: true, estrela: true }),
  // As da loja, cada uma com o seu tema (TEMAS, logo acima).
  flor: molduraFlor,
  orbita: molduraOrbita,
  dalia: molduraDalia,
  leque: molduraLeque,
  "noite-estrelada": molduraNoite,
  // Fora de venda: só as vê quem comprou.
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
const desenhadas = new Map<string, TracoMoldura[]>();

export function desenhoDaMoldura(id: string): TracoMoldura[] {
  if (!desenhadas.has(id)) desenhadas.set(id, MOLDURAS[id]?.() ?? []);
  return desenhadas.get(id)!;
}

const temasProntos = new Map<string, TemaDoPerfil>();

// Null para quem está sem moldura, com a da patente ou com uma antiga: nesses casos o
// crachá e o perfil seguem nas cores de sempre.
export function temaDaMoldura(id: string | null | undefined): TemaDoPerfil | null {
  if (!id || !TEMAS[id]) return null;
  if (!temasProntos.has(id)) temasProntos.set(id, TEMAS[id]());
  return temasProntos.get(id)!;
}
