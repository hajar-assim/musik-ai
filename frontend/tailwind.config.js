/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chambray': '#334389',
        'cararra': '#f4f4f1',
        'pharlap': '#a38980',
        'nepal': '#93a5c7',
        'botticelli': '#c6d1e0',
        'falcon': '#6d5666',
        'cashmere': '#e6c5a3',
        'waikawa': '#6677aa',
      },
      fontFamily: {
        'sans': ['Hoboken Serial', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
