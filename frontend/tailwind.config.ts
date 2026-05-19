import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark navy base
        bg: {
          primary:   "#050b1a",
          secondary: "#0d1b2e",
          tertiary:  "#112240",
          card:      "#0d1b2e",
          hover:     "#162b4d",
        },
        // Accent colors
        accent: {
          cyan:       "#00d4ff",
          "cyan-dim": "#0099bb",
          purple:     "#7c3aed",
          "purple-dim":"#5b21b6",
        },
        // Semantic
        success: "#10b981",
        warning: "#f59e0b",
        danger:  "#ef4444",
        // Text
        text: {
          primary:   "#f0f4ff",
          secondary: "#94a3b8",
          muted:     "#475569",
        },
        // Border
        border: {
          DEFAULT: "#1e3a5f",
          bright:  "#2d5a8e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      backgroundImage: {
        "gradient-radial":    "radial-gradient(var(--tw-gradient-stops))",
        "gradient-card":      "linear-gradient(135deg, #0d1b2e 0%, #112240 100%)",
        "gradient-accent":    "linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)",
        "gradient-glow":      "radial-gradient(ellipse at center, rgba(0,212,255,0.15) 0%, transparent 70%)",
      },
      boxShadow: {
        "glow-cyan":   "0 0 20px rgba(0, 212, 255, 0.25)",
        "glow-purple": "0 0 20px rgba(124, 58, 237, 0.25)",
        "card":        "0 4px 24px rgba(0, 0, 0, 0.4)",
        "card-hover":  "0 8px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 212, 255, 0.1)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":    "fadeIn 0.3s ease-in-out",
        "slide-up":   "slideUp 0.4s ease-out",
        "glow":       "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%":   { boxShadow: "0 0 10px rgba(0, 212, 255, 0.2)" },
          "100%": { boxShadow: "0 0 30px rgba(0, 212, 255, 0.5)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
