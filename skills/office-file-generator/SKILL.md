---
name: office-file-generator
description: >
  Generate Word (.docx), Excel (.xlsx), PowerPoint (.pptx), and PDF files from user descriptions,
  structured data, or existing files like CSV/JSON/text. Also generates charts and data visualizations
  embedded in Excel or as standalone images. Use this skill whenever the user wants to create, build,
  generate, or export any Office or PDF document — even if they don't use exact terms like "Word" or
  "Excel". Trigger on: "make a report", "create a spreadsheet", "build a presentation", "turn this
  data into a table", "export as Excel", "make slides", "generate a contract/invoice/resume",
  "convert CSV to Excel", "put this in a PPT", "export as PDF", "make a chart", "plot this data",
  "generate a bar/pie/line chart". Always use this skill proactively when the user's intent involves
  producing a .docx, .xlsx, .pptx, or .pdf file, or any chart/graph output.
---

# Office File Generator

You help users create Word (.docx), Excel (.xlsx), PowerPoint (.pptx), PDF, and chart files using Python.

## Core Libraries

| Format | Library | Install |
|--------|---------|---------|
| Word | `python-docx` | `pip install python-docx` |
| Excel + Charts | `openpyxl` | `pip install openpyxl` |
| PowerPoint | `python-pptx` | `pip install python-pptx` |
| PDF (simple) | `reportlab` | `pip install reportlab` |
| PDF (HTML→PDF) | `weasyprint` | `pip install weasyprint` |
| Charts / Plots | `matplotlib` | `pip install matplotlib` |

Always check if the required library is installed first; install if missing.

## Workflow

1. **Understand the request** — identify format, content, style preferences, and output path
2. **Write a Python script** to generate the file
3. **Run the script** via Bash
4. **Confirm** the file was created, report the path and file size

## Output Path

- If the user specifies a path → use it
- Otherwise → save to the current working directory with a sensible filename

---

