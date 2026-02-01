/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 紫黑主色
        dark: {
          950: '#0a0a0f',
          900: '#12121a',
          800: '#1a1a26',
          700: '#252533',
          600: '#32324a',
        },
        violet: {
          950: '#1e1b2e',
          800: '#2d2a4a',
          600: '#5b4d8c',
          500: '#7c6bb8',
          400: '#9d8dd4',
          300: '#b8a8e0',
        },
        accent: {
          violet: '#7c6bb8',
          red: '#c0392b',
        },
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.25s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
