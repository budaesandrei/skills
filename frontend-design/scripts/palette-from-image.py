"""
palette-from-image.py — Extract dominant colors and generate harmonies from an image.

Usage:
    python palette-from-image.py path/to/logo.png
    python palette-from-image.py path/to/logo.png --count 8
    python palette-from-image.py path/to/logo.png --harmonies --output palette.json
"""

import argparse
import colorsys
import json
import sys
from colorthief import ColorThief
from material_color_utilities import prominent_colors_from_image
from PIL import Image


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_hsl(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    hls = colorsys.rgb_to_hls(r, g, b)
    return {"h": round(hls[0] * 360), "s": round(hls[2] * 100), "l": round(hls[1] * 100)}


def generate_harmonies(hex_color):
    """Generate color harmonies from a base color."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)

    def hsl_to_hex(h, l, s):
        r2, g2, b2 = colorsys.hls_to_rgb(h % 1.0, l, s)
        return f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"

    return {
        "complementary": [hex_color, hsl_to_hex(hue + 0.5, light, sat)],
        "analogous": [hsl_to_hex(hue - 1/12, light, sat), hex_color, hsl_to_hex(hue + 1/12, light, sat)],
        "triadic": [hex_color, hsl_to_hex(hue + 1/3, light, sat), hsl_to_hex(hue + 2/3, light, sat)],
        "split_complementary": [hex_color, hsl_to_hex(hue + 5/12, light, sat), hsl_to_hex(hue + 7/12, light, sat)],
        "tetradic": [hex_color, hsl_to_hex(hue + 0.25, light, sat), hsl_to_hex(hue + 0.5, light, sat), hsl_to_hex(hue + 0.75, light, sat)],
    }


def main():
    parser = argparse.ArgumentParser(description="Extract color palette from an image")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--count", type=int, default=5, help="Number of colors to extract (default: 5)")
    parser.add_argument("--harmonies", action="store_true", help="Generate color harmonies from dominant color")
    parser.add_argument("--output", "-o", help="Output as JSON file")
    args = parser.parse_args()

    # Extract with colorthief (quantization-based, good for logos)
    ct = ColorThief(args.image)
    dominant = rgb_to_hex(*ct.get_color(quality=1))
    palette_rgb = ct.get_palette(color_count=args.count, quality=1)
    palette = [rgb_to_hex(*c) for c in palette_rgb]

    # Also extract with M3 (perceptual, good for photos)
    img = Image.open(args.image)
    m3_colors = prominent_colors_from_image(img, args.count)
    m3_palette = list(m3_colors)  # already hex strings

    result = {
        "source": args.image,
        "dominant_color": dominant,
        "dominant_hsl": hex_to_hsl(dominant),
        "palette_quantized": palette,
        "palette_perceptual": m3_palette,
    }

    if args.harmonies:
        result["harmonies"] = generate_harmonies(dominant)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Palette written to {args.output}")
    else:
        print(f"Dominant: {dominant} (HSL: {hex_to_hsl(dominant)})")
        print(f"\nPalette (quantized): {', '.join(palette)}")
        print(f"Palette (perceptual M3): {', '.join(m3_palette)}")
        if args.harmonies:
            print(f"\nHarmonies from {dominant}:")
            for name, colors in result["harmonies"].items():
                print(f"   {name}: {', '.join(colors)}")


if __name__ == "__main__":
    main()
