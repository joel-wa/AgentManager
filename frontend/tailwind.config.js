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
        'dark-surface': '#2a2a2a',
        'dark-hover': '#333333',
        'dark-border': 'rgba(255, 255, 255, 0.08)',
        'accent-blue': '#3b82f6',
        'accent-green': '#10b981',
        'accent-orange': '#f59e0b',
        'accent-purple': '#8b5cf6',
      },
      backdropBlur: {
        'xl': '40px',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Consolas', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
