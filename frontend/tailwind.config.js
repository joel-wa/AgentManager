/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#1e1e1e',
        'dark-surface': '#252526',
        'dark-hover': '#2d2d30',
        'dark-border': '#3c3c3c',
        'accent-blue': '#0078d4',
        'accent-green': '#4ec9b0',
        'accent-orange': '#ce9178',
        'accent-purple': '#c586c0',
      },
    },
  },
  plugins: [],
}
