/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        pro: {
          DEFAULT: "#2563eb",
          light: "#93c5fd",
          bg: "#eff6ff",
        },
        con: {
          DEFAULT: "#dc2626",
          light: "#fca5a5",
          bg: "#fef2f2",
        },
        ink: {
          950: "#0b0e14",
          900: "#12161f",
          800: "#1b2130",
          700: "#252c3d",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
