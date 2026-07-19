#!/usr/bin/env python3

import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt

plot_dir = Path("plots")
out_pptx = "EFT_shape_comparison.pptx"

pattern = re.compile(r"(.+)_([A-Za-z0-9]+)_(\d+)_scaledC([0-9.]+)\.png")

groups = {}

for f in plot_dir.glob("*.png"):
    m = pattern.match(f.name)
    if not m:
        continue

    var, op, plotnum, scale = m.groups()
    key = (op, var, plotnum)

    groups.setdefault(key, []).append((float(scale), f))

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# title slide
slide = prs.slides.add_slide(prs.slide_layouts[6])
box = slide.shapes.add_textbox(Inches(0.8), Inches(2.7), Inches(12), Inches(1))
box.text_frame.text = "EFT Shape Comparison"
box.text_frame.paragraphs[0].font.size = Pt(38)
box.text_frame.paragraphs[0].font.bold = True

# one slide = same operator + same variable + three scales
for (op, var, plotnum), items in sorted(groups.items()):
    items = sorted(items, key=lambda x: x[0])

    # split into groups of 3 scales per slide
    for chunk_start in range(0, len(items), 3):
        chunk = items[chunk_start:chunk_start + 3]

        slide = prs.slides.add_slide(prs.slide_layouts[6])

        title = slide.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.5), Inches(0.5))
        title.text_frame.text = f"Operator: {op}, Variable:{var}"
        title.text_frame.paragraphs[0].font.size = Pt(24)
        title.text_frame.paragraphs[0].font.bold = True

        x_positions = [0.35, 4.55, 8.75]
        y_img = 1.15
        w_img = 4.3
        h_img = 4.8

        for i, (scale, img) in enumerate(chunk):
            label = slide.shapes.add_textbox(
                Inches(x_positions[i]),
                Inches(0.75),
                Inches(w_img),
                Inches(0.35),
            )
            label.text_frame.paragraphs[0].font.size = Pt(16)
            label.text_frame.paragraphs[0].font.bold = True

            slide.shapes.add_picture(
                str(img),
                Inches(x_positions[i]),
                Inches(y_img),
                width=Inches(w_img),
                height=Inches(h_img),
            )

prs.save(out_pptx)
print(f"Saved: {out_pptx}")