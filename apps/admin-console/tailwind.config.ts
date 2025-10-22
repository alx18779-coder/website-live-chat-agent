import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './features/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'surface-primary': '#0F172A',
        'surface-elevated': '#1F2937',
        'brand-primary': '#2952FF',
        'brand-secondary': '#3BA3FF',
      },
      boxShadow: {
        glow: '0 0 24px rgba(41, 82, 255, 0.35)',
      },
    },
  },
  plugins: [],
};

export default config;
