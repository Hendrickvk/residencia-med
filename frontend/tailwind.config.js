/** @type {import('tailwindcss').Config} */

// Cor cheia, fundo suave e texto sobre a cor de um nível de triagem
// (DESIGN_TRIAGEM.md §2) — gera `bg-t1`, `bg-t1-soft`, `text-t1-on` etc.
const nivel = (n) => ({ DEFAULT: `var(--t${n})`, soft: `var(--t${n}-soft)`, on: `var(--t${n}-on)` });

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
        enunciado: ["18px", { lineHeight: "1.7", fontWeight: "400" }],
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
      },
      transitionTimingFunction: {
        brand: "cubic-bezier(0.2, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
};
