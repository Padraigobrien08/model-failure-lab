import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["selector", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ground: "var(--ground)",
        panel: "var(--panel)",
        raised: "var(--panel-raised)",
        ink: "var(--ink)",
        "muted-ink": "var(--muted-ink)",
        line: "var(--line)",
        "line-soft": "var(--line-soft)",
        accent: "var(--accent)",
        "accent-text": "var(--accent-text)",
        "accent-wash": "var(--accent-wash)",
        "on-accent": "var(--on-accent)",
        "btn-bg": "var(--btn-bg)",
        "btn-ink": "var(--btn-ink)",
        bad: "var(--red)",
        "bad-bg": "var(--red-bg)",
        "bad-panel": "var(--red-panel)",
        "bad-line": "var(--red-line)",
        "bad-head": "var(--red-head)",
        "bad-chip-bg": "var(--red-chip-bg)",
        "bad-chip-ink": "var(--red-chip-ink)",
        good: "var(--green)",
        "good-bg": "var(--green-bg)",
        warn: "var(--warn)",
        "warn-bg": "var(--warn-bg)",
        "cand-panel": "var(--cand-panel)",
        "cand-head": "var(--cand-head)",
      },
      borderRadius: {
        tok: "var(--radius-tok)",
        "tok-sm": "calc(var(--radius-tok) * 0.75)",
      },
      fontFamily: {
        heading: ["var(--font-heading)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
        sans: ["var(--font-body)"],
      },
    },
  },
  plugins: [],
};

export default config;
