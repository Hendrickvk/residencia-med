import assert from "node:assert/strict";
import { test } from "node:test";

import { desenhoDaMoldura, temaDaMoldura } from "../src/lib/cosmeticos.ts";

const PATENTES = ["ciclo", "sutura", "residencia", "r2", "r3", "preceptoria", "chefia"];
const COM_TEMA = ["flor", "orbita", "dalia", "leque", "noite-estrelada"];

function luminancia(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contraste(a: string, b: string): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
}

test("cada moldura nova desenha e traz um tema", () => {
  for (const id of COM_TEMA) {
    assert.ok(desenhoDaMoldura(id).length > 0, id);
    const tema = temaDaMoldura(id);
    assert.ok(tema, id);
    for (const t of [...desenhoDaMoldura(id), ...tema.cena]) assert.doesNotMatch(t.d, /NaN|undefined/, id);
  }
});

test("toda moldura da loja se mexe", () => {
  for (const id of COM_TEMA) {
    assert.ok(desenhoDaMoldura(id).some((t) => t.movimento), id);
  }
});

test("patente, moldura antiga e nenhuma moldura não mudam o perfil", () => {
  for (const id of [...PATENTES, "monitor", "item-do-futuro", null, undefined]) {
    assert.equal(temaDaMoldura(id), null, String(id));
  }
});

test("o texto de cada tema passa AA sobre o fundo dele", () => {
  for (const id of COM_TEMA) {
    const v = temaDaMoldura(id)!.variaveis;
    for (const cor of ["--ink", "--ink-2", "--muted"]) {
      assert.ok(contraste(v[cor], v["--surface"]) >= 4.5, `${id} ${cor}`);
    }
  }
});

test("toda patente desenha, sem coordenada inválida", () => {
  for (const id of PATENTES) {
    const tracos = desenhoDaMoldura(id);
    assert.ok(tracos.length > 0, id);
    for (const t of tracos) assert.doesNotMatch(t.d, /NaN|undefined/, id);
  }
});

test("o reflexo só existe da prata para cima, e sobe do pé ao topo", () => {
  for (const id of ["ciclo", "sutura", "residencia"]) {
    assert.ok(desenhoDaMoldura(id).every((t) => t.atraso === undefined), id);
  }
  for (const id of ["r2", "r3", "preceptoria", "chefia"]) {
    const atrasos = desenhoDaMoldura(id).flatMap((t) => (t.atraso === undefined ? [] : [t.atraso]));
    assert.ok(atrasos.length >= 12, id);
    assert.deepEqual(atrasos, [...atrasos].sort((a, b) => a - b), id);
  }
});

test("a coroa cresce com a patente", () => {
  const folhas = (id: string) => desenhoDaMoldura(id).filter((t) => t.largura === undefined && t.atraso === undefined).length;
  const contagem = PATENTES.map(folhas);
  assert.deepEqual(contagem, [...contagem].sort((a, b) => a - b));
  assert.ok(folhas("ciclo") < folhas("residencia") && folhas("r3") < folhas("chefia"));
});

test("id desconhecido não desenha nada", () => {
  assert.deepEqual(desenhoDaMoldura("item-do-futuro"), []);
});
