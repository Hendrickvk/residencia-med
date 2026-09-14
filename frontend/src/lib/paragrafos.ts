// Discussão do caso em parágrafos (DESIGN_TRIAGEM.md §6). As explicações do
// banco são um bloco único de texto (média de ~750 caracteres); a quebra é
// feita só na exibição, sem mexer no conteúdo. Regra testada nas 645
// explicações do banco antes de entrar aqui.

// Fim de frase seguido de maiúscula.
const FRASE = /(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])/;
// Frase que passa a discutir outra alternativa: "(A)", "Alternativa B", "C)".
const OUTRA_ALTERNATIVA = /\([A-E]\)|^(Alternativa|Letra)\s+[A-E]\b|^[A-E]\)/;

// Alternativas com menos que isso não ganham parágrafo próprio (ficava picotado).
const CURTO = 90;
// Bloco acima disso é dividido por frases em trechos de ~ALVO caracteres...
const LONGO = 480;
const ALVO = 280;
// ...sem deixar uma sobra minúscula sozinha no fim.
const RESTO_MINIMO = 120;

const tamanho = (frases: string[]) => frases.join(" ").length;

export function dividirEmParagrafos(texto: string): string[] {
  // Quebras escritas no próprio texto têm prioridade.
  const quebrasReais = texto
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean);
  if (quebrasReais.length > 1) return quebrasReais;

  // 1. Um bloco por alternativa discutida; o primeiro explica a resposta certa.
  const blocos: string[][] = [];
  for (const frase of texto.trim().split(FRASE)) {
    if (blocos.length === 0 || OUTRA_ALTERNATIVA.test(frase)) blocos.push([frase]);
    else blocos[blocos.length - 1].push(frase);
  }

  // 2. Alternativas curtas seguidas dividem o mesmo parágrafo (nunca com o primeiro).
  const juntos: string[][] = [blocos[0]];
  for (const bloco of blocos.slice(1)) {
    const anterior = juntos[juntos.length - 1];
    if (juntos.length > 1 && (tamanho(bloco) < CURTO || tamanho(anterior) < CURTO)) anterior.push(...bloco);
    else juntos.push(bloco);
  }

  // 3. Blocos longos (explicações que não citam as alternativas) viram trechos por frase.
  const paragrafos: string[] = [];
  for (const bloco of juntos) {
    if (tamanho(bloco) <= LONGO || bloco.length < 2) {
      paragrafos.push(bloco.join(" "));
      continue;
    }
    let atual: string[] = [];
    for (const frase of bloco) {
      atual.push(frase);
      if (tamanho(atual) >= ALVO) {
        paragrafos.push(atual.join(" "));
        atual = [];
      }
    }
    if (atual.length > 0) {
      const resto = atual.join(" ");
      if (resto.length < RESTO_MINIMO && paragrafos.length > 0) paragrafos[paragrafos.length - 1] += ` ${resto}`;
      else paragrafos.push(resto);
    }
  }
  return paragrafos;
}
