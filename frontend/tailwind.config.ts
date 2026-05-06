import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        gov: {
          DEFAULT: '#0f5132',
          dark: '#0a3d24',
          light: '#e6f2ec',
          accent: '#c9a227',
        },
      },
      fontFamily: {
        sans: ['"Cairo"', '"Tajawal"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