## Word (.docx) — python-docx

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('Document Title', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Heading + paragraph
doc.add_heading('Section 1', level=1)
doc.add_paragraph('Body text goes here.')

# Styled run
para = doc.add_paragraph()
run = para.add_run('Bold and colored text')
run.bold = True
run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
run.font.size = Pt(12)

# Table
table = doc.add_table(rows=1, cols=3)
table.style = 'Table Grid'
hdr = table.rows[0].cells
hdr[0].text = 'Name'; hdr[1].text = 'Role'; hdr[2].text = 'Score'
row = table.add_row().cells
row[0].text = 'Alice'; row[1].text = 'Dev'; row[2].text = '95'

doc.save('output.docx')
```

**Tips:**
- `doc.add_page_break()` for page breaks
- `doc.add_picture(path, width=Inches(4))` for images
- Table styles: `'Table Grid'`, `'Light Shading'`, `'Medium Shading 1'`

---

## Excel (.xlsx) with Charts — openpyxl

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference

wb = Workbook()
ws = wb.active
ws.title = 'Report'

# Header row
headers = ['Month', 'Revenue', 'Cost', 'Profit']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = Font(bold=True, color='FFFFFF')
    cell.fill = PatternFill('solid', fgColor='1F497D')
    cell.alignment = Alignment(horizontal='center')

# Data
data = [('Jan', 120000, 80000, 40000), ('Feb', 135000, 85000, 50000), ('Mar', 150000, 90000, 60000)]
for row_data in data:
    ws.append(row_data)

# Column widths
for col in ws.columns:
    ws.column_dimensions[get_column_letter(col[0].column)].width = 15

# ---- Bar Chart ----
chart = BarChart()
chart.type = "col"
chart.title = "Monthly Revenue vs Cost"
chart.y_axis.title = "Amount"
chart.x_axis.title = "Month"
chart.style = 10  # built-in style 1–48

data_ref = Reference(ws, min_col=2, max_col=3, min_row=1, max_row=len(data)+1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(data)+1)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
chart.shape = 4
ws.add_chart(chart, "F2")

# ---- Pie Chart ----
pie = PieChart()
pie.title = "Cost Breakdown"
pie_data = Reference(ws, min_col=3, min_row=1, max_row=len(data)+1)
pie.add_data(pie_data, titles_from_data=True)
pie.set_categories(cats)
ws.add_chart(pie, "F20")

wb.save('output.xlsx')
```

**Chart types available:** `BarChart`, `LineChart`, `PieChart`, `AreaChart`, `ScatterChart`
**Chart styles:** integers 1–48 (style=10 is a clean blue theme)

---

## PowerPoint (.pptx) with Random Theme — python-pptx

**Always apply a random built-in theme** unless the user specifies one. This makes presentations look polished without manual styling.

```python
import random
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# --- Built-in theme palette (background + accent colors) ---
THEMES = [
    {"name": "Ocean Blue",    "bg": "1F3864", "title": "FFFFFF", "accent": "00B0F0", "body": "DDEEFF"},
    {"name": "Forest Green",  "bg": "1E4D2B", "title": "FFFFFF", "accent": "70AD47", "body": "E2EFDA"},
    {"name": "Crimson",       "bg": "7B0000", "title": "FFFFFF", "accent": "FF9900", "body": "FFF2CC"},
    {"name": "Slate Gray",    "bg": "2E3440", "title": "ECEFF4", "accent": "88C0D0", "body": "E5E9F0"},
    {"name": "Sunset Orange", "bg": "843C0C", "title": "FFFFFF", "accent": "FFC000", "body": "FEF3C7"},
    {"name": "Royal Purple",  "bg": "3B1F6E", "title": "FFFFFF", "accent": "C55FFF", "body": "EDE7F6"},
    {"name": "Teal Modern",   "bg": "004B5A", "title": "FFFFFF", "accent": "00CED1", "body": "E0F7FA"},
    {"name": "Monochrome",    "bg": "212121", "title": "FAFAFA", "accent": "BDBDBD", "body": "F5F5F5"},
]

theme = random.choice(THEMES)
print(f"🎨 Using theme: {theme['name']}")

def hex_to_rgb(h):
    h = h.lstrip('#')
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def style_slide_bg(slide, prs, bg_hex):
    """Fill slide background with solid color."""
    from pptx.util import Pt
    from pptx.oxml.ns import qn
    from lxml import etree
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = hex_to_rgb(bg_hex)

def add_title_slide(prs, title_text, subtitle_text, theme):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout for full control
    style_slide_bg(slide, prs, theme['bg'])
    w, h = prs.slide_width, prs.slide_height

    # Title box
    txb = slide.shapes.add_textbox(Inches(0.8), Inches(2.2), w - Inches(1.6), Inches(1.5))
    tf = txb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title_text
    run.font.size = Pt(40)
    run.font.bold = True
    run.font.color.rgb = hex_to_rgb(theme['title'])

    # Subtitle box
    txb2 = slide.shapes.add_textbox(Inches(0.8), Inches(3.9), w - Inches(1.6), Inches(0.8))
    tf2 = txb2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = subtitle_text
    r2.font.size = Pt(20)
    r2.font.color.rgb = hex_to_rgb(theme['accent'])

    # Accent line
    from pptx.util import Emu
    line = slide.shapes.add_shape(1, Inches(2), Inches(3.7), w - Inches(4), Emu(40000))
    line.fill.solid()
    line.fill.fore_color.rgb = hex_to_rgb(theme['accent'])
    line.line.fill.background()
    return slide

def add_content_slide(prs, title_text, bullets, theme):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    style_slide_bg(slide, prs, theme['bg'])
    w, h = prs.slide_width, prs.slide_height

    # Title bar
    title_bar = slide.shapes.add_shape(1, 0, 0, w, Inches(1.2))
    title_bar.fill.solid()
    title_bar.fill.fore_color.rgb = hex_to_rgb(theme['accent'])
    title_bar.line.fill.background()

    # Title text
    txb = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), w - Inches(0.8), Inches(0.9))
    tf = txb.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title_text
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = hex_to_rgb(theme['bg'])

    # Bullet content
    txb2 = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), w - Inches(1.0), h - Inches(1.8))
    tf2 = txb2.text_frame
    tf2.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = f"• {bullet}"
        p.space_before = Pt(8)
        for run in p.runs:
            run.font.size = Pt(18)
            run.font.color.rgb = hex_to_rgb(theme['body'])
    return slide

# --- Build presentation ---
prs = Presentation()
prs.slide_width  = Inches(13.33)   # 16:9 widescreen
prs.slide_height = Inches(7.5)

add_title_slide(prs, "Presentation Title", "Subtitle · 2025", theme)

slides_content = [
    ("Topic One",   ["Key point A", "Key point B", "Key point C"]),
    ("Topic Two",   ["Key point D", "Key point E", "Key point F"]),
]
for title, bullets in slides_content:
    add_content_slide(prs, title, bullets, theme)

prs.save('output.pptx')
print(f"✅ Saved output.pptx with theme '{theme['name']}'")
```

**Available themes (randomly selected each run):**
`Ocean Blue`, `Forest Green`, `Crimson`, `Slate Gray`, `Sunset Orange`, `Royal Purple`, `Teal Modern`, `Monochrome`

If the user wants a specific theme, match by name or pick the closest match.

---

## PDF Generation

### Option A — reportlab (simple, no dependencies on system fonts)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT

doc = SimpleDocTemplate("output.pdf", pagesize=A4,
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2.5*cm, rightMargin=2.5*cm)
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle('Title', parent=styles['Title'],
    fontSize=22, textColor=colors.HexColor('#1F497D'), spaceAfter=16, alignment=TA_CENTER)
heading_style = ParagraphStyle('H1', parent=styles['Heading1'],
    fontSize=14, textColor=colors.HexColor('#1F497D'), spaceBefore=12, spaceAfter=6)
body_style = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=11, leading=16, spaceAfter=8)

