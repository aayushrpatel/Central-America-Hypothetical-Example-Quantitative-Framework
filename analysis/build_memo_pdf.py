"""Render memo/memo.md -> memo/memo.html -> memo/memo.pdf (Letter, via Playwright/Chromium).

Run:  python3 analysis/build_memo_pdf.py
"""
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
MEMO = ROOT / "memo"

CSS = """
@page { size: Letter; margin: 0.42in 0.5in; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.25pt; line-height: 1.25;
       color: #0b0b0b; background: #fff; }
h1 { font-size: 13pt; margin: 0 0 4px; }
h2 { font-size: 10pt; margin: 7px 0 2px; border-bottom: 1px solid #ccc; padding-bottom: 1px; }
h3 { font-size: 9pt; margin: 8px 0 3px; }
p { margin: 3px 0; }
ul, ol { margin: 2px 0 3px 16px; padding: 0; }
li { margin: 0; }
table { border-collapse: collapse; margin: 4px 0; width: 100%; page-break-inside: avoid; }
th, td { border: 1px solid #d0cec7; padding: 1.5px 5px; text-align: left; vertical-align: top; }
th { background: #f1f0ec; }
img { width: 68%; display: block; margin: 4px auto; }
code { font-size: 8pt; }
hr { border: 0; border-top: 1px solid #999; margin: 8px 0; page-break-after: always; }
h3 + p, h3 ~ ol { font-size: 7.6pt; }
ol li { word-break: break-all; }
"""


def main():
    md = (MEMO / "memo.md").read_text()
    body = markdown.markdown(md, extensions=["tables"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>LNG Strait Memo</title>" \
           f"<style>{CSS}</style></head><body>{body}</body></html>"
    (MEMO / "memo.html").write_text(html)
    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://{MEMO / "memo.html"}');
  await p.pdf({{ path: '{MEMO / "memo.pdf"}', format: 'Letter', printBackground: true,
                 margin: {{ top: '0.42in', bottom: '0.42in', left: '0.5in', right: '0.5in' }} }});
  await b.close();
}})();
"""
    subprocess.run(["node", "-e", js], check=True)
    print("wrote", MEMO / "memo.pdf")


if __name__ == "__main__":
    main()
