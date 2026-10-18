"""Build the report: report/report_*.html parts -> report/report.html -> PDF with page numbers.

Run from the repository root after the notebook has written outputs/figures:
    .venv/bin/python report/build.py
"""
import glob, io, os, subprocess, tempfile
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_PDF = os.path.join(HERE, "..", "F1_Podium_Prediction_Report_Team10.pdf")

CSS = """
@page { size: A4; margin: 18mm 18mm 20mm 18mm; }
:root { --blue: #1f4e79; --rule: #d9dee5; --muted: #6b7280; --head: #f3f5f8; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 10.4pt; line-height: 1.5; color: #222; background: #fff; }
h1 { color: var(--blue); font-size: 20pt; border-bottom: 2px solid var(--blue); padding-bottom: 6px; margin: 0 0 14px; break-before: page; }
h1.title { font-size: 28pt; border: none; margin: 4px 0 6px; break-before: auto; }
h2 { color: var(--blue); font-size: 13.5pt; margin: 18px 0 6px; break-after: avoid; }
h3 { font-size: 11pt; margin: 14px 0 4px; break-after: avoid; }
p { margin: 6px 0; } ul { margin: 4px 0 8px; padding-left: 20px; } li { margin: 2px 0; }
code { font-family: Menlo, monospace; font-size: 8.6pt; background: #eef1f5; padding: 0 3px; border-radius: 3px; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 8px 0 2px; }
tr { break-inside: avoid; }
th { background: var(--head); text-align: left; font-weight: 600; padding: 5px 6px; border-bottom: 1px solid var(--rule); }
td { padding: 5px 6px; border-bottom: 1px solid var(--rule); vertical-align: top; }
table.num td:not(:first-child), table.num th:not(:first-child) { text-align: right; }
table.num .l { text-align: left !important; }
table.num td:not(.l):not(:first-child) { white-space: nowrap; }
table.narrow { width: auto; min-width: 55%; }
tr.hl td { background: #fff7e0; font-weight: 600; }
.cap, figcaption { font-size: 8.4pt; color: var(--muted); margin: 3px 0 12px; }
.cap b, figcaption b { color: #222; }
figure { margin: 10px 0; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; }
figcaption { text-align: left; }
.side { display: flex; gap: 16px; align-items: flex-start; break-inside: avoid; }
.side > * { flex: 1; } .side figure { margin-top: 0; }
.box { border: 1px solid var(--rule); border-left: 4px solid var(--blue); background: #f7f9fc; padding: 8px 12px; margin: 10px 0; break-inside: avoid; }
.kicker { font-size: 9pt; letter-spacing: .08em; color: var(--muted); text-transform: uppercase; margin-top: 4mm; }
.sub { color: #4b5563; font-size: 11pt; }
table.meta td:first-child { color: var(--muted); font-weight: 600; width: 26%; }
.todo { background: #fff3c4; padding: 1px 5px; font-weight: 600; }
.grain { font-size: 9.2pt; color: #374151; background: #f7f7f7; padding: 6px 10px; border-radius: 4px; }
"""

def build_html():
    parts = sorted(glob.glob(os.path.join(HERE, "report_part*.html")))
    body = "\n".join(open(p, encoding="utf-8").read() for p in parts)
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>F1 Podium Prediction Report</title>
<style>{CSS}</style></head><body>
{body}
</body></html>"""
    path = os.path.join(HERE, "report.html")
    open(path, "w", encoding="utf-8").write(html)
    return path

def to_pdf(html_path):
    tmp = tempfile.mktemp(suffix=".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    f"--print-to-pdf={tmp}", "file://" + html_path], check=True, capture_output=True)
    return tmp

def number_pages(src, dst):
    reader = PdfReader(src); writer = PdfWriter(); n = len(reader.pages)
    for i, page in enumerate(reader.pages, start=1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(w, h))
        c.setFont("Helvetica", 8); c.setFillGray(0.45); c.drawCentredString(w / 2, 26, f"{i} / {n}"); c.save()
        buf.seek(0); page.merge_page(PdfReader(buf).pages[0]); writer.add_page(page)
    with open(dst, "wb") as f:
        writer.write(f)
    return n

if __name__ == "__main__":
    html = build_html()
    pages = number_pages(to_pdf(html), OUT_PDF)
    print(f"{os.path.relpath(OUT_PDF)}: {pages} pages")
