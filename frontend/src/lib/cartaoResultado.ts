// Cartão de resultado de prova oficial para compartilhar: é o que faz a
// plataforma circular nos grupos de estudo. 1080×1350 (4:5, o formato que o
// WhatsApp e o Instagram mostram inteiro), sempre escuro, como a imagem de
// prévia do link. Leva a prova, o aproveitamento, o desempenho por
// área e a assinatura com o endereço — nunca questão, alternativa ou gabarito:
// o que circula é o resultado da aluna, e a plataforma vai como assinatura.
//
// As cores saem dos tokens `.dark` do theme.css, lidas de um elemento
// temporário, para não haver hex solto aqui (DESIGN_TRIAGEM.md §3).

import { nivelTriagem } from "./triagem";

export interface DadosCartao {
  prova: string; // "Revalida 2025/1"
  pct: number; // aproveitamento, 0–100
  acertos: number;
  total: number;
  areas: { area: string; pct_acerto: number }[];
  emBlocos?: boolean; // a prova inteira, feita em blocos (db.prova_em_blocos)
}

const LARGURA = 1080;
const ALTURA = 1350;
const MARGEM = 88;
const SITE = "qualaconduta.com.br";

function tokensEscuros() {
  const el = document.createElement("div");
  el.className = "dark";
  el.hidden = true;
  document.body.appendChild(el);
  const css = getComputedStyle(el);
  const v = (nome: string) => css.getPropertyValue(nome).trim();
  const t = {
    ground: v("--ground"),
    ink: v("--ink"),
    ink2: v("--ink-2"),
    muted: v("--muted"),
    trilho: v("--line-soft"),
    linha: v("--line"),
    nivel: [1, 2, 3, 4, 5].map((n) => v(`--t${n}`)),
  };
  el.remove();
  return t;
}

// `fontStretch` e `letterSpacing` do canvas: onde o navegador não tiver, o
// texto sai na largura normal, e só.
function fonte(ctx: CanvasRenderingContext2D, peso: number, px: number, largura = "normal", espaco = "0px") {
  ctx.font = `${peso} ${px}px Archivo, "Arial Narrow", Arial, sans-serif`;
  const estilo = ctx as unknown as Record<string, string>;
  estilo.fontStretch = largura;
  estilo.letterSpacing = espaco;
}

function retangulo(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, w, h, r);
  else ctx.rect(x, y, w, h);
  ctx.fill();
}

function caber(ctx: CanvasRenderingContext2D, texto: string, max: number): string {
  if (ctx.measureText(texto).width <= max) return texto;
  let t = texto;
  while (t.length > 1 && ctx.measureText(`${t}…`).width > max) t = t.slice(0, -1);
  return `${t.trimEnd()}…`;
}

