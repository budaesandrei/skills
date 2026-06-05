"""
industry-preset.py — Generate starter palettes and design tokens by industry/product type.

Usage:
    python industry-preset.py saas
    python industry-preset.py finance --brand "#0047AB"
    python industry-preset.py healthcare --output tokens.json
    python industry-preset.py --list
"""

import argparse
import json
import sys
from material_color_utilities import Variant, theme_from_color

PRESETS = {
    "saas": {
        "description": "Modern SaaS / Developer Tools (Linear, Vercel, Notion style)",
        "default_theme": "dark",
        "default_brand": "#6366f1",
        "variant": "TONAL_SPOT",
        "design_tokens": {
            "border_radius": "12px",
            "border_radius_sm": "8px",
            "border_radius_lg": "16px",
            "shadow": "none",
            "border": "1px solid rgba(255, 255, 255, 0.08)",
            "border_light": "1px solid rgba(0, 0, 0, 0.06)",
            "backdrop_blur": "12px",
            "font_body": "'Inter', -apple-system, sans-serif",
            "font_display": "'Geist', 'Inter', sans-serif",
            "font_mono": "'Geist Mono', 'JetBrains Mono', monospace",
            "spacing_unit": "4px",
            "transition": "150ms ease",
        },
        "notes": [
            "Dark-first design, offer light/system/dark toggle",
            "Depth via layered surfaces + subtle borders, NOT shadows",
            "Maximum restraint: 1-2 accent colors, rest neutrals",
            "Large border-radius, generous padding",
            "Subtle backdrop-filter blur for overlays",
        ],
    },
    "finance": {
        "description": "Finance / Fintech (Banking, Trading, Analytics)",
        "default_theme": "light",
        "default_brand": "#1e40af",
        "variant": "NEUTRAL",
        "design_tokens": {
            "border_radius": "8px",
            "border_radius_sm": "4px",
            "border_radius_lg": "12px",
            "shadow": "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
            "shadow_lg": "0 4px 12px rgba(0,0,0,0.1)",
            "border": "1px solid #e2e8f0",
            "font_body": "'IBM Plex Sans', -apple-system, sans-serif",
            "font_display": "'IBM Plex Sans', sans-serif",
            "font_mono": "'IBM Plex Mono', monospace",
            "spacing_unit": "4px",
            "transition": "200ms ease",
            "color_positive": "#059669",
            "color_negative": "#dc2626",
            "color_warning": "#d97706",
        },
        "notes": [
            "Light default for data clarity and trust",
            "Blue dominates: trust, stability, professionalism",
            "Semantic colors critical: green=gain, red=loss, amber=caution",
            "Shadows used for card elevation (data density needs separation)",
            "Conservative radius — approachable but not playful",
            "Offer dark mode for trading/dashboard contexts",
        ],
    },
    "healthcare": {
        "description": "Healthcare / Medical / Wellness",
        "default_theme": "light",
        "default_brand": "#0d9488",
        "variant": "NEUTRAL",
        "design_tokens": {
            "border_radius": "8px",
            "border_radius_sm": "6px",
            "border_radius_lg": "12px",
            "shadow": "0 1px 3px rgba(0,0,0,0.06)",
            "border": "1px solid #e0f2f1",
            "font_body": "'Source Sans 3', -apple-system, sans-serif",
            "font_display": "'Source Sans 3', sans-serif",
            "font_mono": "'Source Code Pro', monospace",
            "spacing_unit": "4px",
            "transition": "200ms ease",
            "color_critical": "#dc2626",
            "color_warning": "#f59e0b",
            "color_success": "#10b981",
            "color_info": "#0ea5e9",
        },
        "notes": [
            "ALWAYS light default — clarity is life-critical",
            "Teal/blue-green: calming, clinical, trustworthy",
            "High contrast mandatory (WCAG AAA where possible)",
            "Generous text sizing, never below 14px body",
            "Alert colors must be unambiguous (red=critical, never decorative)",
            "Dark mode rarely offered; if so, muted and tested extensively",
        ],
    },
    "media": {
        "description": "Entertainment / Media / Streaming",
        "default_theme": "dark",
        "default_brand": "#8b5cf6",
        "variant": "VIBRANT",
        "design_tokens": {
            "border_radius": "8px",
            "border_radius_sm": "4px",
            "border_radius_lg": "16px",
            "shadow": "0 8px 32px rgba(0,0,0,0.4)",
            "shadow_glow": "0 0 20px rgba(139, 92, 246, 0.3)",
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "font_body": "'Plus Jakarta Sans', -apple-system, sans-serif",
            "font_display": "'Plus Jakarta Sans', sans-serif",
            "font_mono": "monospace",
            "spacing_unit": "4px",
            "transition": "300ms cubic-bezier(0.4, 0, 0.2, 1)",
            "gradient_primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        },
        "notes": [
            "Dark default — content immersion, cinematic feel",
            "Vibrant accent colors, bold brand presence",
            "Heavy shadows for dramatic depth",
            "Full-bleed imagery, edge-to-edge media",
            "Longer transitions for cinematic feel",
            "Glow effects on interactive elements",
        ],
    },
    "ecommerce": {
        "description": "E-commerce / Retail / Marketplace",
        "default_theme": "light",
        "default_brand": "#ea580c",
        "variant": "TONAL_SPOT",
        "design_tokens": {
            "border_radius": "12px",
            "border_radius_sm": "8px",
            "border_radius_lg": "16px",
            "shadow": "0 2px 8px rgba(0,0,0,0.06)",
            "shadow_hover": "0 8px 24px rgba(0,0,0,0.12)",
            "border": "1px solid #f1f5f9",
            "font_body": "'DM Sans', -apple-system, sans-serif",
            "font_display": "'DM Sans', sans-serif",
            "font_mono": "monospace",
            "spacing_unit": "4px",
            "transition": "200ms ease",
            "color_sale": "#dc2626",
            "color_success": "#16a34a",
            "color_cta": "#ea580c",
        },
        "notes": [
            "Light default — product photography needs accurate color",
            "Warm accents (orange, coral) for conversion psychology",
            "Large radius — friendly, inviting, approachable",
            "Hover shadows for product card elevation",
            "CTA colors warm and high-contrast",
            "Dark mode: luxury brands only (exception pattern)",
        ],
    },
    "creative": {
        "description": "Creative Tools / Design / Photo/Video Editing",
        "default_theme": "dark",
        "default_brand": "#2563eb",
        "variant": "NEUTRAL",
        "design_tokens": {
            "border_radius": "4px",
            "border_radius_sm": "2px",
            "border_radius_lg": "8px",
            "shadow": "0 1px 2px rgba(0,0,0,0.3)",
            "border": "1px solid rgba(255, 255, 255, 0.12)",
            "font_body": "'SF Pro Text', -apple-system, sans-serif",
            "font_display": "'SF Pro Display', -apple-system, sans-serif",
            "font_mono": "'SF Mono', 'Menlo', monospace",
            "font_size_base": "12px",
            "spacing_unit": "4px",
            "transition": "100ms ease",
            "panel_bg": "#1e1e1e",
            "canvas_bg": "#2d2d2d",
        },
        "notes": [
            "Dark default — neutral canvas for color-accurate work",
            "Minimal accent colors (blue for selection, red for destructive)",
            "Small radius — dense, utilitarian, tool-like",
            "Small base font (12-13px) for information density",
            "Fast transitions — tools should feel instant",
            "Clear panel/canvas/toolbar hierarchy via surface shading",
        ],
    },
}

VARIANT_MAP = {
    "TONAL_SPOT": Variant.TONALSPOT,
    "NEUTRAL": Variant.NEUTRAL,
    "VIBRANT": Variant.VIBRANT,
    "EXPRESSIVE": Variant.EXPRESSIVE,
    "FIDELITY": Variant.FIDELITY,
    "CONTENT": Variant.CONTENT,
    "MONOCHROME": Variant.MONOCHROME,
}


def generate_preset(industry, brand_override=None):
    """Generate a full preset with M3 colors."""
    preset = PRESETS[industry]
    brand = brand_override or preset["default_brand"]
    variant = VARIANT_MAP[preset["variant"]]

    theme = theme_from_color(brand, 0, variant)
    light = theme.schemes.light
    dark = theme.schemes.dark

    return {
        "industry": industry,
        "description": preset["description"],
        "brand_color": brand,
        "default_theme": preset["default_theme"],
        "design_tokens": preset["design_tokens"],
        "colors": {
            "light": {
                "primary": light.primary,
                "on_primary": light.on_primary,
                "secondary": light.secondary,
                "surface": light.surface,
                "on_surface": light.on_surface,
                "surface_container": light.surface_container,
                "outline": light.outline,
                "error": light.error,
            },
            "dark": {
                "primary": dark.primary,
                "on_primary": dark.on_primary,
                "secondary": dark.secondary,
                "surface": dark.surface,
                "on_surface": dark.on_surface,
                "surface_container": dark.surface_container,
                "outline": dark.outline,
                "error": dark.error,
            },
        },
        "notes": preset["notes"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate industry-specific design presets")
    parser.add_argument("industry", nargs="?", choices=list(PRESETS.keys()),
                        help="Industry type")
    parser.add_argument("--brand", help="Override brand color (hex)")
    parser.add_argument("--list", action="store_true", help="List available presets")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    if args.list or not args.industry:
        print("Available industry presets:\n")
        for key, preset in PRESETS.items():
            print(f"  {key:12s}  {preset['description']}")
            print(f"  {'':12s}  Default: {preset['default_theme']} theme | Brand: {preset['default_brand']}")
            print()
        return

    result = generate_preset(args.industry, args.brand)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Preset written to {args.output}")
    else:
        print(f"[{result['industry'].upper()}] {result['description']}")
        print(f"Brand: {result['brand_color']} | Default: {result['default_theme']} theme")
        print(f"\nDesign Tokens:")
        for k, v in result["design_tokens"].items():
            print(f"   {k}: {v}")
        print(f"\nLight Colors:")
        for k, v in result["colors"]["light"].items():
            print(f"   {k}: {v}")
        print(f"\nDark Colors:")
        for k, v in result["colors"]["dark"].items():
            print(f"   {k}: {v}")
        print(f"\nNotes:")
        for note in result["notes"]:
            print(f"   - {note}")


if __name__ == "__main__":
    main()
