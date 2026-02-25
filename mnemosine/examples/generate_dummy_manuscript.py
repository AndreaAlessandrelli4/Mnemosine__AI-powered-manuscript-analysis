#!/usr/bin/env python3
"""
Generate a dummy manuscript directory for testing Mnemosine.

Usage:
    python generate_dummy_manuscript.py [output_dir]

Creates:
    <output_dir>/
        Immagini/
            001_frontespizio.jpg
            002_pagina_interna.jpg
            003_pagina_interna.jpg
            004_retro.jpg
        OUTPUT/  (empty, will be populated by pipeline)
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow required: pip install Pillow")
    sys.exit(1)


def create_page_image(path: Path, page_num: int, text: str, size=(800, 1100)):
    """Create a simple manuscript-like page image."""
    img = Image.new("RGB", size, color=(245, 240, 230))  # parchment-like
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle(
        [40, 40, size[0] - 40, size[1] - 40],
        outline=(139, 120, 100),
        width=2,
    )

    # Header
    header = f"Page {page_num:03d}"
    draw.text((60, 60), header, fill=(80, 60, 40))

    # Body text
    y = 120
    lines = text.split("\n")
    for line in lines:
        if y > size[1] - 80:
            break
        draw.text((60, y), line, fill=(40, 30, 20))
        y += 24

    # Page number at bottom
    draw.text(
        (size[0] // 2, size[1] - 60),
        str(page_num),
        fill=(100, 80, 60),
        anchor="mm",
    )

    img.save(str(path), "JPEG", quality=90)


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dummy_manuscript")
    images_dir = output / "Immagini"
    output_dir = output / "OUTPUT"

    images_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = [
        (1, "001_frontespizio.jpg", "LIBER SANCTI AUGUSTINI\nDE CIVITATE DEI\n\nCodex Membranaceus\nSaeculum XIV"),
        (2, "002_pagina_interna.jpg", "Incipit liber primus.\n\nGloriosissimam civitatem Dei\nsive in hoc temporum cursu\ncum inter impios peregrinatur\nex fide vivens..."),
        (3, "003_pagina_interna.jpg", "...quae sit ista civitas\nquam dico. Cum enim\nduae sint civitates,\nuna malorum, altera bonorum\nab initio generis humani\nusque in finem saeculi..."),
        (4, "004_retro.jpg", "Explicit liber primus\nDeo gratias\n\n[Annotazione marginale:\nCorrectum per me fr. Iohannem]"),
    ]

    for page_num, filename, text in pages:
        path = images_dir / filename
        create_page_image(path, page_num, text)
        print(f"Created: {path}")

    print(f"\nDummy manuscript created at: {output}")
    print(f"  - {len(pages)} page images in {images_dir}")
    print(f"  - Empty OUTPUT directory at {output_dir}")
    print(f"\nTo analyze: POST /analyze with manuscript_path=\"{output.resolve()}\"")


if __name__ == "__main__":
    main()
