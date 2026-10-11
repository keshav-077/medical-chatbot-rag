"""Generate README GIFs (logo, wordmark, architecture, system design) via Chrome headless."""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "docs" / "brand"
DIAGRAMS = ROOT / "docs" / "diagrams"

FPS = 12
LOGO_FRAMES = 36
DIAGRAM_FRAMES = 30


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


def logo_svg(t: float) -> str:
    scale = 1 + 0.03 * math.sin(2 * math.pi * t / 4)
    rot = (t / 18) * 360
    pulse_phase = (math.sin(2 * math.pi * t / 2.4) + 1) / 2
    dashoffset = 42 * (1 - pulse_phase)
    opacity = 0.75 + 0.25 * pulse_phase
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
  <g opacity="0.22" transform="rotate({rot} 60 58)">{petals}</g>
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
  <text x="78" y="40" font-family="Quicksand,Segoe UI,sans-serif" font-size="22" font-weight="700" fill="#4A5D23">bloom</text>
  <text x="78" y="58" font-family="Quicksand,Segoe UI,sans-serif" font-size="10" font-weight="600" fill="#4A5D23" fill-opacity="0.62" letter-spacing="2.5">ORGANIC CARE</text>
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
    chrome = find_chrome()
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
    main()
