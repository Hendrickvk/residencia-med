// O enunciado é texto, e a tabela do caderno vem nele como linhas `| a | b |`: a mesma
// forma do Markdown, que também se lê no admin. Texto sem isso sai como sempre saiu.
export type BlocoEnunciado =
  | { tipo: "texto"; texto: string }
  | { tipo: "tabela"; titulo: string[]; linhas: string[][] };

function celulas(linha: string) {
  return linha
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());
}

export function blocosDoEnunciado(enunciado: string): BlocoEnunciado[] {
  const blocos: BlocoEnunciado[] = [];
  let tabela: string[][] = [];

  function fecharTabela() {
    if (tabela.length >= 2) {
      blocos.push({ tipo: "tabela", titulo: tabela[0], linhas: tabela.slice(1) });
    } else if (tabela.length === 1) {
      // Uma linha só não é tabela: um "|" solto no texto continua texto.
      blocos.push({ tipo: "texto", texto: tabela[0].join(" | ") });
    }
    tabela = [];
  }

  for (const linha of enunciado.split("\n")) {
    if (linha.trim().startsWith("|")) {
      tabela.push(celulas(linha));
      continue;
    }
    fecharTabela();
    if (linha.trim()) blocos.push({ tipo: "texto", texto: linha.trim() });
  }
  fecharTabela();
  return blocos;
}
