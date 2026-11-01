import assert from "node:assert/strict";
import { test } from "node:test";
import { blocosDoEnunciado } from "../src/lib/enunciado.ts";

test("enunciado sem tabela sai como um parágrafo só", () => {
  assert.deepEqual(blocosDoEnunciado("Um caso comum."), [{ tipo: "texto", texto: "Um caso comum." }]);
});

test("tabela vira título e linhas, com o texto em volta na ordem", () => {
  const blocos = blocosDoEnunciado("Antes.\n| Exame | Valor |\n| Ureia | 28 mg/dL |\n| TSH | 5 |\nDepois.");
  assert.deepEqual(blocos, [
    { tipo: "texto", texto: "Antes." },
    { tipo: "tabela", titulo: ["Exame", "Valor"], linhas: [["Ureia", "28 mg/dL"], ["TSH", "5"]] },
    { tipo: "texto", texto: "Depois." },
  ]);
});

test("célula vazia continua sendo célula", () => {
  const [tabela] = blocosDoEnunciado("| Exame | Resultado | Referência |\n| Bilirrubinas | 12,0 g/dL |  |");
  assert.equal(tabela.tipo, "tabela");
  assert.deepEqual(tabela.tipo === "tabela" && tabela.linhas[0], ["Bilirrubinas", "12,0 g/dL", ""]);
});

test("barra solta no meio do texto não vira tabela", () => {
  assert.equal(blocosDoEnunciado("Razão A | B no exame.")[0].tipo, "texto");
  assert.equal(blocosDoEnunciado("| só uma linha |")[0].tipo, "texto");
});
