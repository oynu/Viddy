/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        viddy: {
          bg: "#0B0E17",
          card: "#131A29",
          cardHover: "#182236",
          border: "#1E2A42",
          accent: "#00F0FF",
          secondary: "#7928CA",
          danger: "#FF0055",
          success: "#00FF66",
          warning: "#FFB800"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
