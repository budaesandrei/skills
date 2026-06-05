# Theming Knowledge Base

Reference guide for color theming, light/dark mode design, and industry-specific UI patterns. Synthesized from NN/g research, Material Design 3, Stripe engineering, Nathan Curtis (EightShapes), CSS-Tricks, Toptal, and Vercel/Linear design teams.

## Theme Toggle: Light / System / Dark

Always implement a **3-state toggle**, not just light/dark:

| Option | Behavior |
|--------|----------|
| Light | Forces light theme regardless of OS |
| System | Follows `prefers-color-scheme` (default on first visit) |
| Dark | Forces dark theme regardless of OS |

Store user's explicit choice in `localStorage` only when they override system default.

## Light vs Dark: When to Use Which (Research-Based)

### Evidence Summary (NN/g, 2020)

- Light mode produces better visual acuity and proofreading performance for normal-vision users
- The smaller the font, the stronger light mode's advantage
- Dark mode may protect against myopia long-term
- Dark mode benefits users with cataracts/cloudy ocular media
- In nighttime ambient light, light mode STILL outperforms dark for small text

### Recommendation

Default to light unless the product category warrants dark-first (see Industry Patterns below). ALWAYS offer the toggle.

## Deriving a Dark Theme from Light

### The Wrong Way
- Simply inverting colors
- Using pure black (#000000) backgrounds
- Using pure white (#ffffff) text
- Keeping saturated accent colors unchanged

### The Right Way (Material Design 3 Tonal System)

Define a **tonal scale** (13 values per color, tone 0-100). Light picks from dark tones for text on light surfaces. Dark picks from light tones for text on dark surfaces.

| Role | Light Theme Tone | Dark Theme Tone |
|------|-----------------|-----------------|
| Surface | 99 | 10 |
| Surface Container Low | 96 | 12 |
| Surface Container | 94 | 17 |
| Surface Container High | 92 | 22 |
| On Surface (text) | 10 | 90 |
| On Surface Variant | 30 | 80 |
| Primary | 40 | 80 |
| On Primary | 100 | 20 |

### Key Rules

1. **Never pure black** — use #121212 or slightly tinted dark gray
2. **Never pure white text** — use #e0e0e0 or similar off-white
3. **Desaturate accent colors** — saturated colors vibrate against dark backgrounds
4. **Elevation = lighter surfaces** — higher elements are lighter (NOT darker)
5. **Dim images** — apply `filter: brightness(.8) contrast(1.2)` in dark mode
6. **Medium font weight** — avoid very heavy or very light fonts on dark
7. **Increase letter-spacing slightly** — light text on dark needs more breathing room

### Dark Mode Shadows

- Don't naively invert shadows (light shadow on dark = ugly)
- Use very subtle dark shadows only if background is light enough gray
- Prefer **surface elevation via tonal shift** over shadows in dark mode
- Borders (`1px solid rgba(255,255,255,0.08)`) replace shadows in modern dark UIs

## Color Architecture for Dual Themes (Nathan Curtis / EightShapes)

### Process

1. **Inventory neutrals** — audit all grays, prune to 8-12 harmonious tints
2. **Define semantic roles** — primary text, secondary text, interactive, error, disabled, background, surface, border (heavy + hairline)
3. **Map each role to BOTH modes** — fill a matrix: role x background setting
4. **Tokenize** — CSS custom properties named by role, values swap per theme
5. **Test components on ALL backgrounds** — stack your library on white, gray, dark side-by-side

### Gotchas

- Link color on dark backgrounds: blue often fails WCAG — may need to use white
- Error red on dark: test carefully, often needs lightening
- Background-on-background: cards on dark canvases need testing
- States (hover/active): use opacity shifts, not new color picks per theme

## Perceptual Color (Stripe's Approach)

Standard HSL lightness is NOT perceptually uniform — yellow looks lighter than blue at the same L value.

### Use CIELAB/OKLCH for Theme Construction

- Colors at the same CIELAB lightness appear equally bright to human eyes
- Build palette in perceptual space, then derive dark theme as a "level shift"
- This ensures: at any given contrast level, all hues have identical contrast ratios against backgrounds

### Practical Implication

Use the `material-color-utilities` library which implements HCT (Hue-Chroma-Tone) — Google's perceptually uniform color space designed specifically for theming.

## Industry-Specific Design Patterns

### Modern SaaS / Developer Tools

**Examples**: Linear, Vercel, Notion, Raycast, Warp

| Trait | Pattern |
|-------|---------|
| Default theme | Dark |
| Border radius | 12-16px |
| Shadows | None — replaced by 1px low-opacity borders |
| Depth | Surface layering at different opacities |
| Palette | 1-2 accent colors max, rest neutrals |
| Typography | Clean grotesque sans-serif (custom fonts common) |
| Spacing | Generous negative space |
| Effects | Subtle backdrop-filter blur for overlays |
| Transitions | Fast (100-200ms) |

**When dark mode is NOT appropriate for SaaS**: Dense data tables, complex forms, many mixed content types. Consider light default for productivity/data-heavy B2B SaaS.

### Finance / Fintech

| Sub-category | Default | Why |
|---|---|---|
| Trading platforms | Dark | Terminal-style, information density |
| Retail banking | Light | Trust, clarity, accessibility-first |
| Millennial fintech | Dark | Sophisticated, premium |
| Data dashboards | Dark | Reduced eye strain for all-day use |

**Colors**: Blue (trust), green (gains), red (losses), gold (premium).
**Shadows**: Yes — used for card separation in data-dense layouts.
**Radius**: Conservative (4-8px).

### Healthcare / Medical

| Trait | Pattern |
|-------|---------|
| Default theme | ALWAYS light |
| Colors | Teal, blue-green (calming, clinical) |
| Contrast | WCAG AAA wherever possible |
| Font size | Never below 14px body |
| Alerts | Red = critical, amber = warning (never decorative) |
| Dark mode | Rarely offered |

### Entertainment / Media / Streaming

| Trait | Pattern |
|-------|---------|
| Default theme | Dark |
| Background | True black or near-black (immersion) |
| Accents | Vibrant, bold brand colors |
| Shadows | Heavy, dramatic depth |
| Imagery | Full-bleed, edge-to-edge |
| Transitions | Longer (300ms+), cinematic |

### E-commerce / Retail

| Trait | Pattern |
|-------|---------|
| Default theme | Light |
| Colors | Warm accents (orange, coral) for conversion |
| Product photos | Need accurate color (demands light background) |
| Radius | Large (12-16px) — friendly, inviting |
| Shadows | Hover elevation on product cards |
| Exception | Luxury brands use dark for exclusivity |

### Creative Tools (Figma, Adobe, Blender)

| Trait | Pattern |
|-------|---------|
| Default theme | Dark (neutral canvas for color accuracy) |
| Radius | Small (2-4px) — dense, utilitarian |
| Font size | Small (12-13px) for density |
| Transitions | Instant (100ms) |
| Accent colors | Minimal (blue=selection, red=destructive) |
| Depth | Clear panel/canvas/toolbar hierarchy |

## Minimalism Characteristics (NN/g Study of 112 Sites)

| Feature | Prevalence |
|---------|-----------|
| Flat design (no gradients/shadows) | 96% |
| Limited/monochromatic color | 95% |
| Restricted UI elements | 87% |
| Maximized negative space | 84% |
| Dramatic typography | 75% |

49% used purely monochromatic palettes. 46% used monochromatic + 1-2 accent colors.

## CSS Implementation Pattern

```css
:root {
  color-scheme: light;
  /* Semantic tokens */
  --color-surface: #ffffff;
  --color-on-surface: #1a1a1a;
  --color-primary: #0047AB;
  --color-on-primary: #ffffff;
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --color-surface: #121212;
    --color-on-surface: #e0e0e0;
    --color-primary: #809fff;
    --color-on-primary: #002966;
  }
}

/* Manual override class */
.dark {
  color-scheme: dark;
  --color-surface: #121212;
  --color-on-surface: #e0e0e0;
  --color-primary: #809fff;
  --color-on-primary: #002966;
}
```

Also set `<meta name="color-scheme" content="light dark">` in HTML head to let browser handle form controls, scrollbars, and system colors automatically.

## Available Scripts

Run from `~/.kiro/skills/frontend-design/scripts/`:

| Script | Purpose |
|--------|---------|
| `extract-theme.py --color "#hex"` | Generate full M3 light+dark CSS custom properties from brand color |
| `extract-theme.py --image logo.png` | Same but extract source color from logo |
| `contrast-check.py fg bg` | Check WCAG AA/AAA compliance between colors |
| `contrast-check.py --palette "c1,c2,c3"` | Check all pairs in a palette |
| `palette-from-image.py image.png` | Extract dominant colors + harmonies |
| `derive-dark-theme.py --file light.css` | Convert light CSS vars to dark equivalents |
| `derive-dark-theme.py --vars "hex,hex"` | Quick dark derivation of color list |
| `industry-preset.py saas` | Generate full design tokens for industry |
| `industry-preset.py finance --brand "#hex"` | Industry preset with custom brand color |

**Dependencies**: `pip install material-color-utilities Pillow colorthief wcag-contrast-ratio`

## Sources

- Nielsen Norman Group: "Dark Mode vs. Light Mode: Which Is Better?" (Budiu, 2020)
- EightShapes: "Light & Dark Color Modes in Design Systems" (Curtis, 2017)
- CSS-Tricks: "A Complete Guide to Dark Mode on the Web" (Adhuham, 2020)
- Stripe Engineering: "Designing Accessible Color Systems" (Koopersmith & Miner, 2019)
- Toptal: "The Principles of Dark UI Design" (Philips, 2024)
- Rauno.me: "What will you ship?" (Vercel design, 2023)
- web.dev: "Improve dark mode default with color-scheme" (Steiner)
- Smashing Magazine: "Using HSL Colors In CSS" (Shadeed, 2021)
- Material Design 3: Color system, tonal palettes, dark theme
- Apple Human Interface Guidelines: Dark Mode
- Tailwind CSS: Dark mode implementation patterns
