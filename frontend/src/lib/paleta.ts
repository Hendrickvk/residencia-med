import type { CSSProperties } from "react";
import paleta from "./paleta.json";

// Paleta do avatar e das pastas: dez famílias de oito tons, do mais claro (1)
// ao mais escuro (8). O mesmo JSON valida no servidor (`db.normalizar_cor`),
// então as duas listas não têm como divergir. O banco guarda a chave
// (`azul-3`); o hex sai daqui, nunca do cliente — cor vinda de fora viraria CSS.
//
// Desde 2026-09-24 entram vermelho, laranja, amarelo, verde e azul, por decisão
// do usuário: as alunas acharam as cores poucas e parecidas. A regra que fica é
// a dos *tokens*: t1–t5 continuam só para nível de aproveitamento
// (DESIGN_TRIAGEM.md §2), e estes hex são outros, mesmo quando o matiz lembra.
//
// Estilo inline, e não classe do Tailwind: são 80 cores, e o Tailwind só gera a
// classe que acha escrita por extenso no código.

export interface Tom {
  hex: string;
  /** Texto por cima: branco ou tinta, o que der mais contraste (≥ 4,5:1,
   *  conferido em `tests/test_paleta.py`). */
  on: string;
}

export interface Familia {
  chave: string;
  nome: string;
  tons: Tom[];
}

export type Contexto = "perfil" | "pasta";

export const FAMILIAS: Familia[] = paleta.familias;
export const COR_PADRAO: Record<Contexto, string> = paleta.padrao;
// Chaves de antes da paleta nova (`ameixa`, `ardosia`...), traduzidas para o
// tom mais próximo. É o que evita migrar o banco: quem já tinha escolhido
// continua com a mesma cor, e a chave nova só é gravada no próximo "Salvar".
const LEGADO: Record<Contexto, Record<string, string>> = paleta.legado;

/** O tom mostrado quando a família ainda não foi escolhida: o do meio. */
export const TOM_DA_FAMILIA = 3;

/** Separa `azul-3` em família e índice (0 a 7); `undefined` se não existir. */
export function partes(chave: string): { familia: Familia; indice: number } | undefined {
  const corte = chave.lastIndexOf("-");
  const familia = FAMILIAS.find((f) => f.chave === chave.slice(0, corte));
  const indice = Number(chave.slice(corte + 1)) - 1;
  return familia?.tons[indice] ? { familia, indice } : undefined;
}

/** A chave que vale: a nova, a antiga traduzida, ou o padrão do contexto. */
export function normalizarCor(chave: string | null | undefined, contexto: Contexto): string {
  const traduzida = chave ? (LEGADO[contexto][chave] ?? chave) : "";
  return partes(traduzida) ? traduzida : COR_PADRAO[contexto];
}

function resolver(chave: string | null | undefined, contexto: Contexto) {
  const { familia, indice } = partes(normalizarCor(chave, contexto))!;
  return { familia, tom: familia.tons[indice] };
}

/** Cor cheia, com o texto legível por cima. */
export function corCheia(chave: string | null | undefined, contexto: Contexto): CSSProperties {
  const { tom } = resolver(chave, contexto);
  return { backgroundColor: tom.hex, color: tom.on };
}

/** Só o fundo, para faixas e pontos sem texto. */
export function corDeFundo(chave: string | null | undefined, contexto: Contexto): CSSProperties {
  return { backgroundColor: resolver(chave, contexto).tom.hex };
}

/** O véu do baralho: o tom do meio da família misturado ao papel, na
 *  proporção do tema (`--veu-pasta`). Do meio, e não o tom escolhido: um
 *  amarelo quase branco sumiria no papel claro, um cinza quase preto no escuro. */
export function veuDaPasta(chave: string | null | undefined): CSSProperties {
  const { familia } = resolver(chave, "pasta");
  return {
    backgroundColor: `color-mix(in srgb, ${familia.tons[TOM_DA_FAMILIA].hex} var(--veu-pasta), var(--surface))`,
  };
}
