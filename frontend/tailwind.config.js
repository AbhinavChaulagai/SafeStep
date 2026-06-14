/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        risk: {
          low: '#22c55e',
          moderate: '#eab308',
          elevated: '#f97316',
          high: '#ef4444',
        },
      },
    },
  },
  plugins: [],
}
