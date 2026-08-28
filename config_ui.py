import os
import re

# 1. Update index.html
with open("frontend/index.html", "r") as f:
    html = f.read()

fonts = """    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">"""
if "fonts.googleapis.com" not in html:
    html = html.replace("</head>", fonts + "\n  </head>")
with open("frontend/index.html", "w") as f:
    f.write(html)

# 2. Update tailwind.config.ts
with open("frontend/tailwind.config.ts", "w") as f:
    f.write("""import type { Config } from 'tailwindcss'

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
} satisfies Config
""")

# 3. Update index.css
with open("frontend/src/index.css", "r") as f:
    css = f.read()

base_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-base text-primary font-sans;
  }
}

@layer components {
  .tabular-data {
    @apply font-mono;
    font-variant-numeric: tabular-nums;
  }
  
  .card-surface {
    @apply bg-surface border border-subtle rounded-xl;
    box-shadow: 0 1px 3px rgba(0,0,0,0.4);
  }
}

/* Custom Scrollbar for Ops Dashboard */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: theme('colors.base');
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: theme('colors.subtle');
  border-radius: 4px;
}

/* Continuous Surface Blending (for Map) */
.heat-surface-map .leaflet-overlay-pane {
  filter: blur(14px) contrast(1.4);
}
path.hover-reveal-border:hover, path.selected-cell {
  filter: blur(0px) !important;
  stroke: rgba(236,237,238,0.8);
  stroke-width: 2px;
}
"""
with open("frontend/src/index.css", "w") as f:
    f.write(base_css)

print("Config complete.")
