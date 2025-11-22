/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--color-background))',
        foreground: 'hsl(var(--color-foreground))',
        card: 'hsl(var(--color-card))',
        'card-foreground': 'hsl(var(--color-card-foreground))',
        primary: 'hsl(var(--color-primary))',
        'primary-foreground': 'hsl(var(--color-primary-foreground))',
        secondary: 'hsl(var(--color-secondary))',
        'secondary-foreground': 'hsl(var(--color-secondary-foreground))',
        muted: 'hsl(var(--color-muted))',
        'muted-foreground': 'hsl(var(--color-muted-foreground))',
        accent: 'hsl(var(--color-accent))',
        'accent-foreground': 'hsl(var(--color-accent-foreground))',
        destructive: 'hsl(var(--color-destructive))',
        'destructive-foreground': 'hsl(var(--color-destructive-foreground))',
        border: 'hsl(var(--color-border))',
        input: 'hsl(var(--color-input))',
        ring: 'hsl(var(--color-ring))',
      },
    },
  },
  plugins: [],
}