story = []
story.append(Paragraph("Document Title", title_style))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Section 1", heading_style))
story.append(Paragraph("Body text here.", body_style))

# Table
data = [['Name', 'Role', 'Score'],
        ['Alice', 'Dev', '95'],
        ['Bob',   'PM',  '88']]
tbl = Table(data, colWidths=[5*cm, 5*cm, 4*cm])
tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
]))
story.append(Spacer(1, 0.3*cm))
story.append(tbl)

doc.build(story)
print("✅ PDF saved")
```

### Option B — matplotlib chart → embed in PDF

```python
import matplotlib.pyplot as plt
from reportlab.platypus import Image as RLImage
import tempfile, os

# Generate chart as temp PNG, then embed
fig, ax = plt.subplots(figsize=(6, 3.5))
ax.bar(['Jan','Feb','Mar'], [120000, 135000, 150000], color='#1F497D')
ax.set_title('Monthly Revenue')
ax.set_ylabel('Amount')
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    chart_path = f.name
fig.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()

story.append(RLImage(chart_path, width=14*cm, height=8*cm))
# ... doc.build(story) ...
os.unlink(chart_path)  # clean up temp file
```

---

## Chart Generation — matplotlib

Use matplotlib for standalone charts or charts to embed in PDF/Word/PPT.

```python
import matplotlib.pyplot as plt
import matplotlib.style as mstyle
import numpy as np

# Choose a style (try: 'seaborn-v0_8', 'ggplot', 'bmh', 'dark_background', 'fivethirtyeight')
plt.style.use('seaborn-v0_8')

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Bar chart
categories = ['Q1', 'Q2', 'Q3', 'Q4']
values = [120, 145, 165, 190]
axes[0].bar(categories, values, color='#1F497D', alpha=0.85, edgecolor='white')
axes[0].set_title('Quarterly Sales', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Revenue (k)')

# Line chart
months = np.arange(1, 13)
trend = np.array([80, 90, 95, 100, 115, 125, 130, 140, 145, 155, 165, 175])
axes[1].plot(months, trend, marker='o', color='#00B0F0', linewidth=2.5, markersize=6)
axes[1].fill_between(months, trend, alpha=0.15, color='#00B0F0')
axes[1].set_title('Monthly Trend', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Month')

plt.tight_layout()
plt.savefig('output_charts.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Chart saved")
```

**Chart type quick reference:**
| Chart | Code |
|-------|------|
| Bar | `ax.bar(x, y)` |
| Horizontal bar | `ax.barh(x, y)` |
| Line | `ax.plot(x, y)` |
| Scatter | `ax.scatter(x, y)` |
| Pie | `ax.pie(values, labels=labels, autopct='%1.1f%%')` |
| Histogram | `ax.hist(data, bins=20)` |
| Heatmap | `ax.imshow(matrix, cmap='Blues')` |

**Embed chart in Word:**
```python
doc.add_picture('output_charts.png', width=Inches(5.5))
```

**Embed chart in PPT:**
```python
slide.shapes.add_picture('output_charts.png', Inches(1), Inches(1.5), Inches(8), Inches(4.5))
```

---

## Converting Existing Data

**CSV → Excel:**
```python
import pandas as pd
df = pd.read_csv('data.csv')
df.to_excel('output.xlsx', index=False, engine='openpyxl')
```

**CSV/JSON → PDF report:**
```python
import pandas as pd, json
df = pd.read_csv('data.csv')   # or pd.read_json(...)
# Convert df rows to reportlab Table data
table_data = [df.columns.tolist()] + df.values.tolist()
```

**Word → PDF (via LibreOffice, if available):**
```bash
libreoffice --headless --convert-to pdf output.docx
```

---

## Error Handling

Always wrap file operations in try/except:

```python
try:
    # ... generate file ...
    import os
    size = os.path.getsize(output_path)
    print(f"✅ Saved: {output_path} ({size:,} bytes)")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback; traceback.print_exc()
```

---

## What to Tell the User

After successful generation:
1. Confirm file path and size
2. Describe what was generated (e.g., "5-slide PPTX using **Ocean Blue** theme, with title slide + 4 content slides")
3. For PPT: always mention which theme was applied
4. For charts: mention chart types included
