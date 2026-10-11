"""Generate README GIFs (logo, wordmark, architecture, system design) via Chrome headless."""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "docs" / "brand"
DIAGRAMS = ROOT / "docs" / "diagrams"

FPS = 12
LOGO_FRAMES = 36
DIAGRAM_FRAMES = 30
HERO_FPS = 15
HERO_FRAMES = 45


def find_chrome() -> str:
    for candidate in (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ):
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")
    if not found:
        raise RuntimeError("Chrome/Chromium not found — install Chrome to generate GIFs.")
    return found


def screenshot_svg(chrome: str, svg: str, out_png: Path, width: int, height: int) -> None:
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:transparent;}}
svg{{display:block;width:{width}px;height:{height}px;}}</style></head>
<body>{svg}</body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        html_path = Path(f.name)
    try:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--window-size={width},{height}",
                f"--screenshot={out_png}",
                html_path.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        html_path.unlink(missing_ok=True)


def frames_to_gif(frame_paths: list[Path], out_gif: Path, duration_ms: int) -> None:
    images = [Image.open(p).convert("RGBA") for p in frame_paths]
    # Flatten on light cream for README consistency
    flat: list[Image.Image] = []
    bg = (255, 245, 238, 255)
    for im in images:
        canvas = Image.new("RGBA", im.size, bg)
        canvas.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
        flat.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=256))
    flat[0].save(
        out_gif,
        save_all=True,
        append_images=flat[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    for im in images:
        im.close()


def logo_svg(t: float, *, petal_opacity: float = 0.22) -> str:
    scale = 1 + 0.04 * math.sin(2 * math.pi * t / 4)
    rot = (t / 18) * 360
    pulse_phase = (math.sin(2 * math.pi * t / 2.4) + 1) / 2
    dashoffset = 42 * (1 - pulse_phase)
    opacity = 0.65 + 0.35 * pulse_phase
    petals = ""
    for angle in (0, 72, 144, 216, 288):
        petals += (
            f'<ellipse cx="60" cy="34" rx="10" ry="18" fill="#fff" '
            f'transform="rotate({angle + rot} 60 58)"/>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <defs>
    <linearGradient id="bloom-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF4D8D"/>
      <stop offset="100%" stop-color="#E3256B"/>
    </linearGradient>
    <filter id="bloom-glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g transform="translate(60 60) scale({scale}) translate(-60 -60)">
    <path fill="url(#bloom-bg)" d="M60 8c14 0 24 8 30 18 10-2 22 2 28 14 6 12 2 26-6 36 4 12 0 26-10 34-10 8-24 8-36 2-10 8-24 10-36 2-12-8-16-22-12-34-8-10-12-24-6-36 6-12 18-16 28-14C36 16 46 8 60 8z"/>
  </g>
  <g opacity="{petal_opacity}" transform="rotate({rot} 60 58)">{petals}</g>
  <g filter="url(#bloom-glow)">
    <path fill="#fff" d="M60 38c-8 0-14 6-14 14 0 10 14 22 14 22s14-12 14-22c0-8-6-14-14-14z"/>
    <path fill="none" stroke="#E3256B" stroke-width="2.2" stroke-linecap="round"
      stroke-dasharray="42" stroke-dashoffset="{dashoffset:.2f}" opacity="{opacity:.3f}"
      d="M44 58h6l3-8 4 16 4-10 3 6h12"/>
  </g>
</svg>"""


def wordmark_svg(t: float) -> str:
    scale = 1 + 0.03 * math.sin(2 * math.pi * t / 4)
    rot = (t / 18) * 360
    pulse_phase = (math.sin(2 * math.pi * t / 2.4) + 1) / 2
    dashoffset = 21 * (1 - pulse_phase)
    opacity = 0.75 + 0.25 * pulse_phase
    petals = ""
    for angle in (0, 72, 144, 216, 288):
        petals += (
            f'<ellipse cx="60" cy="34" rx="10" ry="18" fill="#fff" '
            f'transform="rotate({angle + rot} 60 58)"/>'
        )
    inner = f"""
  <g transform="translate(8 8) scale(0.5)">
    <g transform="translate(60 60) scale({scale}) translate(-60 -60)">
      <path fill="url(#wm-bg)" d="M60 8c14 0 24 8 30 18 10-2 22 2 28 14 6 12 2 26-6 36 4 12 0 26-10 34-10 8-24 8-36 2-10 8-24 10-36 2-12-8-16-22-12-34-8-10-12-24-6-36 6-12 18-16 28-14C36 16 46 8 60 8z"/>
    </g>
    <g opacity="0.22" transform="rotate({rot} 60 58)">{petals}</g>
    <path fill="#fff" d="M60 38c-8 0-14 6-14 14 0 10 14 22 14 22s14-12 14-22c0-8-6-14-14-14z"/>
    <path fill="none" stroke="#E3256B" stroke-width="2.2" stroke-linecap="round"
      stroke-dasharray="21" stroke-dashoffset="{dashoffset:.2f}" opacity="{opacity:.3f}"
      d="M44 58h6l3-8 4 16 4-10 3 6h12"/>
  </g>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="280" height="76" viewBox="0 0 280 76">
  <rect width="280" height="76" rx="12" fill="#FFF5EE"/>
  <defs>
    <linearGradient id="wm-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF4D8D"/>
      <stop offset="100%" stop-color="#E3256B"/>
    </linearGradient>
  </defs>
  {inner}
  <text x="78" y="40" font-family="Georgia, 'Times New Roman', serif" font-size="24" font-weight="700" fill="#1A1F12">Bloom</text>
  <text x="78" y="58" font-family="Segoe UI, system-ui, sans-serif" font-size="9" font-weight="600" fill="#6B7355" letter-spacing="2.2">ORGANIC CARE</text>
</svg>"""


def architecture_svg(frame: int) -> str:
    base = (DIAGRAMS / "architecture.svg").read_text(encoding="utf-8")
    offset = (frame * 6) % 40
    # Animated flow along top connectors
    animated_path = (
        f'<path d="M180 116h40M360 116h40M540 116h40M740 116h40" '
        f'stroke="#E3256B" stroke-width="3" stroke-dasharray="10 8" stroke-dashoffset="{offset}" '
        f'fill="none" marker-end="url(#arr)"/>'
    )
    base = base.replace(
        '<path d="M180 116h40M360 116h40M540 116h40M740 116h40" stroke="#E3256B" stroke-width="2" marker-end="url(#arr)"/>',
        animated_path,
    )
    voff = (frame * 4) % 20
    base = base.replace(
        'stroke-dasharray="6 4"',
        f'stroke-dasharray="6 4" stroke-dashoffset="{voff}"',
        1,
    )
    base = base.replace(
        'fill="#fff" stroke="#FF9900" stroke-width="2"/>\n <text x="660" y="115"',
        f'fill="#FFF8F0" stroke="#FF9900" stroke-width="3"/>\n <text x="660" y="115"',
        1,
    )
    return base


def system_design_svg(frame: int) -> str:
    base = (DIAGRAMS / "system-design.svg").read_text(encoding="utf-8")
    highlight = frame % 6
    boxes = [
        (40, 290, 120, 44),
        (180, 290, 120, 44),
        (320, 290, 120, 44),
        (460, 290, 120, 44),
        (600, 290, 120, 44),
        (740, 290, 120, 44),
    ]
    for i, (x, y, w, h) in enumerate(boxes):
        old = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#FFE4E1"/>'
        if i == highlight:
            new = (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                f'fill="#FFD0E8" stroke="#E3256B" stroke-width="2.5"/>'
            )
        else:
            new = old
        base = base.replace(old, new, 1)
    step = (frame // 6) % 3
    steps = [
        (340, 150, 280, 48),
        (340, 218, 280, 48),
        (300, 362, 360, 48),
    ]
    for i, (x, y, w, h) in enumerate(steps):
        if i != step:
            continue
        if i == 2:
            old = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#4A5D23"/>'
            new = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#5A7229" stroke="#E3256B" stroke-width="2"/>'
        else:
            old = (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" '
                f'fill="#fff" stroke="#4A5D23" stroke-opacity=".35"/>'
            )
            new = (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" '
                f'fill="#FFF0EC" stroke="#E3256B" stroke-width="2"/>'
            )
        base = base.replace(old, new, 1)
    return base


def _font(candidates: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    search_roots = (
        Path(r"C:\Windows\Fonts"),
        Path("/usr/share/fonts/truetype/msttcorefonts"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/System/Library/Fonts/Supplemental"),
    )
    for root in search_roots:
        for fname in candidates:
            path = root / fname
            if path.is_file():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def generate_hero_pngs() -> None:
    """Static PNGs for PaperLoom-style README hero (GitHub-safe typography)."""
    BRAND.mkdir(parents=True, exist_ok=True)
    title_font = _font(("georgiab.ttf", "Georgia Bold.ttf", "DejaVuSerif-Bold.ttf"), 58)
    tag_font = _font(("segoeui.ttf", "Segoe UI.ttf", "DejaVuSans.ttf"), 11)
    sub_font = _font(("segoeui.ttf", "Segoe UI.ttf", "DejaVuSans.ttf"), 15)
    lead_bold = _font(("seguisb.ttf", "Segoe UI Semibold.ttf", "DejaVuSans-Bold.ttf"), 17)
    body_font = _font(("segoeui.ttf", "Segoe UI.ttf", "DejaVuSans.ttf"), 14)

    # Serif wordmark title (cream card)
    t_img = Image.new("RGBA", (260, 72), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(t_img)
    t_draw.text((0, 2), "Bloom", font=title_font, fill="#1A1F12")
    t_img.save(BRAND / "bloom-serif-title.png")

    # Coral accent dash
    bar = Image.new("RGBA", (44, 4), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle((0, 0, 44, 3), fill="#E3256B")
    bar.save(BRAND / "accent-bar.png")

    # Caps tagline (gray-green)
    tag_text = "LISTEN FIRST · CITE ALWAYS · CARE NEARBY"
    tag_w = int(tag_font.getlength(tag_text)) + 4
    tag_img = Image.new("RGBA", (tag_w, 22), (0, 0, 0, 0))
    ImageDraw.Draw(tag_img).text((0, 0), tag_text, font=tag_font, fill="#6B7355")
    tag_img.save(BRAND / "bloom-hero-tagline.png")

    # Card subtitle
    sub = "Every answer traced to sources and nearby care."
    sub_w = int(sub_font.getlength(sub)) + 4
    sub_img = Image.new("RGBA", (sub_w, 26), (0, 0, 0, 0))
    ImageDraw.Draw(sub_img).text((0, 0), sub, font=sub_font, fill="#4A5D23")
    sub_img.save(BRAND / "bloom-hero-subtitle.png")

    # Dark-band lead (white text, transparent bg)
    lead1 = "Ask anything health-related. Get cited guidance with India meds, maps, and labs."
    lead2 = "Bloom is an India-first companion on web and Telegram — LangGraph safety, RAG, and voice."
    w = max(int(lead_bold.getlength(lead1)), int(body_font.getlength(lead2))) + 8
    lead_img = Image.new("RGBA", (w, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(lead_img)
    d.text((0, 0), lead1, font=lead_bold, fill="#F4F4F5")
    d.text((0, 36), lead2, font=body_font, fill="#D4D4D8")
    lead_img.save(BRAND / "readme-hero-lead.png")
    print("Wrote README hero PNGs under docs/brand/")


def _compose_readme_hero_frame(logo: Image.Image, t: float) -> Image.Image:
    """Dark banner + cream card; logo left, Bloom wordmark right (layout inspired by premium README heroes)."""
    w, h = 780, 196
    dark = (18, 16, 24)
    cream = (255, 245, 238)
    canvas = Image.new("RGB", (w, h), dark)
    draw = ImageDraw.Draw(canvas)

    cx1, cy1, cx2, cy2 = 36, 32, w - 36, h - 32
    draw.rounded_rectangle((cx1, cy1, cx2, cy2), radius=20, fill=cream, outline=(74, 68, 88), width=1)

    title_font = _font(("georgiab.ttf", "Georgia Bold.ttf", "DejaVuSerif-Bold.ttf"), 56)
    organic_font = _font(("segoeui.ttf", "Segoe UI.ttf", "DejaVuSans.ttf"), 10)
    tag_font = _font(("segoeuisl.ttf", "Segoe UI Italic.ttf", "DejaVuSans-Oblique.ttf"), 15)
    sub_font = _font(("segoeui.ttf", "Segoe UI.ttf", "DejaVuSans.ttf"), 14)

    lx, ly, tile = 56, 48, 108
    draw.rounded_rectangle(
        (lx, ly, lx + tile, ly + tile),
        radius=18,
        fill=(255, 236, 243),
        outline=(227, 37, 107),
        width=2,
    )
    draw.ellipse((lx + tile - 18, ly + 10, lx + tile - 6, ly + 22), fill=(255, 77, 141))

    canvas.paste(logo, (lx + 10, ly + 10), logo)

    tx = lx + tile + 28
    ty = 52
    draw.text((tx, ty), "Bloom", font=title_font, fill=(26, 31, 18))
    draw.text((tx, ty + 58), "ORGANIC CARE", font=organic_font, fill=(107, 115, 85))

    pulse = (math.sin(2 * math.pi * t / 2.4) + 1) / 2
    bar_w = int(28 + 36 * pulse)
    draw.rectangle((tx, ty + 78, tx + bar_w, ty + 82), fill=(227, 37, 107))

    draw.text((tx, ty + 92), "Listen first. Cite always. Care nearby.", font=tag_font, fill=(74, 93, 35))
    draw.text(
        (tx, ty + 114),
        "India-first health companion — web, Telegram, cited RAG.",
        font=sub_font,
        fill=(90, 98, 72),
    )
    return canvas


def generate_readme_hero_gif(chrome: str) -> None:
    """README header GIF: full dark band, animated Bloom mark + name + taglines."""
    duration_ms = int(1000 / HERO_FPS)
    logo_px = 176
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        palette_frames: list[Image.Image] = []
        for i in range(HERO_FRAMES):
            t = i / HERO_FPS
            logo_png = tmp_path / f"logo_{i:03d}.png"
            screenshot_svg(chrome, logo_svg(t, petal_opacity=0.34), logo_png, logo_px, logo_px)
            logo = Image.open(logo_png).convert("RGBA").resize((88, 88), Image.Resampling.LANCZOS)

            frame = _compose_readme_hero_frame(logo, t)
            logo.close()
            frame_path = tmp_path / f"hero_{i:03d}.png"
            frame.save(frame_path)
            palette_frames.append(
                Image.open(frame_path).convert("P", palette=Image.ADAPTIVE, colors=256)
            )

        out = BRAND / "readme-hero.gif"
        palette_frames[0].save(
            out,
            save_all=True,
            append_images=palette_frames[1:],
            duration=duration_ms,
            loop=0,
            optimize=True,
        )
        for im in palette_frames:
            im.close()
    print(f"Wrote {out} ({HERO_FRAMES} frames @ {HERO_FPS} fps)")


def render_gif(
    chrome: str,
    name: str,
    svg_fn,
    out_gif: Path,
    width: int,
    height: int,
    n_frames: int,
) -> None:
    duration_ms = int(1000 / FPS)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        frames: list[Path] = []
        for i in range(n_frames):
            t = i / FPS
            svg = svg_fn(t) if name in ("logo", "wordmark") else svg_fn(i)
            png = tmp_path / f"{name}_{i:03d}.png"
            screenshot_svg(chrome, svg, png, width, height)
            frames.append(png)
        frames_to_gif(frames, out_gif, duration_ms)
    print(f"Wrote {out_gif} ({n_frames} frames)")


def main() -> None:
    generate_hero_pngs()
    chrome = find_chrome()
    generate_readme_hero_gif(chrome)
    render_gif(chrome, "logo", logo_svg, BRAND / "bloom-logo.gif", 120, 120, LOGO_FRAMES)
    render_gif(chrome, "wordmark", wordmark_svg, BRAND / "bloom-wordmark.gif", 280, 76, LOGO_FRAMES)
    render_gif(
        chrome,
        "architecture",
        architecture_svg,
        DIAGRAMS / "architecture.gif",
        960,
        420,
        DIAGRAM_FRAMES,
    )
    render_gif(
        chrome,
        "system_design",
        system_design_svg,
        DIAGRAMS / "system-design.gif",
        960,
        480,
        DIAGRAM_FRAMES,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--hero-only":
        generate_hero_pngs()
    elif len(sys.argv) > 1 and sys.argv[1] == "--hero-gif-only":
        generate_hero_pngs()
        generate_readme_hero_gif(find_chrome())
    else:
        main()
