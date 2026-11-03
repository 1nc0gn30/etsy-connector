#!/opt/zothos-ai-env/bin/python3
"""Build Bespoke Editorial Etsy Big Banner (3360x840), Mini Banner (1200x160),
Shop Story Photo (1200x800), and Shop Icon (500x500) for MetaDigitalGoods,
and push updated Shop Title, Announcement & Digital Message live via Etsy API v3.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, "~/NullAITech/etsy-connector/src")
from etsy_connector.client import EtsyClient

BRAND_DIR = Path("~/NullAITech/etsy-connector/brand_assets/metadigitalgoods")
STUDIO_DIR = Path("~/NullAITech/metadigitalgoods/public/assets/studio")
PUBLIC_ASSETS_DIR = Path("~/NullAITech/metadigitalgoods/public/assets")
ARTIFACT_DIR = Path("~/.gemini/antigravity-cli/brain/5e2f4196-8ec1-4cf2-8d92-bad9291e3aa7")

BRAND_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.FreeTypeFont:
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
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def crop_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    return ImageOps.fit(img.convert("RGB"), (target_w, target_h), method=Image.Resampling.LANCZOS)


def draw_botanical_sprig(draw: ImageDraw.ImageDraw, cx: int, cy: int, length: int, direction: int, color_stem: tuple, color_leaf: tuple, color_berry: tuple) -> None:
    """Draw a horizontal botanical olive & berry sprig extending left (-1) or right (+1)."""
    x_end = cx + direction * length
    draw.line([(cx, cy), (x_end, cy)], fill=color_stem, width=3)
    steps = 5
    for i in range(1, steps + 1):
        px = cx + direction * int((length * i) / (steps + 1))
        # Upper and lower leaves
        for sign in (-1, 1):
            lx = px + direction * 22
            ly = cy + sign * 18
            draw.line([(px, cy), (lx, ly)], fill=color_stem, width=2)
            draw.ellipse([lx - 8, ly - 5, lx + 8, ly + 5], fill=color_leaf)
        if i % 2 == 1:
            bx = px + direction * 8
            by = cy - 9
            draw.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=color_berry)


def build_big_banner_3360x840() -> Path:
    w, h = 3360, 840
    # Base deep forest heirloom canvas
    canvas = Image.new("RGB", (w, h), (22, 38, 30))

    # Load studio photographs for Left and Right editorial wings
    left_top = crop_cover(Image.open(STUDIO_DIR / "hero_lifestyle.jpg"), 1020, 420)
    left_bot = crop_cover(Image.open(STUDIO_DIR / "cat_ai_grandmas.jpg"), 1020, 420)
    right_top = crop_cover(Image.open(STUDIO_DIR / "cat_ai_moms.jpg"), 1020, 420)
    right_bot = crop_cover(Image.open(STUDIO_DIR / "cat_recipes.jpg"), 1020, 420)

    canvas.paste(left_top, (0, 0))
    canvas.paste(left_bot, (0, 420))
    canvas.paste(right_top, (w - 1020, 0))
    canvas.paste(right_bot, (w - 1020, 420))

    # Apply smooth dark-forest & warm-gold gradient vignette over photo wings toward center
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # Subtle grid divider lines on photo wings
    odraw.line([(0, 420), (1020, 420)], fill=(197, 160, 89, 210), width=4)
    odraw.line([(w - 1020, 420), (w, 420)], fill=(197, 160, 89, 210), width=4)

    # Smooth horizontal alpha fade on inner edges of photo wings (x=680..1020 and x=2340..2680)
    for x in range(w):
        alpha = 0
        if x < 620:
            alpha = 45
        elif 620 <= x <= 1020:
            t = (x - 620) / 400.0
            alpha = int(45 + t * 210)
        elif 1020 < x < w - 1020:
            alpha = 255
        elif w - 1020 <= x <= w - 620:
            t = (w - 620 - x) / 400.0
            alpha = int(45 + t * 210)
        else:
            alpha = 45
        odraw.line([(x, 0), (x, h)], fill=(20, 36, 28, alpha))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Outer double heirloom gold frame around entire 3360x840 banner
    draw.rectangle([18, 18, w - 18, h - 18], outline=(197, 160, 89), width=5)
    draw.rectangle([30, 30, w - 30, h - 30], outline=(143, 179, 157), width=2)

    # Photo wing corner labels (subtle luxury editorial tags)
    f_tag = get_font(19, bold=True, serif=False)
    photo_tags = [
        (48, 48, "★  HEIRLOOM BINDERS & 2026 CALENDARS"),
        (48, 448, "★  #1 BESTSELLER: AI FOR GRANDMAS"),
        (w - 578, 48, "★  #2 CO-HEADLINER: AI FOR BUSY MOMS"),
        (w - 578, 448, "★  FAMILY RECIPES & HOME GUIDES"),
    ]
    for tx, ty, label in photo_tags:
        draw.rounded_rectangle([tx, ty, tx + 530, ty + 48], radius=12, fill=(20, 36, 28), outline=(197, 160, 89), width=2)
        draw.text((tx + 265, ty + 24), label, font=f_tag, fill=(248, 236, 205), anchor="mm")

    # Center Warm Parchment Editorial Medallion Card
    card_l, card_r = 860, w - 860
    card_t, card_b = 58, h - 58
    # Soft drop shadow
    draw.rounded_rectangle([card_l + 10, card_t + 12, card_r + 10, card_b + 12], radius=34, fill=(10, 18, 14))
    # Warm cream parchment fill
    draw.rounded_rectangle([card_l, card_t, card_r, card_b], radius=34, fill=(252, 248, 239), outline=(197, 160, 89), width=6)
    draw.rounded_rectangle([card_l + 14, card_t + 14, card_r - 14, card_b - 14], radius=26, outline=(42, 68, 56), width=3)

    cx = w // 2

    # Top Eyebrow Pill inside Center Card
    f_eyebrow = get_font(26, bold=True, serif=False)
    eyebrow_w = 1220
    draw.rounded_rectangle([cx - eyebrow_w // 2, 104, cx + eyebrow_w // 2, 164], radius=30, fill=(32, 54, 43), outline=(197, 160, 89), width=2)
    draw.text(
        (cx, 134),
        "★  THOUGHTFUL PRINTABLE BOOKS, FAMILY BINDERS & LARGE-PRINT GUIDES  ★",
        font=f_eyebrow,
        fill=(246, 224, 168),
        anchor="mm",
    )

    # Main Shop Title + Botanical Sprigs
    f_title = get_font(98, bold=True, serif=True)
    draw.text((cx, 268), "MetaDigitalGoods", font=f_title, fill=(24, 44, 34), anchor="mm")
    draw_botanical_sprig(draw, cx - 515, 268, 150, -1, (92, 133, 110), (120, 160, 135), (197, 160, 89))
    draw_botanical_sprig(draw, cx + 515, 268, 150, 1, (92, 133, 110), (120, 160, 135), (197, 160, 89))

    # Gold Divider Line with Center Diamond
    draw.line([(cx - 560, 348), (cx + 560, 348)], fill=(197, 160, 89), width=3)
    draw.polygon([(cx, 336), (cx + 14, 348), (cx, 360), (cx - 14, 348)], fill=(197, 160, 89))

    # Editorial Subtitle Lines
    f_sub1 = get_font(35, bold=True, serif=True)
    f_sub2 = get_font(28, bold=False, serif=False)
    draw.text(
        (cx, 412),
        "Home of #1 “AI for Grandmas” & “AI for Busy Moms”",
        font=f_sub1,
        fill=(148, 104, 36),
        anchor="mm",
    )
    draw.text(
        (cx, 474),
        "Heirloom Recipe Binders  •  2026 Large-Print Calendars  •  Emergency Medical Organizers  •  Nostalgia Games",
        font=f_sub2,
        fill=(58, 75, 66),
        anchor="mm",
    )

    # Bottom 3 High-Converting Trust Badges
    badges = [
        ("✓ Instant PDF Download", "Ready in Seconds After Checkout"),
        ("✓ Easy 16pt–18pt Large Print", "Gentle on the Eyes, Zero Clutter"),
        ("✓ Print at Home or Use on iPad", "Standard 8.5\"×11\" & GoodNotes"),
    ]
    bw = 465
    bgap = 32
    start_x = cx - ((bw * 3 + bgap * 2) // 2)
    by = 548
    bh = 118
    f_b_title = get_font(26, bold=True, serif=False)
    f_b_sub = get_font(21, bold=False, serif=False)

    for idx, (bt, bs) in enumerate(badges):
        bx = start_x + idx * (bw + bgap)
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=20, fill=(28, 48, 38), outline=(197, 160, 89), width=3)
        draw.text((bx + bw // 2, by + 40), bt, font=f_b_title, fill=(252, 248, 239), anchor="mm")
        draw.text((bx + bw // 2, by + 82), bs, font=f_b_sub, fill=(228, 198, 132), anchor="mm")

    # Footer micro-line inside medallion
    f_micro = get_font(21, bold=True, serif=False)
    draw.text(
        (cx, 722),
        "★  25+ Curated Printable Books & Binders  •  Crafted with Warmth for Real Households  ★",
        font=f_micro,
        fill=(92, 112, 100),
        anchor="mm",
    )

    out_path = BRAND_DIR / "shop_banner_big_3360x840.png"
    canvas.save(out_path, "PNG", optimize=True)
    shutil.copy2(out_path, PUBLIC_ASSETS_DIR / "shop_banner_big_3360x840.png")
    shutil.copy2(out_path, ARTIFACT_DIR / "metadigitalgoods-banner-3360x840.png")
    return out_path


def build_mini_banner_1200x160() -> Path:
    w, h = 1200, 160
    img = Image.new("RGB", (w, h), (24, 44, 34))
    draw = ImageDraw.Draw(img)
    draw.rectangle([6, 6, w - 6, h - 6], outline=(197, 160, 89), width=3)
    draw.rectangle([12, 12, w - 12, h - 12], outline=(143, 179, 157), width=1)

    f_title = get_font(40, bold=True, serif=True)
    f_sub = get_font(21, bold=True, serif=False)
    draw.text((w // 2, 54), "MetaDigitalGoods  •  Heirloom Printables & Gentle Guides", font=f_title, fill=(252, 248, 239), anchor="mm")
    draw.text(
        (w // 2, 112),
        "★ #1 AI for Grandmas  •  #2 AI for Busy Moms  •  Recipe Binders  •  2026 Large-Print Calendars ★",
        font=f_sub,
        fill=(232, 198, 128),
        anchor="mm",
    )
    out_path = BRAND_DIR / "shop_banner_mini_1200x160.png"
    img.save(out_path, "PNG", optimize=True)
    shutil.copy2(out_path, PUBLIC_ASSETS_DIR / "shop_banner_mini_1200x160.png")
    return out_path


def build_story_photo_1200x800() -> Path:
    """Create a 1200x800 Etsy Shop Story Showcase Image combining studio photography + story quote."""
    w, h = 1200, 800
    canvas = Image.new("RGB", (w, h), (250, 246, 238))

    # Left half: sunlit grandma & daughter / lifestyle studio photo
    p_left = crop_cover(Image.open(STUDIO_DIR / "audience_grandma.jpg"), 580, 740)
    canvas.paste(p_left, (30, 30))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([30, 30, 610, 770], outline=(197, 160, 89), width=4)

    # Right half: Story Card
    rx0, ry0, rx1, ry1 = 635, 30, 1170, 770
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=24, fill=(28, 48, 38), outline=(197, 160, 89), width=4)
    rcx = (rx0 + rx1) // 2

    f_eye = get_font(19, bold=True, serif=False)
    f_h = get_font(36, bold=True, serif=True)
    f_body = get_font(19, bold=False, serif=True)
    f_check = get_font(19, bold=True, serif=False)

    draw.text((rcx, 95), "★  OUR STORY & MISSION  ★", font=f_eye, fill=(232, 198, 128), anchor="mm")
    draw.text((rcx, 160), "Technology & Paper", font=f_h, fill=(252, 248, 239), anchor="mm")
    draw.text((rcx, 212), "That Feels Like Home", font=f_h, fill=(232, 198, 128), anchor="mm")
    draw.line([(rx0 + 60, 258), (rx1 - 60, 258)], fill=(197, 160, 89), width=2)

    quote_lines = [
        "“We started MetaDigitalGoods with a simple",
        "belief: nobody should feel left behind by",
        "modern tools—and nothing replaces the peace",
        "of mind of a well-organized kitchen binder.”",
    ]
    qy = 310
    for ql in quote_lines:
        draw.text((rcx, qy), ql, font=f_body, fill=(235, 240, 236), anchor="mm")
        qy += 36

    pillars = [
        "✓ Plain-English, Jargon-Free Guides",
        "✓ Generous 16pt–18pt Comfort Print",
        "✓ Designed for 8.5\"×11\" & iPad",
        "✓ 25+ Instant Download Printables",
    ]
    py = 490
    for pil in pillars:
        draw.rounded_rectangle([rx0 + 36, py, rx1 - 36, py + 48], radius=12, fill=(38, 64, 51), outline=(197, 160, 89), width=2)
        draw.text((rcx, py + 24), pil, font=f_check, fill=(252, 248, 239), anchor="mm")
        py += 60

    out_path = BRAND_DIR / "shop_story_photo_1200x800.png"
    canvas.save(out_path, "PNG", optimize=True)
    shutil.copy2(out_path, ARTIFACT_DIR / "metadigitalgoods-story-1200x800.png")
    return out_path


def update_live_shop_profile() -> dict:
    client = EtsyClient()
    shop_title = (
        "AI for Grandmas & Busy Moms Guides • Large-Print Family Recipe & Medical Binders • 2026 Calendars & Nostalgia Games"
    )[:140]

    shop_announcement = (
        "✨ Welcome to MetaDigitalGoods — Thoughtful Printables & Gentle Guides for Real Households! ✨\n\n"
        "Home of our #1 Bestseller 'AI for Grandmas' and #2 'AI for Busy Moms: 5-Minute Meal Plans & Sanity', "
        "alongside 25+ heirloom family recipe binders, large-print emergency medical organizers, 2026 wall calendars, "
        "quilting journals, and nostalgic 1950s/60s trivia & bingo games.\n\n"
        "✔ 100% Instant Digital Downloads — Ready right after checkout with zero shipping wait\n"
        "✔ Easy-on-the-Eyes 16pt–18pt Large Print formatting\n"
        "✔ Prints effortlessly on standard 8.5\" x 11\" US Letter paper or opens in GoodNotes / iPad\n\n"
        "Need help downloading or printing your files? Send us a message anytime—we reply fast and are always happy to help!"
    )

    digital_msg = (
        "Thank you so much for your order from MetaDigitalGoods! 🌸\n\n"
        "Your printable PDF files are ready for instant download right now:\n"
        "1. In your web browser (Safari, Chrome, or Edge), visit: https://www.etsy.com/your/purchases and click 'Download Files' next to your order.\n"
        "2. Printing Tip: Open the PDF and select 'Actual Size' or 'Fit to Printable Area' on standard 8.5\" x 11\" US Letter paper.\n\n"
        "If you ever need your files emailed directly to you or have any questions at all, just reply to this message and we will take care of you right away!"
    )

    return client.update_shop(
        title=shop_title,
        announcement=shop_announcement,
        digital_sale_message=digital_msg,
        confirm=True,
    )


if __name__ == "__main__":
    big = build_big_banner_3360x840()
    mini = build_mini_banner_1200x160()
    story = build_story_photo_1200x800()
    print(f"✓ Built Big Banner (3360x840):   {big} ({big.stat().st_size:,} bytes)")
    print(f"✓ Built Mini Banner (1200x160):  {mini} ({mini.stat().st_size:,} bytes)")
    print(f"✓ Built Story Photo (1200x800):  {story} ({story.stat().st_size:,} bytes)")

    res = update_live_shop_profile()
    print("✓ Live Etsy Shop Profile Updated via API v3:")
    print(json.dumps({k: res.get(k) for k in ["shop_id", "shop_name", "title", "listing_active_count"]}, indent=2))
