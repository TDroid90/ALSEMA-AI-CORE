import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src.tsx", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0B0B0B",
        surface: "#141414",
        border: "#252525",
        accent: "#00C2FF",
      },
    },
  },
  plugins: [],
} satisfies Config;
