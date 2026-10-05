/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        serif: [
          "Georgia",
          "ui-serif",
          "serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      colors: {
        paper: {
          50:  "#FDFCFA",
          100: "#F7F5F2",
          200: "#EDE9E3",
          300: "#DDD8D0",
          400: "#C5BEB4",
        },
        ink: {
          900: "#1A1917",
          700: "#3D3A35",
          500: "#6B6760",
          400: "#8C8880",
          300: "#B0ACA5",
        },
        accent: "#1C4ED8",
        danger: "#B91C1C",
        success: "#15803D",
        warn:    "#B45309",
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      maxWidth: {
        content: "72rem",
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
