import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        orange: "var(--orange)",
        violet: "var(--violet)",
        "deep-violet": "var(--deep-violet)",
        amber: "var(--amber)",
        lilac: "var(--lilac)",
        page: "var(--bg-page)",
        card: "var(--bg-card)",
        surface: "var(--bg-surface)",
        selected: "var(--bg-selected)",
        primary: "var(--text-primary)",
        secondary: "var(--text-secondary)",
        muted: "var(--text-muted)",
        border: "var(--border)",
        status: {
          ready: {
            bg: "var(--status-ready-bg)",
            text: "var(--status-ready-text)",
          },
          building: {
            bg: "var(--status-building-bg)",
            text: "var(--status-building-text)",
          },
          error: {
            bg: "var(--status-error-bg)",
            text: "var(--status-error-text)",
          },
          pro: {
            bg: "var(--status-pro-bg)",
            text: "var(--status-pro-text)",
          },
          draft: {
            bg: "var(--status-draft-bg)",
            text: "var(--status-draft-text)",
          },
        },
      },
      borderRadius: {
        card: "14px",
        input: "12px",
        button: "11px",
        pill: "10px",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.6s cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
};

export default config;
