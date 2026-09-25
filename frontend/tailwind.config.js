/** @type {import('tailwindcss').Config} */

// Cor cheia, fundo suave e texto sobre a cor de um nível de triagem
// (DESIGN_TRIAGEM.md §2) — gera `bg-t1`, `bg-t1-soft`, `text-t1-on` etc.
const nivel = (n) => ({ DEFAULT: `var(--t${n})`, soft: `var(--t${n}-soft)`, on: `var(--t${n}-on)` });

// Curvas de movimento (DESIGN_TRIAGEM.md §3). `brand` para trocas de estado;
// `suave` (desacelera longo) para o que entra, desliza ou cresce.
const BRAND = "cubic-bezier(0.2, 0, 0.2, 1)";
const SUAVE = "cubic-bezier(0.16, 1, 0.3, 1)";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ground: "var(--ground)",
        surface: "var(--surface)",
        ink: { DEFAULT: "var(--ink)", 2: "var(--ink-2)" },
        muted: "var(--muted)",
        faint: "var(--faint)",
        line: { DEFAULT: "var(--line)", soft: "var(--line-soft)" },
        onink: "var(--on-ink)",
        focus: "var(--focus)",
        t1: nivel(1),
        t2: nivel(2),
        t3: nivel(3),
        t4: nivel(4),
        t5: nivel(5),
      },
      fontFamily: {
        sans: ["Archivo", "Arial Narrow", "Arial", "sans-serif"],
      },
      fontSize: {
        titulo: ["44px", { lineHeight: "1.04", letterSpacing: "-0.03em", fontWeight: "800" }],
        subtitulo: ["24px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "800" }],
        bloco: ["17px", { lineHeight: "1.3", fontWeight: "700" }],
        corpo: ["15.5px", { lineHeight: "1.55", fontWeight: "400" }],
        apoio: ["13.5px", { lineHeight: "1.45", fontWeight: "400" }],
      },
      borderRadius: {
        etq: "3px",
        col: "4px",
        btn: "5px",
        card: "6px",
        caso: "8px",
        pill: "999px",
      },
      transitionDuration: {
        hover: "120ms",
        toggle: "180ms",
        desliza: "320ms",
        cresce: "700ms",
      },
      transitionTimingFunction: {
        brand: BRAND,
        suave: SUAVE,
      },
      keyframes: {
        // Tela ou bloco que chega: sobe 8px enquanto aparece.
        entrar: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "none" },
        },
        // Troca de caso/questão e de aba: desliza no sentido da navegação. 12px e
        // não 20: numa sessão longa isto roda centenas de vezes, muitas pela
        // tecla, e aí o movimento tem de ser quase imperceptível (2026-09-25).
        "entrar-frente": {
          from: { opacity: "0", transform: "translateX(12px)" },
          to: { opacity: "1", transform: "none" },
        },
        "entrar-tras": {
          from: { opacity: "0", transform: "translateX(-12px)" },
          to: { opacity: "1", transform: "none" },
        },
        desvanecer: { from: { opacity: "0" }, to: { opacity: "1" } },
        "desvanecer-saida": { from: { opacity: "1" }, to: { opacity: "0" } },
        // Menus e diálogos: crescem de 97% a partir da origem.
        surgir: {
          from: { opacity: "0", transform: "scale(0.97) translateY(-4px)" },
          to: { opacity: "1", transform: "none" },
        },
        sumir: {
          from: { opacity: "1", transform: "none" },
          to: { opacity: "0", transform: "scale(0.97) translateY(-4px)" },
        },
        // Barra de aproveitamento enchendo a partir da esquerda.
        crescer: { from: { transform: "scaleX(0)" }, to: { transform: "scaleX(1)" } },
        // Letra da alternativa escolhida.
        marcar: {
          "0%": { transform: "scale(0.8)" },
          "60%": { transform: "scale(1.08)" },
          "100%": { transform: "scale(1)" },
        },
        girar: {
          from: { opacity: "0", transform: "rotate(-90deg) scale(0.6)" },
          to: { opacity: "1", transform: "none" },
        },
        // Cursor de terminal: liga/desliga, sem meio-tom.
        piscar: { "0%, 49%": { opacity: "1" }, "50%, 100%": { opacity: "0" } },
      },
      // `backwards` aplica o quadro inicial durante o atraso (escalonamento) e
      // não deixa transform preso no elemento depois — um transform residual
      // viraria bloco de contenção para os `fixed` de dentro (diálogos).
      animation: {
        entrar: `entrar 240ms ${SUAVE} backwards`,
        "entrar-frente": `entrar-frente 200ms ${SUAVE} backwards`,
        "entrar-tras": `entrar-tras 200ms ${SUAVE} backwards`,
        desvanecer: `desvanecer 220ms ${BRAND} backwards`,
        "desvanecer-saida": `desvanecer-saida 160ms ${BRAND} forwards`,
        surgir: `surgir 200ms ${SUAVE} backwards`,
        sumir: `sumir 140ms ${BRAND} forwards`,
        crescer: `crescer 800ms ${SUAVE} backwards`,
        marcar: `marcar 260ms ${SUAVE}`,
        girar: `girar 320ms ${SUAVE}`,
        piscar: "piscar 1s steps(1, end) infinite",
      },
    },
  },
  plugins: [],
};
