// Sem dependência nova: `node --test` lê o TypeScript direto (npm test).
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";

const armazenado = new Map<string, string>();
Object.assign(globalThis, {
  localStorage: {
    getItem: (k: string) => armazenado.get(k) ?? null,
    setItem: (k: string, v: string) => void armazenado.set(k, v),
    removeItem: (k: string) => void armazenado.delete(k),
  },
});

const { envioDoCaso, lerSessao, respostaPendente, salvarSessao } = await import("../src/lib/sessaoSalva.ts");

const CHAVE = "residencia-med:sessao-pratica";
const questao = { id: 7, resposta_correta: "B" } as never;
const base = {
  email: "a@teste.local",
  filtros: {} as never,
  questoes: [questao],
  idx: 0,
  respondidas: [],
  resultados: [],
  marcadas: [],
  duracaoMs: 1000,
  sessaoId: "s1",
};

beforeEach(() => armazenado.clear());

test("devolve o caso como estava: alternativa, confirmação, chute e tempo", () => {
  salvarSessao({ ...base, caso: { selecionada: "A", confirmado: true, chutando: true, decorridoMs: 42_000 } });
  assert.deepEqual(lerSessao()?.caso, { selecionada: "A", confirmado: true, chutando: true, decorridoMs: 42_000 });
});

test("sessão salva antes deste campo abre com o caso em branco, sem perder o lugar", () => {
  armazenado.set(CHAVE, JSON.stringify({
    ...base, sessaoId: undefined, idx: 0, versao: 1, salvoEm: 1234 + Date.now() - 1234,
  }));
  const lida = lerSessao();
  assert.deepEqual(lida?.caso, { selecionada: null, confirmado: false, chutando: false, decorridoMs: 0 });
  assert.ok(lida?.sessaoId, "ganha um identificador para o envio");
  assert.equal(lida?.idx, 0);
});

test("sessão vencida não volta", () => {
  armazenado.set(CHAVE, JSON.stringify({ ...base, versao: 1, salvoEm: Date.now() - 13 * 3600 * 1000 }));
  assert.equal(lerSessao(), null);
});

test("só há resposta pendente depois de confirmar", () => {
  const sem = { ...base, versao: 1 as const, salvoEm: 0, caso: { selecionada: "A", confirmado: false, chutando: false, decorridoMs: 5 } };
  assert.equal(respostaPendente(sem), null);
});

test("a resposta pendente leva o tempo medido e o chute", () => {
  const s = { ...base, versao: 1 as const, salvoEm: 0, caso: { selecionada: "A", confirmado: true, chutando: true, decorridoMs: 9000 } };
  assert.deepEqual(respostaPendente(s), {
    envio: "s1:7:0",
    payload: { questao_id: 7, alternativa: "A", confianca: "chute", tempo_ms: 9000 },
  });
});

test("acerto sem chute vai como seguro, erro sem chute vai sem confiança", () => {
  const com = (selecionada: string) => ({ ...base, versao: 1 as const, salvoEm: 0, caso: { selecionada, confirmado: true, chutando: false, decorridoMs: 1 } });
  assert.equal(respostaPendente(com("B"))?.payload.confianca, "seguro");
  assert.equal(respostaPendente(com("A"))?.payload.confianca, undefined);
});

test("o mesmo caso gera o mesmo envio, e cabe no limite da API", () => {
  assert.equal(envioDoCaso("s", 7, 0), envioDoCaso("s", 7, 0));
  assert.ok(envioDoCaso(crypto.randomUUID(), 999_999, 499).length <= 64);
});