export async function desenharCartao(d: DadosCartao): Promise<Blob> {
  // A Archivo já está na página; isto só garante os pesos antes de desenhar.
  await Promise.all(["400", "500", "700", "800"].map((p) => document.fonts.load(`${p} 40px Archivo`)));
  const c = tokensEscuros();
  const canvas = document.createElement("canvas");
  canvas.width = LARGURA;
  canvas.height = ALTURA;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("canvas indisponível");
  ctx.fillStyle = c.ground;
  ctx.fillRect(0, 0, LARGURA, ALTURA);

  // Marca: as cinco barras (20/16/12/8/4, em escala 3) e o nome.
  const base = 150;
  [20, 16, 12, 8, 4].forEach((h, i) => {
    ctx.fillStyle = c.nivel[i];
    retangulo(ctx, MARGEM + i * 18, base - h * 3, 12, h * 3, 3);
  });
  ctx.fillStyle = c.ink;
  fonte(ctx, 800, 54, "semi-expanded", "-1.5px");
  ctx.fillText("Conduta", MARGEM + 5 * 18 + 16, base);

  // A prova e o aproveitamento, sem a etiqueta do nível (decisão do usuário):
  // quem vê o cartão não conhece a escala, e um "Urgente" ao lado de um
  // resultado bom inibe quem postaria. O nível fica só na cor das barras.
  ctx.fillStyle = c.ink2;
  fonte(ctx, 700, 46);
  // Feita em blocos, o cartão diz: quatro sentadas não são cinco horas seguidas.
  ctx.fillText(d.emBlocos ? `${d.prova} · em blocos` : d.prova, MARGEM, 262);
  ctx.fillStyle = c.ink;
  fonte(ctx, 800, 250, "semi-expanded", "-10px");
  ctx.fillText(`${d.pct}%`, MARGEM - 8, 500);
  ctx.fillStyle = c.ink2;
  fonte(ctx, 400, 40);
  ctx.fillText(`${d.acertos} acertos em ${d.total} questões`, MARGEM, 584);

  // Desempenho por área, do pior para o melhor, como no resultado.
  const areas = [...d.areas].sort((a, b) => a.pct_acerto - b.pct_acerto).slice(0, 5);
  if (areas.length > 0) {
    ctx.fillStyle = c.muted;
    fonte(ctx, 700, 26, "condensed", "3px");
    ctx.fillText("POR ÁREA", MARGEM, 694);
    const util = LARGURA - 2 * MARGEM;
    areas.forEach((a, i) => {
      const y = 758 + i * 84;
      const texto = `${Math.round(a.pct_acerto)}%`;
      fonte(ctx, 700, 34);
      const larguraPct = ctx.measureText(texto).width;
      ctx.fillStyle = c.ink;
      ctx.fillText(texto, MARGEM + util - larguraPct, y);
      fonte(ctx, 500, 34);
      ctx.fillText(caber(ctx, a.area, util - larguraPct - 24), MARGEM, y);
      ctx.fillStyle = c.trilho;
      retangulo(ctx, MARGEM, y + 16, util, 8, 4);
      ctx.fillStyle = c.nivel[nivelTriagem(a.pct_acerto) - 1];
      retangulo(ctx, MARGEM, y + 16, Math.max(8, (util * a.pct_acerto) / 100), 8, 4);
    });
  }

  // Assinatura: o convite e o endereço.
  ctx.fillStyle = c.linha;
  ctx.fillRect(MARGEM, 1164, LARGURA - 2 * MARGEM, 2);
  ctx.fillStyle = c.ink;
  fonte(ctx, 800, 42, "normal", "-1px");
  ctx.fillText("Descubra onde você perde pontos.", MARGEM, 1232);
  ctx.fillStyle = c.muted;
  fonte(ctx, 600, 34);
  ctx.fillText(SITE, MARGEM, 1284);

  return new Promise((ok, erro) => canvas.toBlob((b) => (b ? ok(b) : erro(new Error("canvas vazio"))), "image/png"));
}

export function nomeArquivoCartao(prova: string): string {
  const slug = prova
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `conduta-${slug}.png`;
}

// No celular abre o compartilhamento do sistema (WhatsApp, Instagram...). No
// computador baixa a imagem, mesmo onde o navegador compartilharia: a janela
// de compartilhar do Windows não tem "salvar", e o WhatsApp Web não aparece
// nela. O arquivo chega pronto: o `share` precisa sair do toque, e desenhar
// antes dele podia estourar o tempo que o navegador dá ao gesto.
export async function compartilharCartao(
  arquivo: File,
  prova: string,
  pct: number,
  emBlocos = false,
): Promise<"compartilhado" | "baixado" | "cancelado"> {
  const texto = `Refiz a prova ${prova}${emBlocos ? ", em blocos," : ""} no Conduta: ${pct}% de acerto. https://${SITE}`;
  if (matchMedia("(pointer: coarse)").matches && navigator.canShare?.({ files: [arquivo] })) {
    try {
      await navigator.share({ files: [arquivo], text: texto });
      return "compartilhado";
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return "cancelado";
      // Qualquer outra recusa do navegador: segue para o download.
    }
  }
  const url = URL.createObjectURL(arquivo);
  const a = document.createElement("a");
  a.href = url;
  a.download = arquivo.name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  return "baixado";
}
