/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "var(--ink-900)",
          700: "var(--ink-700)",
          500: "var(--ink-500)",
          300: "var(--ink-300)",
        },
        line: "var(--line)",
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        railbg: "var(--rail-bg)",
        action: {
          DEFAULT: "var(--action)",
          hover: "var(--action-hover)",
          soft: "var(--action-soft)",
        },
        correct: { DEFAULT: "var(--correct)", soft: "var(--correct-soft)" },
        wrong: { DEFAULT: "var(--wrong)", soft: "var(--wrong-soft)" },
        warn: { DEFAULT: "var(--warn)", soft: "var(--warn-soft)" },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        display: ["34px", { lineHeight: "1.15", letterSpacing: "-0.02em", fontWeight: "600" }],
        h1: ["24px", { lineHeight: "1.25", letterSpacing: "-0.01em", fontWeight: "600" }],
        h2: ["18px", { lineHeight: "1.35", fontWeight: "600" }],
        corpo: ["15px", { lineHeight: "1.55", fontWeight: "400" }],
        apoio: ["13px", { lineHeight: "1.45", fontWeight: "400" }],
        enunciado: ["17px", { lineHeight: "1.65", fontWeight: "400" }],
      },
      borderRadius: {
        btn: "6px",
        panel: "10px",
        pill: "999px",
      },
      transitionDuration: {
        hover: "120ms",
        toggle: "180ms",
      },
      transitionTimingFunction: {
        brand: "cubic-bezier(0.2, 0, 0.2, 1)",
      },
      spacing: {
        rail: "232px",
        "rail-collapsed": "64px",
      },
    },
  },
  plugins: [],
};
