#!/opt/zothos-ai-env/bin/python3
"""Generate MetaDigitalGoods Brand Assets (Logo, Banners) & First Hotcake Printable Product Pack.

Generates:
1. shop_icon_500x500.png (Etsy Shop Icon)
2. shop_banner_big_3360x840.png (Etsy Big Banner)
3. shop_banner_mini_1200x160.png (Etsy Mini Banner)
4. Listing_1_Golden_Era_Trivia_Bingo_Pack.pdf (Multi-page 8.5x11 Large-Print Printable PDF)
5. Listing_1_Hero_Mockup_2000x2000.png (Etsy 1:1 Listing Thumbnail Mockup)
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("/home/zoth/NullAITech/etsy-connector/brand_assets/metadigitalgoods")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if serif:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_botanical_wreath(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, color_leaf: tuple, color_berry: tuple) -> None:
    """Draw a delicate botanical leaf & berry wreath around a center point."""
    num_leaves = 24
    for i in range(num_leaves):
        angle = (2 * math.pi * i) / num_leaves
        # Leave small gap at top and bottom
        if abs(math.cos(angle)) > 0.96:
            continue
        lx = cx + int(radius * math.sin(angle))
        ly = cy + int(radius * math.cos(angle))
        # Outer leaf tip
        tx = cx + int((radius + 18) * math.sin(angle + 0.08))
        ty = cy + int((radius + 18) * math.cos(angle + 0.08))
        draw.line([(lx, ly), (tx, ty)], fill=color_leaf, width=3)
        draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=color_leaf)
        if i % 3 == 0:
            bx = cx + int((radius - 10) * math.sin(angle - 0.05))
            by = cy + int((radius - 10) * math.cos(angle - 0.05))
            draw.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=color_berry)


def generate_shop_icon() -> Path:
    """Create 500x500 Etsy Shop Icon."""
    w, h = 500, 500
    # Warm heirloom cream background
    img = Image.new("RGB", (w, h), (250, 246, 238))
    draw = ImageDraw.Draw(img)

    # Deep sage inner medallion
    cx, cy = w // 2, h // 2
    draw.ellipse([30, 30, w - 30, h - 30], fill=(42, 68, 56), outline=(197, 160, 89), width=6)
    draw.ellipse([44, 44, w - 44, h - 44], outline=(197, 160, 89), width=2)

    # Botanical wreath accents
    draw_botanical_wreath(draw, cx, cy, 195, (143, 179, 157), (218, 175, 95))

    # Central monogram & brand title
    f_mono = get_font(96, bold=True, serif=True)
    f_title = get_font(28, bold=True, serif=True)
    f_sub = get_font(16, bold=False, serif=False)

    draw.text((cx, cy - 55), "MDG", font=f_mono, fill=(247, 239, 224), anchor="mm")
    draw.line([(cx - 110, cy + 10), (cx + 110, cy + 10)], fill=(197, 160, 89), width=2)
    draw.text((cx, cy + 45), "META DIGITAL", font=f_title, fill=(218, 175, 95), anchor="mm")
    draw.text((cx, cy + 82), "GOODS & PRINTABLES", font=f_sub, fill=(224, 232, 226), anchor="mm")

    out_path = OUT_DIR / "shop_icon_500x500.png"
    img.save(out_path, "PNG")
    return out_path


def generate_shop_banners() -> tuple[Path, Path]:
    """Create 3360x840 Big Shop Banner and 1200x160 Mini Banner."""
    w, h = 3360, 840
    img = Image.new("RGB", (w, h), (42, 68, 56))
    draw = ImageDraw.Draw(img)

    # Warm cream inner card with gold double border
    margin = 36
    draw.rectangle([margin, margin, w - margin, h - margin], fill=(252, 248, 240), outline=(197, 160, 89), width=6)
    draw.rectangle([margin + 14, margin + 14, w - margin - 14, h - margin - 14], outline=(143, 179, 157), width=3)

    # Left & Right decorative botanical pillars
    draw_botanical_wreath(draw, 340, h // 2, 240, (92, 133, 110), (197, 160, 89))
    draw_botanical_wreath(draw, w - 340, h // 2, 240, (92, 133, 110), (197, 160, 89))

    cx = w // 2
    f_top = get_font(38, bold=True, serif=False)
    f_main = get_font(112, bold=True, serif=True)
    f_sub = get_font(44, bold=False, serif=True)
    f_pill = get_font(34, bold=True, serif=False)

    draw.text((cx, 170), "★  INSTANT HOME PRINTABLES  •  EASY LARGE-PRINT DESIGNS  ★", font=f_top, fill=(158, 118, 48), anchor="mm")
    draw.text((cx, 330), "MetaDigitalGoods", font=f_main, fill=(35, 58, 48), anchor="mm")
    draw.text(
        (cx, 455),
        "Thoughtful Printable Games, Family Binders, Recipe Cards & Heirloom Crafts",
        font=f_sub,
        fill=(85, 102, 92),
        anchor="mm",
    )

    # 3 Value Badges at bottom
    badges = [
        "✓ Instant PDF Download",
        "✓ Prints on Standard 8.5\" x 11\" Paper",
        "✓ Easy-to-Read Large Print",
    ]
    badge_w = 680
    gap = 60
    start_x = cx - ((badge_w * 3 + gap * 2) // 2)
    by = 575
    for idx, text in enumerate(badges):
        bx = start_x + idx * (badge_w + gap)
        draw.rounded_rectangle([bx, by, bx + badge_w, by + 100], radius=24, fill=(42, 68, 56), outline=(197, 160, 89), width=3)
        draw.text((bx + badge_w // 2, by + 50), text, font=f_pill, fill=(252, 248, 240), anchor="mm")

    big_path = OUT_DIR / "shop_banner_big_3360x840.png"
    img.save(big_path, "PNG")

    # Mini Banner (1200x160)
    mw, mh = 1200, 160
    mini = Image.new("RGB", (mw, mh), (42, 68, 56))
    mdraw = ImageDraw.Draw(mini)
    mdraw.rectangle([8, 8, mw - 8, mh - 8], outline=(197, 160, 89), width=3)
    f_mtitle = get_font(42, bold=True, serif=True)
    f_msub = get_font(22, bold=False, serif=False)
    mdraw.text((mw // 2, 56), "MetaDigitalGoods  •  Heirloom Printables", font=f_mtitle, fill=(252, 248, 240), anchor="mm")
    mdraw.text((mw // 2, 112), "Instant Digital Downloads  |  Large-Print Games  |  Home & Health Binders  |  Recipe Cards", font=f_msub, fill=(218, 175, 95), anchor="mm")
    mini_path = OUT_DIR / "shop_banner_mini_1200x160.png"
    mini.save(mini_path, "PNG")

    return big_path, mini_path


def generate_golden_era_printable_pdf() -> Path:
    """Create a real multi-page 8.5x11 (150 DPI: 1275x1650 px) Large-Print 1950s/1960s Trivia & Bingo Pack PDF."""
    pw, ph = 1275, 1650
    pages = []

    f_h1 = get_font(54, bold=True, serif=True)
    f_h2 = get_font(34, bold=True, serif=True)
    f_body = get_font(28, bold=False, serif=False)
    f_bold = get_font(28, bold=True, serif=False)
    f_small = get_font(22, bold=False, serif=False)

    # PAGE 1: Cover & Printing Guide
    p1 = Image.new("RGB", (pw, ph), (253, 250, 244))
    d1 = ImageDraw.Draw(p1)
    d1.rectangle([45, 45, pw - 45, ph - 45], outline=(42, 68, 56), width=6)
    d1.rectangle([60, 60, pw - 60, ph - 60], outline=(197, 160, 89), width=3)

    d1.text((pw // 2, 200), "META DIGITAL GOODS • LARGE-PRINT EDITION", font=f_bold, fill=(158, 118, 48), anchor="mm")
    d1.text((pw // 2, 310), "1950s & 1960s Golden Era", font=f_h1, fill=(35, 58, 48), anchor="mm")
    d1.text((pw // 2, 385), "Nostalgia Trivia & Classic Bingo Bundle", font=f_h2, fill=(65, 90, 78), anchor="mm")
    d1.line([(200, 445), (pw - 200, 445)], fill=(197, 160, 89), width=3)

    features = [
        "✓ Designed with Easy-on-the-Eyes 18pt+ Large Print",
        "✓ Ready to Print at Home on Standard 8.5\" x 11\" Letter Paper",
        "✓ Perfect for Family Reunions, Church Socials, Senior Centers & Parties",
        "✓ Includes 20 Golden Era Trivia Questions + Full Answer Key",
        "✓ Includes 6 Unique Large-Print Nostalgia Bingo Cards + Caller Sheet",
    ]
    y = 540
    for feat in features:
        d1.text((140, y), feat, font=f_body, fill=(40, 48, 44))
        y += 72

    d1.rounded_rectangle([120, 960, pw - 120, 1420], radius=20, fill=(242, 236, 224), outline=(197, 160, 89), width=3)
    d1.text((pw // 2, 1025), "EASY HOME PRINTING TIPS", font=f_h2, fill=(35, 58, 48), anchor="mm")
    tips = [
        "1. Load standard 8.5\" x 11\" US Letter paper (or heavy cardstock for Bingo).",
        "2. In your printer dialog, select 'Actual Size' or 'Fit to Printable Area'.",
        "3. Print as many copies of the Trivia Sheet as you have guests!",
        "4. Need help? Message MetaDigitalGoods on Etsy anytime for fast support.",
    ]
    ty = 1105
    for tip in tips:
        d1.text((160, ty), tip, font=f_small, fill=(55, 65, 60))
        ty += 64

    d1.text((pw // 2, 1540), "© MetaDigitalGoods • Crafted for Memorable Gatherings", font=f_small, fill=(120, 130, 125), anchor="mm")
    pages.append(p1)

    # PAGE 2: Large-Print Trivia Game (Questions 1-10)
    trivia_q1 = [
        ("1. Which rock-and-roll icon sang 'Hound Dog' and 'Love Me Tender' in 1956?", "Elvis Presley"),
        ("2. What classic 1950s sitcom starred Lucille Ball and Desi Arnaz?", "I Love Lucy"),
        ("3. What plastic hoop toy became a nationwide sensation in 1958?", "The Hula Hoop"),
        ("4. Who hosted 'American Bandstand' starting in 1956?", "Dick Clark"),
        ("5. Which 1960s British band debuted on The Ed Sullivan Show in 1964?", "The Beatles"),
        ("6. What was the name of the sheriff played by Andy Griffith in Mayberry?", "Sheriff Andy Taylor"),
        ("7. What popular two-piece saddle shoe colors were worn by 1950s teens?", "Black and White"),
        ("8. Which 1965 musical film starred Julie Andrews as Maria von Trapp?", "The Sound of Music"),
        ("9. What coin was commonly placed inside loafers for good luck in the 1950s?", "A Shiny Penny (Penny Loafers)"),
        ("10. On what date did Apollo 11 land on the Moon in July 1969?", "July 20, 1969"),
    ]

    p2 = Image.new("RGB", (pw, ph), (255, 255, 255))
    d2 = ImageDraw.Draw(p2)
    d2.rectangle([45, 45, pw - 45, ph - 45], outline=(42, 68, 56), width=5)
    d2.text((pw // 2, 115), "GOLDEN ERA NOSTALGIA TRIVIA (PART 1)", font=f_h2, fill=(35, 58, 48), anchor="mm")
    d2.text((pw // 2, 165), "Player Name: ____________________________    Score: _____ / 10", font=f_small, fill=(80, 90, 85), anchor="mm")
    d2.line([(80, 200), (pw - 80, 200)], fill=(197, 160, 89), width=2)

    qy = 240
    for q, _ in trivia_q1:
        d2.text((90, qy), q, font=f_bold, fill=(30, 35, 32))
        d2.text((120, qy + 52), "Answer: ______________________________________________________", font=f_body, fill=(110, 120, 115))
        qy += 130
    pages.append(p2)

    # PAGE 3: Large-Print Trivia Game (Questions 11-20)
    trivia_q2 = [
        ("11. Which animated Stone Age family debuted on prime-time TV in 1960?", "The Flintstones"),
        ("12. What 1959 Mattel fashion doll was named after Ruth Handler's daughter?", "Barbie"),
        ("13. Which smooth crooner was famous for 'Moon River' and holiday sweaters?", "Andy Williams"),
        ("14. What drive-in restaurant chain featured carhops on roller skates?", "Sonic / A&W Drive-In"),
        ("15. Which 1960s dance craze did Chubby Checker make famous?", "The Twist"),
        ("16. What was the name of the family dog on 'The Brady Bunch'?", "Tiger"),
        ("17. Which green gelatin salad mold was a staple at 1950s church potlucks?", "Lime Jell-O Salad"),
        ("18. Who played Mary Richards on 'The Mary Tyler Moore Show'?", "Mary Tyler Moore"),
        ("19. What 3-wheeled childhood bike had tassels on the handlebars?", "Tricycle"),
        ("20. What phrase did Ed Sullivan famously use to introduce his big show?", "'A Really Big Shew!'"),
    ]

    p3 = Image.new("RGB", (pw, ph), (255, 255, 255))
    d3 = ImageDraw.Draw(p3)
    d3.rectangle([45, 45, pw - 45, ph - 45], outline=(42, 68, 56), width=5)
    d3.text((pw // 2, 115), "GOLDEN ERA NOSTALGIA TRIVIA (PART 2)", font=f_h2, fill=(35, 58, 48), anchor="mm")
    d3.line([(80, 165), (pw - 80, 165)], fill=(197, 160, 89), width=2)

    qy = 210
    for q, _ in trivia_q2:
        d3.text((90, qy), q, font=f_bold, fill=(30, 35, 32))
        d3.text((120, qy + 52), "Answer: ______________________________________________________", font=f_body, fill=(110, 120, 115))
        qy += 130
    pages.append(p3)

    # PAGE 4: Host Answer Key
    p4 = Image.new("RGB", (pw, ph), (253, 250, 244))
    d4 = ImageDraw.Draw(p4)
    d4.rectangle([45, 45, pw - 45, ph - 45], outline=(42, 68, 56), width=5)
    d4.text((pw // 2, 120), "HOST ANSWER KEY • GOLDEN ERA TRIVIA", font=f_h2, fill=(35, 58, 48), anchor="mm")
    d4.line([(80, 170), (pw - 80, 170)], fill=(197, 160, 89), width=2)

    ay = 215
    for q, a in trivia_q1 + trivia_q2:
        num = q.split(".")[0]
        d4.text((95, ay), f"{num}. {a}", font=f_bold, fill=(35, 58, 48))
        ay += 66
    pages.append(p4)

    # PAGES 5-8: 4 Unique Large-Print Golden Era Bingo Cards
    bingo_items = [
        "I Love Lucy", "Elvis Presley", "Hula Hoop", " Drive-In Movie", "Saddle Shoes",
        "Jukebox", "Penny Loafers", "Poodle Skirt", "Milkshake", "The Beatles",
        "Ed Sullivan", "Andy Griffith", "The Twist", "Root Beer Float", "Tupperware",
        "Rotary Phone", "TV Dinner", "Lava Lamp", "Moon Landing", "Sound of Music",
        "Dick Clark", "Roller Skates", "Record Player", "Church Potluck", "Sunday Drive",
    ]

    rng = random.Random(42)
    for card_idx in range(1, 5):
        pb = Image.new("RGB", (pw, ph), (255, 255, 255))
        db = ImageDraw.Draw(pb)
        db.rectangle([45, 45, pw - 45, ph - 45], outline=(42, 68, 56), width=5)
        db.text((pw // 2, 130), f"GOLDEN ERA MEMORIES BINGO  •  CARD #{card_idx}", font=f_h2, fill=(35, 58, 48), anchor="mm")
        db.text((pw // 2, 185), "Mark 5 in a row horizontally, vertically, or diagonally to win!", font=f_small, fill=(90, 100, 95), anchor="mm")

        grid_left = 112
        grid_top = 240
        cell_size = 210
        headers = ["B", "I", "N", "G", "O"]

        # Header row
        for col, h_char in enumerate(headers):
            x0 = grid_left + col * cell_size
            db.rectangle([x0, grid_top, x0 + cell_size, grid_top + 90], fill=(42, 68, 56), outline=(255, 255, 255), width=3)
            db.text((x0 + cell_size // 2, grid_top + 45), h_char, font=f_h1, fill=(252, 248, 240), anchor="mm")

        shuffled = bingo_items[:]
        rng.shuffle(shuffled)

        for row in range(5):
            for col in range(5):
                x0 = grid_left + col * cell_size
                y0 = grid_top + 90 + row * cell_size
                is_free = row == 2 and col == 2
                bg = (242, 236, 224) if is_free else (255, 255, 255)
                db.rectangle([x0, y0, x0 + cell_size, y0 + cell_size], fill=bg, outline=(42, 68, 56), width=3)
                label = "★ FREE ★\nSPACE" if is_free else shuffled[row * 5 + col].strip()
                # Wrap into 2 lines if needed
                words = label.split()
                if not is_free and len(words) >= 2:
                    mid = len(words) // 2
                    label = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
                db.multiline_text(
                    (x0 + cell_size // 2, y0 + cell_size // 2),
                    label,
                    font=f_bold if is_free else f_small,
                    fill=(158, 118, 48) if is_free else (30, 35, 32),
                    anchor="mm",
                    align="center",
                )

        db.text((pw // 2, 1520), "MetaDigitalGoods  •  Easy-to-Read Large Print", font=f_small, fill=(110, 120, 115), anchor="mm")
        pages.append(pb)

    pdf_path = OUT_DIR / "Listing_1_Golden_Era_Trivia_Bingo_Pack.pdf"
    pages[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return pdf_path, pages


def generate_listing_hero_mockup(pages: list[Image.Image]) -> Path:
    """Create a 2000x2000 high-converting Etsy Listing Hero Thumbnail Mockup."""
    w, h = 2000, 2000
    img = Image.new("RGB", (w, h), (244, 238, 226))
    draw = ImageDraw.Draw(img)

    # Top banner header
    draw.rectangle([0, 0, w, 280], fill=(42, 68, 56))
    draw.line([(0, 280), (w, 280)], fill=(197, 160, 89), width=10)
    f_banner = get_font(76, bold=True, serif=True)
    f_sub = get_font(40, bold=True, serif=False)
    draw.text((w // 2, 110), "1950s & 1960s GOLDEN ERA PARTY PACK", font=f_banner, fill=(252, 248, 240), anchor="mm")
    draw.text((w // 2, 210), "LARGE-PRINT TRIVIA + BINGO CARDS + ANSWER KEY (INSTANT PDF)", font=f_sub, fill=(218, 175, 95), anchor="mm")

    # Place 3 tilted/cascading page previews on the warm linen surface
    positions = [(110, 380), (660, 430), (1180, 380)]
    preview_indices = [0, 1, 4]
    for (px, py), p_idx in zip(positions, preview_indices):
        card = pages[p_idx].resize((700, 906), Image.Resampling.LANCZOS)
        # Drop shadow
        draw.rounded_rectangle([px + 14, py + 18, px + 714, py + 924], radius=8, fill=(205, 196, 182))
        img.paste(card, (px, py))
        draw.rectangle([px, py, px + 700, py + 906], outline=(180, 170, 155), width=3)

    # Bottom conversion callout bar
    draw.rounded_rectangle([80, 1420, w - 80, 1920], radius=36, fill=(42, 68, 56), outline=(197, 160, 89), width=6)
    f_call = get_font(56, bold=True, serif=True)
    f_bull = get_font(42, bold=False, serif=False)
    draw.text((w // 2, 1515), "★  EASY-TO-READ LARGE PRINT  •  PRINTS AT HOME  ★", font=f_call, fill=(218, 175, 95), anchor="mm")
    draw.text((w // 2, 1630), "✓ 20 Nostalgic 50s & 60s Trivia Questions + Host Answer Key", font=f_bull, fill=(252, 248, 240), anchor="mm")
    draw.text((w // 2, 1720), "✓ Unique Large-Print Bingo Cards  •  Standard 8.5\" x 11\" Letter Size", font=f_bull, fill=(252, 248, 240), anchor="mm")
    draw.text((w // 2, 1815), "✓ Instant Digital Download — Print Unlimited Copies for Your Gathering!", font=f_bull, fill=(143, 179, 157), anchor="mm")

    mockup_path = OUT_DIR / "Listing_1_Hero_Mockup_2000x2000.png"
    img.save(mockup_path, "PNG")
    return mockup_path


if __name__ == "__main__":
    icon = generate_shop_icon()
    big_b, mini_b = generate_shop_banners()
    pdf_p, rendered_pages = generate_golden_era_printable_pdf()
    mockup_p = generate_listing_hero_mockup(rendered_pages)
    print(f"Generated Icon:        {icon}")
    print(f"Generated Big Banner:  {big_b}")
    print(f"Generated Mini Banner: {mini_b}")
    print(f"Generated Product PDF: {pdf_p}")
    print(f"Generated Hero Mockup: {mockup_p}")
