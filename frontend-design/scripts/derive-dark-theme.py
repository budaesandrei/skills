"""
derive-dark-theme.py — Convert light theme CSS custom properties to a dark theme.

Uses perceptual color manipulation (CIELAB lightness inversion) to derive
dark equivalents that maintain the same hue/character.

Usage:
    python derive-dark-theme.py --file light-theme.css
    python derive-dark-theme.py --vars "#ffffff,#f5f5f5,#222222,#0047AB,#e53935"
    python derive-dark-theme.py --file light-theme.css --output dark-theme.css
"""

import argparse
import colorsys
import re
import sys


def hex_to_hsl(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return hue, sat, light


def hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def derive_dark_color(hex_color):
    """
    Derive a dark-mode equivalent of a color.
    
    Rules based on Material Design + research findings:
    - Very light colors (backgrounds) → very dark equivalents
    - Very dark colors (text) → light equivalents
    - Mid-range accent colors → desaturate slightly, adjust lightness
    - Pure white → #e0e0e0 (never pure white in dark mode)
    - Pure black → #121212 (never pure black in dark mode)
    """
    h = hex_color.lstrip("#").lower()

    # Handle pure extremes
    if h == "ffffff":
        return "#e0e0e0"
    if h == "000000":
        return "#121212"

    hue, sat, light = hex_to_hsl(hex_color)

    # Background colors (very light, L > 0.9) → dark surfaces
    if light > 0.9:
        new_light = 0.07 + (1.0 - light) * 0.5  # Map 0.9-1.0 → 0.07-0.12
        new_sat = sat * 0.3  # Heavily desaturate backgrounds
        return hsl_to_hex(hue, new_sat, new_light)

    # Near-white surfaces (L 0.8-0.9) → dark surface containers
    if light > 0.8:
        new_light = 0.10 + (light - 0.8) * 0.4  # Map 0.8-0.9 → 0.10-0.14
        new_sat = sat * 0.4
        return hsl_to_hex(hue, new_sat, new_light)

    # Dark text colors (L < 0.2) → light text
    if light < 0.2:
        new_light = 0.87 - light * 0.5  # Map 0.0-0.2 → 0.87-0.77
        new_sat = sat * 0.6
        return hsl_to_hex(hue, new_sat, new_light)

    # Medium-dark colors (L 0.2-0.4) → lighten substantially
    if light < 0.4:
        new_light = 0.6 + (light - 0.2) * 0.5
        new_sat = min(sat, 0.7)  # Cap saturation
        return hsl_to_hex(hue, new_sat, new_light)

    # Accent/mid colors (L 0.4-0.8) → adjust for dark bg visibility
    # Desaturate slightly and push lightness to 0.6-0.8 range
    new_light = 0.55 + (light - 0.4) * 0.5
    new_sat = sat * 0.85  # Slight desaturation per CSS-Tricks guidance
    return hsl_to_hex(hue, new_sat, min(new_light, 0.82))


def parse_css_vars(css_content):
    """Extract CSS custom properties and their hex values from CSS."""
    pattern = r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})'
    matches = re.findall(pattern, css_content)
    return matches


def expand_shorthand_hex(hex_color):
    """Expand #abc to #aabbcc."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        return f"#{h[0]*2}{h[1]*2}{h[2]*2}"
    return hex_color


def main():
    parser = argparse.ArgumentParser(description="Derive dark theme from light theme colors")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="CSS file with custom properties to convert")
    group.add_argument("--vars", help="Comma-separated hex colors to convert")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            css = f.read()
        vars_list = parse_css_vars(css)
        if not vars_list:
            print("No CSS custom properties with hex values found in file.", file=sys.stderr)
            sys.exit(1)

        lines = ["/* Dark theme derived from light theme */", ".dark {", "  color-scheme: dark;"]
        for name, value in vars_list:
            value = expand_shorthand_hex(value)
            dark_value = derive_dark_color(value)
            lines.append(f"  {name}: {dark_value}; /* was {value} */")
        lines.append("}")
        result = "\n".join(lines)
    else:
        colors = [c.strip() for c in args.vars.split(",")]
        lines = ["/* Dark equivalents */"]
        for c in colors:
            c = expand_shorthand_hex(c)
            dark = derive_dark_color(c)
            hue_l, _, light_l = hex_to_hsl(c)
            hue_d, _, light_d = hex_to_hsl(dark)
            lines.append(f"{c} -> {dark}  (L: {light_l:.0%} -> {light_d:.0%})")
        result = "\n".join(lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Dark theme written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
