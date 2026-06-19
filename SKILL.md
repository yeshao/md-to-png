# md-to-png — Render Markdown to a shareable PNG

Turn any `.md` file into a **retina-quality PNG** that can be dropped into
Slack, email, or chat — no markdown renderer needed on the recipient's side.

## When to use

- Sharing formatted reports / comparisons / analysis with non-technical folks
- Slack / email / chat previews that don't render markdown
- Archiving a snapshot of a document as an image

## Dependencies

**Zero pip packages.** Uses Playwright's bundled Chromium (pre-installed in
this environment) and Python stdlib only.

```bash
# That's it — no pip install needed.
```

If Playwright is not installed on your system:
```bash
pip install playwright
playwright install chromium
```

## Usage

```bash
# Basic — outputs <input>.png beside the .md file
python3 md_to_png.py input.md

# Retina quality (2x scale)
python3 md_to_png.py input.md --output ~/Desktop/report.png --scale 2

# Custom width (wider = better for tables)
python3 md_to_png.py input.md --width 1400
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--output` / `-o` | `<input>.png` | Output PNG path |
| `--width` | `1200` | Content width in CSS pixels |
| `--scale` | `2` | Device scale factor (1 = standard, 2 = retina, 3 = 3x) |

## Pipeline

```
md ──builtin regex──→ HTML ──Playwright Chromium──→ PNG
```

The markdown→HTML converter supports: headings, tables, bold, inline code,
fenced code blocks, unordered lists, and horizontal rules. It's a minimal
regex-based converter (no external `markdown` package needed).

## Customising the look

Edit the CSS inside `HTML_TEMPLATE` in `md_to_png.py`:
- Font family / size
- Heading colours
- Table header background (`th { background: #1a73e8; ... }`)
- Section box styles

## Example

```bash
python3 md_to_png.py claude_vs_ohmy_pi.md --output ~/Desktop/claude_vs_omp.png --scale 2
```

Produces a 2400×4202 px retina PNG (~600 KB) ready to paste anywhere.
