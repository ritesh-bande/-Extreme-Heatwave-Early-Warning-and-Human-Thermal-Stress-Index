export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: '#0D0F12',
        surface: '#15181C',
        'surface-raised': '#1B1F24',
        subtle: '#262B31',
        primary: '#ECEDEE',
        secondary: '#9BA1A6',
        tertiary: '#6B7075',
        accent: '#4C9F70',
        risk: {
          green: '#4C9F70',
          yellow: '#C9A227',
          orange: '#C9752D',
          red: '#B84A3E',
          purple: '#7A5C9E'
        }
      },
      fontFamily: {
        sans: ['"Public Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        xs: '11px',
        sm: '13px',
        base: '15px',
        lg: '18px',
        xl: '24px',
        '2xl': '40px',
        '3xl': '64px',
      },
      letterSpacing: {
        ui: '0.04em'
      }
    },
  },
  plugins: [],
}
