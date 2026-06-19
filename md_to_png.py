#!/usr/bin/env python3
"""
md-to-png: Render a markdown file to a high-resolution PNG image.

Zero pip dependencies — uses only Python stdlib + Playwright's bundled
Chromium (already installed in this environment).

Usage:
    python3 md_to_png.py input.md [--output out.png] [--width 1200] [--scale 2]

Pipeline:  md ──builtin regex──→ HTML ──Playwright Chromium──→ PNG
"""

import argparse
import os
import re
import sys

# ── Minimal markdown → HTML (stdlib only) ──────────────────────────────────

_RE_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_RE_HR = re.compile(r"^---+\s*$", re.MULTILINE)
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_CODE_INLINE = re.compile(r"`([^`]+)`")
_RE_LIST = re.compile(r"^(\s*)[-*]\s+(.+)$", re.MULTILINE)


def _minimal_md_to_html(md: str) -> str:
    """Convert markdown to HTML using only stdlib regex.

    Supports: headings (#), tables (|), bold (**), inline code (`),
    fenced code blocks (```), unordered lists (-), horizontal rules (---).
    """
    lines = md.split("\n")
    out = []
    in_table = in_code = in_ul = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # fenced code
        if line.lstrip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                lang = line.lstrip()[3:].strip()
                cls = f' class="language-{lang}"' if lang else ""
                out.append(f"<pre><code{cls}>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            i += 1
            continue

        if not line.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            out.append("")
            i += 1
            continue

        m = _RE_HEADING.match(line)
        if m:
            out.append(f"<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>")
            i += 1
            continue

        if _RE_HR.match(line.strip()):
            out.append("<hr>")
            i += 1
            continue

        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                i += 1
                continue
            if not in_table:
                out.append("<table><thead><tr>")
                for c in cells:
                    c = _RE_BOLD.sub(r"<strong>\1</strong>", c)
                    c = _RE_CODE_INLINE.sub(r"<code>\1</code>", c)
                    out.append(f"<th>{c}</th>")
                out.append("</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>")
                for c in cells:
                    c = _RE_BOLD.sub(r"<strong>\1</strong>", c)
                    c = _RE_CODE_INLINE.sub(r"<code>\1</code>", c)
                    out.append(f"<td>{c}</td>")
                out.append("</tr>")
            i += 1
            continue
        else:
            if in_table:
                out.append("</tbody></table>")
                in_table = False

        m = _RE_LIST.match(line)
        if m:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            text = _RE_BOLD.sub(r"<strong>\1</strong>", m.group(2))
            text = _RE_CODE_INLINE.sub(r"<code>\1</code>", text)
            out.append(f"<li>{text}</li>")
            i += 1
            continue
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False

        text = _RE_BOLD.sub(r"<strong>\1</strong>", line)
        text = _RE_CODE_INLINE.sub(r"<code>\1</code>", text)
        out.append(f"<p>{text}</p>")
        i += 1

    if in_table:
        out.append("</tbody></table>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


# ── HTML template ────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #1a1a1a;
    margin: 0;
    padding: {pad_y}px {pad_x}px;
    background: #fff;
    max-width: {content_width}px;
}}
h1 {{
    font-size: 2em;
    font-weight: 700;
    color: #111;
    border-bottom: 3px solid #e0e0e0;
    padding-bottom: 12px;
    margin: 0 0 24px 0;
}}
h2 {{
    font-size: 1.4em;
    font-weight: 600;
    color: #1a73e8;
    margin: 36px 0 14px 0;
    border-bottom: 1px solid #e8e8e8;
    padding-bottom: 6px;
}}
h3 {{
    font-size: 1.1em;
    font-weight: 600;
    color: #333;
    margin: 24px 0 8px 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0 28px 0;
    font-size: 0.88em;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
th {{
    background: #1a73e8;
    color: #fff;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
}}
td {{
    padding: 8px 12px;
    border-bottom: 1px solid #e8e8e8;
}}
tr:nth-child(even) {{ background: #f8f9fa; }}
hr {{
    border: none;
    border-top: 2px solid #e0e0e0;
    margin: 32px 0;
}}
strong {{ font-weight: 600; color: #111; }}
ul, ol {{ padding-left: 24px; }}
li {{ margin-bottom: 5px; }}
p {{ margin: 0 0 8px 0; }}
pre {{
    background: #f4f4f4;
    padding: 14px 18px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.85em;
}}
code {{
    background: #f0f0f0;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 0.85em;
}}
pre code {{ background: none; padding: 0; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

PAGE_PADDING_X = 56
PAGE_PADDING_Y = 48
DEFAULT_WIDTH = 1200
DEFAULT_SCALE = 2  # 2x for retina


def _png_dimensions(path: str) -> tuple[int, int]:
    """Read width and height from a PNG file header (stdlib only)."""
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{path} is not a valid PNG file")
        f.read(4)  # IHDR chunk length
        f.read(4)  # IHDR chunk type
        width = int.from_bytes(f.read(4), "big")
        height = int.from_bytes(f.read(4), "big")
    return width, height


def render_html_to_png(
    html: str, png_path: str, width: int, scale: int
) -> tuple[int, int]:
    """Render HTML to PNG via Playwright Chromium."""
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 800},
                device_scale_factor=scale,
            )
            page.set_content(html, wait_until="load")
            height = page.evaluate("document.body.scrollHeight")
            page.set_viewport_size({"width": width, "height": height + 60})
            page.screenshot(path=png_path, full_page=True)
            browser.close()
    except Exception as exc:
        raise RuntimeError(
            f"Rendering failed: {exc}\n"
            "Is Chromium installed? Run: playwright install chromium"
        ) from exc

    return _png_dimensions(png_path)


def main():
    parser = argparse.ArgumentParser(
        description="Render markdown to PNG via Playwright"
    )
    parser.add_argument("input", help="Path to input .md file")
    parser.add_argument("--output", "-o", default=None, help="Output PNG path")
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Page width (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=DEFAULT_SCALE,
        help=f"Scale factor for retina (default: {DEFAULT_SCALE})",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    png_path = args.output or os.path.splitext(args.input)[0] + ".png"

    with open(args.input, encoding="utf-8") as f:
        md = f.read()

    body = _minimal_md_to_html(md)
    content_width = args.width - 2 * PAGE_PADDING_X
    html = HTML_TEMPLATE.format(
        body=body,
        pad_x=PAGE_PADDING_X,
        pad_y=PAGE_PADDING_Y,
        content_width=content_width,
    )

    w, h = render_html_to_png(html, png_path, args.width, args.scale)
    size = os.path.getsize(png_path)
    print(f"✓ {png_path}  ({w}×{h} px, {size:,} bytes)")


if __name__ == "__main__":
    main()
