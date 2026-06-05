"""
contrast-check.py — Check WCAG AA/AAA compliance between color pairs.

Usage:
    python contrast-check.py "#ffffff" "#121212"
    python contrast-check.py "#e0e0e0" "#1a1a2e" --verbose
    python contrast-check.py --palette "#0047AB,#ffffff,#121212,#e0e0e0"
"""

import argparse
import sys
import wcag_contrast_ratio as wcag


def hex_to_rgb(hex_color):
    """Convert hex to normalized RGB tuple (0-1 range)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def check_pair(fg_hex, bg_hex):
    """Check contrast between two colors, return dict of results."""
    fg = hex_to_rgb(fg_hex)
    bg = hex_to_rgb(bg_hex)
    ratio = wcag.rgb(fg, bg)

    return {
        "fg": fg_hex,
        "bg": bg_hex,
        "ratio": round(ratio, 2),
        "aa_normal": ratio >= 4.5,      # 4.5:1 for normal text
        "aa_large": ratio >= 3.0,       # 3:1 for large text (18px+ or 14px bold)
        "aaa_normal": ratio >= 7.0,     # 7:1 for enhanced
        "aaa_large": ratio >= 4.5,      # 4.5:1 for enhanced large
    }


def format_result(result, verbose=False):
    """Format a contrast check result for display."""
    lines = []
    ratio_str = f"{result['ratio']}:1"
    status = "PASS" if result["aa_normal"] else "WARN" if result["aa_large"] else "FAIL"

    lines.append(f"[{status}] {result['fg']} on {result['bg']} -> {ratio_str}")

    if verbose:
        lines.append(f"   AA normal text (>=4.5:1):  {'PASS' if result['aa_normal'] else 'FAIL'}")
        lines.append(f"   AA large text  (>=3.0:1):  {'PASS' if result['aa_large'] else 'FAIL'}")
        lines.append(f"   AAA normal text (>=7.0:1): {'PASS' if result['aaa_normal'] else 'FAIL'}")
        lines.append(f"   AAA large text  (>=4.5:1): {'PASS' if result['aaa_large'] else 'FAIL'}")

    return "\n".join(lines)


def suggest_fix(fg_hex, bg_hex, target_ratio=4.5):
    """Suggest adjusted foreground color to meet target contrast."""
    bg = hex_to_rgb(bg_hex)
    fg = hex_to_rgb(fg_hex)
    ratio = wcag.rgb(fg, bg)

    if ratio >= target_ratio:
        return None

    # Determine if we should lighten or darken
    bg_luminance = 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2]
    direction = -1 if bg_luminance < 0.5 else 1  # darken on light bg, lighten on dark bg

    # Binary search for the right adjustment
    best = fg
    for step in range(50):
        factor = 1 + (direction * step * 0.02)
        if direction == -1:
            candidate = tuple(max(0, min(1, c * (1 / factor))) for c in fg)
        else:
            candidate = tuple(max(0, min(1, c * factor)) for c in fg)
        if wcag.rgb(candidate, bg) >= target_ratio:
            best = candidate
            break
        best = candidate

    return "#{:02x}{:02x}{:02x}".format(
        int(best[0] * 255), int(best[1] * 255), int(best[2] * 255)
    )


def main():
    parser = argparse.ArgumentParser(description="Check WCAG contrast compliance")
    parser.add_argument("foreground", nargs="?", help="Foreground hex color")
    parser.add_argument("background", nargs="?", help="Background hex color")
    parser.add_argument("--palette", help="Comma-separated colors to check all pairs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed pass/fail")
    parser.add_argument("--fix", action="store_true", help="Suggest fixes for failing pairs")
    args = parser.parse_args()

    if args.palette:
        colors = [c.strip() for c in args.palette.split(",")]
        print(f"Checking all pairs from {len(colors)} colors:\n")
        failures = 0
        for i, bg in enumerate(colors):
            for j, fg in enumerate(colors):
                if i == j:
                    continue
                result = check_pair(fg, bg)
                print(format_result(result, args.verbose))
                if args.fix and not result["aa_normal"]:
                    fix = suggest_fix(fg, bg)
                    if fix:
                        print(f"   -> Suggestion: try {fix} instead of {fg}")
                failures += 0 if result["aa_normal"] else 1
        print(f"\n{'─' * 40}")
        total = len(colors) * (len(colors) - 1)
        print(f"Results: {total - failures}/{total} pairs pass AA normal text")
    elif args.foreground and args.background:
        result = check_pair(args.foreground, args.background)
        print(format_result(result, verbose=True))
        if args.fix and not result["aa_normal"]:
            fix = suggest_fix(args.foreground, args.background)
            if fix:
                print(f"\n-> Suggested fix: {fix} (ratio: {check_pair(fix, args.background)['ratio']}:1)")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
