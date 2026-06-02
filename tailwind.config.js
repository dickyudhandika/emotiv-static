/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      colors: {
        navy: '#09153b',
        primary: '#3363ff',
        light: '#eceef6',
        accent: '#d82d5f',
      },
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    }
  },
  plugins: [],
}
