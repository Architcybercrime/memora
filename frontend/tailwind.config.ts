import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0b0f",
        surface: "#15151c",
        border: "#23232c",
        accent: "#7c5cff",
        muted: "#8b8b96",
      },
    },
  },
  plugins: [],
} satisfies Config;
