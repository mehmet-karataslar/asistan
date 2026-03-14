from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def make_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Background rounded square
    margin = int(size * 0.08)
    radius = int(size * 0.2)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(14, 45, 73, 255),
    )

    # Subtle glow orb
    orb = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    orb_draw = ImageDraw.Draw(orb)
    orb_draw.ellipse(
        [int(size * 0.28), int(size * 0.18), int(size * 0.78), int(size * 0.68)],
        fill=(41, 176, 255, 180),
    )
    orb = orb.filter(ImageFilter.GaussianBlur(radius=int(size * 0.04)))
    image.alpha_composite(orb)

    # Stylized microphone body
    mic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    md = ImageDraw.Draw(mic)
    md.rounded_rectangle(
        [int(size * 0.39), int(size * 0.2), int(size * 0.61), int(size * 0.58)],
        radius=int(size * 0.12),
        fill=(236, 249, 255, 255),
    )
    md.rounded_rectangle(
        [int(size * 0.43), int(size * 0.66), int(size * 0.57), int(size * 0.72)],
        radius=int(size * 0.02),
        fill=(236, 249, 255, 255),
    )
    md.rectangle(
        [int(size * 0.487), int(size * 0.58), int(size * 0.513), int(size * 0.68)],
        fill=(236, 249, 255, 255),
    )
    md.arc(
        [int(size * 0.3), int(size * 0.46), int(size * 0.7), int(size * 0.84)],
        start=25,
        end=155,
        fill=(236, 249, 255, 255),
        width=max(3, int(size * 0.03)),
    )

    image.alpha_composite(mic)

    # Accent pulse lines
    pulse = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pulse)
    stroke = max(2, int(size * 0.022))
    pd.arc(
        [int(size * 0.17), int(size * 0.28), int(size * 0.45), int(size * 0.62)],
        start=285,
        end=75,
        fill=(96, 221, 255, 240),
        width=stroke,
    )
    pd.arc(
        [int(size * 0.55), int(size * 0.28), int(size * 0.83), int(size * 0.62)],
        start=105,
        end=255,
        fill=(96, 221, 255, 240),
        width=stroke,
    )
    image.alpha_composite(pulse)

    return image


def make_svg(path: Path) -> None:
    svg = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"512\" height=\"512\" viewBox=\"0 0 512 512\">
  <defs>
    <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
      <stop offset=\"0%\" stop-color=\"#0E2D49\"/>
      <stop offset=\"100%\" stop-color=\"#133E63\"/>
    </linearGradient>
    <radialGradient id=\"orb\" cx=\"63%\" cy=\"35%\" r=\"45%\">
      <stop offset=\"0%\" stop-color=\"#52D7FF\" stop-opacity=\"0.85\"/>
      <stop offset=\"100%\" stop-color=\"#52D7FF\" stop-opacity=\"0\"/>
    </radialGradient>
  </defs>
  <rect x=\"40\" y=\"40\" width=\"432\" height=\"432\" rx=\"88\" fill=\"url(#bg)\"/>
  <circle cx=\"322\" cy=\"194\" r=\"138\" fill=\"url(#orb)\"/>
  <rect x=\"199\" y=\"106\" width=\"114\" height=\"194\" rx=\"56\" fill=\"#ECF9FF\"/>
  <rect x=\"220\" y=\"338\" width=\"72\" height=\"30\" rx=\"10\" fill=\"#ECF9FF\"/>
  <rect x=\"248\" y=\"296\" width=\"16\" height=\"48\" fill=\"#ECF9FF\"/>
  <path d=\"M164 251c0 60 42 109 92 109s92-49 92-109\" fill=\"none\" stroke=\"#ECF9FF\" stroke-width=\"16\" stroke-linecap=\"round\"/>
  <path d=\"M110 206a76 76 0 0 1 42-62\" fill=\"none\" stroke=\"#60DDFF\" stroke-width=\"12\" stroke-linecap=\"round\"/>
  <path d=\"M402 206a76 76 0 0 0-42-62\" fill=\"none\" stroke=\"#60DDFF\" stroke-width=\"12\" stroke-linecap=\"round\"/>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    icon_dir = project_root / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)

    base = make_icon(size=1024)
    (icon_dir / "asistan-icon.png").write_bytes(base.tobytes())

    # Re-open from in-memory image to save with proper encoder metadata.
    base.save(icon_dir / "asistan-icon.png", format="PNG")
    base.resize((256, 256), Image.Resampling.LANCZOS).save(icon_dir / "asistan-icon-256.png", format="PNG")

    base.save(
        icon_dir / "asistan-icon.ico",
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )

    make_svg(icon_dir / "asistan-icon.svg")


if __name__ == "__main__":
    main()
