# md-to-png

Render any markdown file as a **retina-quality PNG** image — no markdown
renderer needed on the recipient's side. Drop it into Slack, email, or chat.

## Usage

```sh
pip install playwright
playwright install chromium

python3 md_to_png.py input.md --output output.png --scale 2
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--output` / `-o` | `<input>.png` | Output PNG path |
| `--width` | `1200` | Content width in CSS pixels |
| `--scale` | `2` | Device scale factor (1 = standard, 2 = retina, 3 = 3x) |

## Pipeline

```
md ──builtin regex──→ HTML ──Playwright Chromium──→ PNG
```

## License

BSD 3-Clause. See [LICENSE](LICENSE).
