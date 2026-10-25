#!/opt/zothos-ai-env/bin/python3
"""Generate & Publish Listings #21–#25 to Live Etsy Shop MetaDigitalGoods (shop_id: 68503004).

Creates:
- Listing #21: AI for Busy Moms — 5-Minute Meal Plans, Family Schedules & Homework Helper Guide PDF
- Listing #22: Grandma's Garden & Perennial Planting Journal, Seed Inventory & Seasonal Bloom Planner PDF
- Listing #23: Cozy Book Club & Reading Journal Printable Bundle, 100-Book Tracker & Discussion Guide PDF
- Listing #24: Holiday Hostess & Christmas Thanksgiving Planner Binder, Menu Timeline & Gift Tracker PDF
- Listing #25: Caregiver's Daily Companion & Senior Care Log, Printable Vitals, Meds & Doctor Notes PDF

Uploads multi-page 8.5x11 (1275x1650) Large-Print PDFs + 2000x2000 Hero Mockup PNG/JPGs,
and activates all 5 listings (`state: "active"`) on Etsy Open API v3.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/home/zoth/NullAITech/etsy-connector/src")
from etsy_connector.client import EtsyClient

BRAND_DIR = Path("/home/zoth/NullAITech/etsy-connector/brand_assets/metadigitalgoods")
PDF_DIR = BRAND_DIR / "pdfs"
MOCKUP_DIR = BRAND_DIR / "mockups"
STUDIO_DIR = Path("/home/zoth/NullAITech/metadigitalgoods/public/assets/studio")
PDF_DIR.mkdir(parents=True, exist_ok=True)
MOCKUP_DIR.mkdir(parents=True, exist_ok=True)


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


def build_multipage_pdf(
    out_path: Path,
    eyebrow: str,
    title_line1: str,
    title_line2: str,
    highlights: list[str],
    sections: list[tuple[str, str, list[str]]],
    accent_rgb: tuple[int, int, int] = (42, 68, 56),
    gold_rgb: tuple[int, int, int] = (197, 160, 89),
) -> Path:
    pw, ph = 1275, 1650
    pages = []

    f_h1 = get_font(48, bold=True, serif=True)
    f_h2 = get_font(32, bold=True, serif=True)
    f_body = get_font(25, bold=False, serif=False)
    f_bold = get_font(26, bold=True, serif=False)
    f_small = get_font(21, bold=False, serif=False)

    # Cover Page
    p1 = Image.new("RGB", (pw, ph), (253, 250, 244))
    d1 = ImageDraw.Draw(p1)
    d1.rectangle([45, 45, pw - 45, ph - 45], outline=accent_rgb, width=6)
    d1.rectangle([60, 60, pw - 60, ph - 60], outline=gold_rgb, width=3)

    d1.text((pw // 2, 185), eyebrow.upper(), font=f_bold, fill=(158, 118, 48), anchor="mm")
    d1.text((pw // 2, 290), title_line1, font=f_h1, fill=accent_rgb, anchor="mm")
    d1.text((pw // 2, 365), title_line2, font=f_h2, fill=(75, 95, 85), anchor="mm")
    d1.line([(180, 425), (pw - 180, 425)], fill=gold_rgb, width=3)

    y = 510
    for h in highlights:
        d1.text((130, y), f"✓  {h}", font=f_body, fill=(38, 46, 42))
        y += 72

    d1.rounded_rectangle([115, 960, pw - 115, 1430], radius=20, fill=(244, 238, 226), outline=gold_rgb, width=3)
    d1.text((pw // 2, 1030), "HOW TO PRINT OR USE ON YOUR TABLET", font=f_h2, fill=accent_rgb, anchor="mm")
    tips = [
        "1. Home Printer: Load standard 8.5\" x 11\" US Letter paper or cardstock.",
        "2. Printer Settings: Choose 'Actual Size' or 'Fit to Printable Area'.",
        "3. iPad / Tablet: Open in GoodNotes, Notability, or Apple Books to write digitally.",
        "4. Unlimited Personal Use: Print fresh worksheet pages anytime you need them!",
    ]
    ty = 1110
    for tip in tips:
        d1.text((155, ty), tip, font=f_small, fill=(55, 65, 60))
        ty += 64

    d1.text((pw // 2, 1545), "© MetaDigitalGoods • Heirloom Printables & Gentle Guides", font=f_small, fill=(120, 130, 125), anchor="mm")
    pages.append(p1)

    # Content & Worksheet Pages
    for sec_title, sec_sub, items in sections:
        p = Image.new("RGB", (pw, ph), (255, 255, 255))
        d = ImageDraw.Draw(p)
        d.rectangle([45, 45, pw - 45, ph - 45], outline=accent_rgb, width=5)
        d.rectangle([60, 60, pw - 60, 195], fill=accent_rgb)
        d.text((pw // 2, 110), sec_title, font=f_h2, fill=(253, 250, 244), anchor="mm")
        d.text((pw // 2, 158), sec_sub, font=f_small, fill=(228, 205, 155), anchor="mm")

        iy = 250
        for item in items:
            d.rounded_rectangle([90, iy, pw - 90, iy + 108], radius=12, fill=(252, 249, 243), outline=(215, 205, 185), width=2)
            d.text((118, iy + 32), item, font=f_bold, fill=(32, 42, 38))
            d.line([(118, iy + 84), (pw - 118, iy + 84)], fill=(195, 190, 180), width=2)
            iy += 126
            if iy > 1440:
                break

        d.text((pw // 2, 1555), "MetaDigitalGoods • Print Unlimited Copies for Your Household", font=f_small, fill=(130, 140, 135), anchor="mm")
        pages.append(p)

    pages[0].save(out_path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    return out_path


def build_hero_mockup(
    out_path: Path,
    badge_text: str,
    title_lines: list[str],
    subtitle: str,
    bullets: list[str],
    accent_rgb: tuple[int, int, int] = (42, 68, 56),
    gold_rgb: tuple[int, int, int] = (197, 160, 89),
) -> Path:
    w, h = 2000, 2000
    img = Image.new("RGB", (w, h), (247, 242, 232))
    draw = ImageDraw.Draw(img)

    # Top banner bar
    draw.rectangle([0, 0, w, 190], fill=accent_rgb)
    f_badge = get_font(42, bold=True, serif=False)
    draw.text((w // 2, 95), f"★  {badge_text.upper()}  ★", font=f_badge, fill=(248, 232, 188), anchor="mm")

    # Outer gold frame
    draw.rectangle([48, 235, w - 48, h - 48], outline=gold_rgb, width=6)

    # Left page preview card (shadow + white sheet)
    draw.rounded_rectangle([125, 340, 1065, 1620], radius=24, fill=(215, 208, 195))
    draw.rounded_rectangle([105, 320, 1045, 1600], radius=24, fill=(255, 255, 255), outline=accent_rgb, width=5)
    draw.rectangle([135, 350, 1015, 510], fill=accent_rgb)

    f_card_h = get_font(44, bold=True, serif=True)
    f_card_sub = get_font(28, bold=False, serif=False)
    f_card_line = get_font(30, bold=True, serif=False)

    draw.text((575, 410), title_lines[0], font=f_card_h, fill=(255, 252, 245), anchor="mm")
    draw.text((575, 468), title_lines[1] if len(title_lines) > 1 else subtitle, font=f_card_sub, fill=(235, 205, 140), anchor="mm")

    cy = 580
    for idx, b in enumerate(bullets, 1):
        draw.rounded_rectangle([155, cy, 995, cy + 150], radius=16, fill=(252, 249, 242), outline=gold_rgb, width=3)
        draw.text((190, cy + 50), f"0{idx}. {b}", font=f_card_line, fill=(35, 48, 42))
        draw.line([(190, cy + 112), (960, cy + 112)], fill=(205, 198, 185), width=2)
        cy += 185

    # Right marketing panel
    rx = 1110
    f_r_title = get_font(62, bold=True, serif=True)
    f_r_sub = get_font(36, bold=False, serif=False)
    f_r_Check = get_font(34, bold=True, serif=False)

    ty = 390
    for tl in title_lines:
        draw.text((rx, ty), tl, font=f_r_title, fill=accent_rgb)
        ty += 82

    draw.text((rx, ty + 20), subtitle, font=f_r_sub, fill=(145, 108, 42))
    draw.line([(rx, ty + 85), (w - 100, ty + 85)], fill=gold_rgb, width=4)

    by = ty + 135
    for b in bullets + ["Easy 18pt+ Comfort Print", "Prints on 8.5\" x 11\" Paper", "Instant PDF Download"]:
        draw.rounded_rectangle([rx, by, w - 95, by + 92], radius=18, fill=(255, 255, 255), outline=(210, 200, 180), width=2)
        draw.text((rx + 30, by + 46), f"✓  {b}", font=f_r_Check, fill=(35, 52, 44), anchor="lm")
        by += 114

    # Bottom callout pill
    draw.rounded_rectangle([105, 1690, w - 95, 1890], radius=28, fill=accent_rgb, outline=gold_rgb, width=4)
    f_bot = get_font(46, bold=True, serif=True)
    draw.text((w // 2, 1790), "INSTANT DIGITAL DOWNLOAD  •  PRINT AT HOME OR USE ON IPAD", font=f_bot, fill=(253, 250, 244), anchor="mm")

    img.save(out_path, "PNG")
    return out_path


NEW_LISTINGS = [
    {
        "slug": "ai-for-busy-moms",
        "pdf_name": "21_AI_For_Busy_Moms_Family_And_Home_Guide.pdf",
        "images": [
            str(STUDIO_DIR / "cat_ai_moms.jpg"),
            str(STUDIO_DIR / "prod_ai_moms.jpg"),
        ],
        "title": "AI for Busy Moms Printable Book & 5-Minute Meal Planner, Family Schedule, Grocery List and Homework Helper Prompts PDF",
        "price": 7.99,
        "tags": [
            "ai for busy moms",
            "mom meal planner",
            "family binder pdf",
            "chatgpt guide moms",
            "weekly dinner menu",
            "grocery list pdf",
            "homework helper",
            "working mom gift",
            "household organizer",
            "chore chart pdf",
            "mom life planner",
            "kitchen binder pdf",
            "instant download",
        ],
        "description": (
            "Reclaim 5+ hours every single week with 'AI for Busy Moms: 5-Minute Meal Plans, Schedules & Sanity'!\n\n"
            "Thoughtfully designed for busy moms, working parents, and homemakers, this warm, jargon-free printable book gives you 50+ copy-and-paste prompts and printable worksheets that turn everyday chaos into calm in seconds.\n\n"
            "✨ WHAT IS INCLUDED IN YOUR INSTANT DOWNLOAD PDF:\n"
            "• Section 1: The 5-Minute Weekly Family Dinner & Aisle-by-Aisle Grocery List Generator\n"
            "• Section 2: Fridge Leftover Rescue (Turn 4 Random Ingredients into a 20-Minute Kid-Approved Dinner)\n"
            "• Section 3: Tear-Free Homework Helper (Explain Fractions, Science & Spelling in Fun Kid Language)\n"
            "• Section 4: Family Chore Charts, Birthday Party Checklists & Polite Teacher Emails\n"
            "• Printable Weekly Refrigerator Dinner Menu & Grocery Tear-Off Sheet\n\n"
            "🖨️ EASY TO PRINT OR USE ON IPAD:\n"
            "• Formatted for standard 8.5\" x 11\" US Letter paper\n"
            "• Works in GoodNotes, Notability, or Apple Books on iPad\n"
            "• Instant digital download right after checkout — no waiting for shipping!"
        ),
        "pdf_spec": {
            "eyebrow": "MetaDigitalGoods • Busy Mom Edition",
            "t1": "AI for Busy Moms",
            "t2": "5-Minute Meal Plans, Family Schedules & Sanity Guide",
            "highlights": [
                "50+ Copy-and-Paste Mom Prompts for ChatGPT & Claude",
                "5-Minute Weekly Family Dinner & Aisle-by-Aisle Grocery Lists",
                "Fridge Leftover Rescue: 20-Minute Weeknight Dinner Builder",
                "Tear-Free Homework Explainer for Elementary & Middle School",
                "Printable Weekly Refrigerator Menu, Chore Chart & Party Checklist",
            ],
            "sections": [
                (
                    "SECTION 1: 5-MINUTE MEAL & GROCERY PROMPTS",
                    "Copy & paste these exact prompts to plan a whole week of dinners in 60 seconds",
                    [
                        "Prompt 1: 'Plan 5 kid-friendly 30-minute dinners under $85 with an aisle-by-aisle grocery list.'",
                        "Prompt 2: 'I have chicken breast, broccoli, rice, and cheddar—give me 3 20-minute skillet dinners.'",
                        "Prompt 3: 'Create a 5-day high-protein school lunchbox plan with nut-free snacks.'",
                        "Prompt 4: 'Build a Sunday 1-hour meal prep checklist for busy soccer & dance nights.'",
                        "Prompt 5: 'Give me 5 slow-cooker dump-and-go recipes using pantry staples.'",
                    ],
                ),
                (
                    "SECTION 2: TEAR-FREE HOMEWORK & SCHOOL HELPER",
                    "Turn tricky homework and school emails into stress-free wins",
                    [
                        "Prompt 6: 'Explain multiplying fractions to my 9-year-old using pizza slices and a 3-step game.'",
                        "Prompt 7: 'Create a 10-word spelling practice story about dinosaurs using these vocabulary words.'",
                        "Prompt 8: 'Write a warm, polite email to my child's teacher asking for extra reading tips.'",
                        "Prompt 9: 'Give us 3 rainy-day kitchen science experiments using baking soda, vinegar, and food coloring.'",
                        "Prompt 10: 'Create a 15-minute after-school routine chart so homework gets done before screen time.'",
                    ],
                ),
                (
                    "SECTION 3: WEEKLY REFRIGERATOR MENU & GROCERY LOG",
                    "Print unlimited copies for your kitchen counter or refrigerator door",
                    [
                        "MONDAY DINNER: ____________________________________   Prep Time: ______",
                        "TUESDAY DINNER: ___________________________________   Prep Time: ______",
                        "WEDNESDAY DINNER: _________________________________   Prep Time: ______",
                        "THURSDAY DINNER: __________________________________   Prep Time: ______",
                        "FRIDAY FAMILY NIGHT: ______________________________   Prep Time: ______",
                        "TOP GROCERY STAPLES NEEDED: ___________________________________________",
                    ],
                ),
                (
                    "SECTION 4: FAMILY CHORE & MORNING ROUTINE CHART",
                    "Check off daily wins together — simple, encouraging, and clutter-free",
                    [
                        "MORNING: Make Bed & Brush Teeth  [ M ]  [ T ]  [ W ]  [ Th ]  [ F ]",
                        "MORNING: Pack Backpack & Water Bottle  [ M ]  [ T ]  [ W ]  [ Th ]  [ F ]",
                        "AFTER SCHOOL: Shoes & Coat in Cubby  [ M ]  [ T ]  [ W ]  [ Th ]  [ F ]",
                        "AFTER SCHOOL: 20 Minutes Reading / Homework  [ M ]  [ T ]  [ W ]  [ Th ]  [ F ]",
                        "EVENING: Help Clear Dinner Plates  [ M ]  [ T ]  [ W ]  [ Th ]  [ F ]",
                        "WEEKEND REWARD / FAMILY ACTIVITY: _____________________________________",
                    ],
                ),
            ],
        },
    },
    {
        "slug": "grandmas-garden-planting-journal",
        "pdf_name": "22_Grandmas_Garden_And_Perennial_Planting_Journal.pdf",
        "mockup_name": "Listing_22_Grandmas_Garden_Journal_Mockup.png",
        "title": "Grandma's Garden & Perennial Planting Journal, Large Print Seed Inventory, Seasonal Bloom Calendar and Yard Planner Binder PDF",
        "price": 6.99,
        "tags": [
            "garden journal pdf",
            "planting planner",
            "grandmas garden",
            "seed inventory log",
            "perennial tracker",
            "gardener gift pdf",
            "flower bed planner",
            "vegetable logbook",
            "large print binder",
            "botanical journal",
            "spring garden log",
            "yard layout grid",
            "printable garden",
        ],
        "description": (
            "Celebrate every bloom, harvest, and heirloom seed with 'Grandma's Garden & Perennial Planting Journal'!\n\n"
            "Designed in easy-on-the-eyes 18pt+ Large Print, this printable gardening binder helps you track what you planted, where it grows best, sun & watering needs, and seasonal garden memories.\n\n"
            "🌸 WHAT IS INCLUDED IN YOUR INSTANT DOWNLOAD PDF:\n"
            "• Seasonal Spring, Summer, Autumn & Winter Garden Checklist\n"
            "• Flower Bed & Raised Vegetable Bed Layout Grid\n"
            "• Seed Packet & Perennial Bulb Inventory Tracker\n"
            "• Plant Care Profile Sheet (Sun, Soil, Watering & Pruning Notes)\n"
            "• 'From Grandma's Garden' Pass-Along Plant & Cutting Gift Tags\n\n"
            "🖨️ Prints effortlessly at home on standard 8.5\" x 11\" US Letter paper!"
        ),
        "mockup_spec": {
            "badge": "Large-Print Heirloom Gardening Binder",
            "lines": ["Grandma's Garden", "Planting & Seed Journal"],
            "sub": "Seasonal Bloom Tracker, Bed Layouts & Seed Packet Log",
            "bullets": [
                "Raised Bed & Flower Border Grid",
                "Seed Packet & Bulb Inventory Log",
                "Perennial Sun, Soil & Pruning Tracker",
                "Seasonal Spring-to-Fall Checklists",
            ],
            "accent": (42, 68, 56),
        },
        "pdf_spec": {
            "eyebrow": "MetaDigitalGoods • Heirloom Garden Series",
            "t1": "Grandma's Garden Journal",
            "t2": "Perennial Planting Log, Seed Inventory & Seasonal Bloom Planner",
            "highlights": [
                "Easy-to-Read 18pt+ Large Print Formatting for Comfortable Writing",
                "Seasonal Spring, Summer, Fall & Winter Garden Task Checklists",
                "Seed Packet, Bulb & Perennial Division Inventory Ledger",
                "Flower Bed & Vegetable Patch Sun/Shade Layout Planner",
                "Pass-Along Plant History & 'Grown With Love' Notes",
            ],
            "sections": [
                (
                    "PAGE 1: SEED PACKET & BULB INVENTORY LOG",
                    "Keep track of varieties, planting dates, days to sprout, and favorite sources",
                    [
                        "1. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                        "2. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                        "3. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                        "4. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                        "5. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                        "6. Variety / Flower Name: ______________________  Sun: [Full] [Part] [Shade]  Planted: _______",
                    ],
                ),
                (
                    "PAGE 2: PERENNIAL BLOOM & CARE PROFILE",
                    "Record what thrived, when it bloomed, and fertilizer or pruning reminders",
                    [
                        "Bed / Location (e.g., Front Porch Border): ________________________________________",
                        "Spring Blooms (March–May): ____________________________________________________",
                        "Summer Blooms (June–August): __________________________________________________",
                        "Autumn Color (Sept–Nov): ______________________________________________________",
                        "Mulch, Compost & Feeding Notes: _______________________________________________",
                        "Plants to Divide or Share Next Season: ________________________________________",
                    ],
                ),
                (
                    "PAGE 3: SEASONAL GARDEN CHECKLIST",
                    "Check off essential tasks across all four seasons",
                    [
                        "[  ] Early Spring: Clean pruners, test soil, start sweet peas & tomatoes indoors",
                        "[  ] Late Spring: Mulch perennial beds, plant dahlias & zinnias after last frost",
                        "[  ] Summer: Deadhead roses & cosmos, deep-water morning roots, harvest herbs",
                        "[  ] Autumn: Plant tulip & daffodil bulbs, save heirloom seeds, rake leaf mulch",
                        "[  ] Winter: Sketch next year's flower beds & browse seed catalogs with warm tea",
                    ],
                ),
            ],
        },
    },
    {
        "slug": "cozy-book-club-reading-journal",
        "pdf_name": "23_Cozy_Book_Club_And_Reading_Journal_Bundle.pdf",
        "mockup_name": "Listing_23_Book_Club_Reading_Journal_Mockup.png",
        "title": "Cozy Book Club & Reading Journal Printable Bundle, Large Print 100-Book Tracker, Discussion Questions and Favorite Quotes PDF",
        "price": 5.99,
        "tags": [
            "reading journal pdf",
            "book club kit",
            "book tracker pdf",
            "book lover gift",
            "printable book log",
            "reading list binder",
            "book review sheet",
            "library tracker",
            "large print journal",
            "cottagecore book",
            "ladies book club",
            "bookshelf tracker",
            "instant download",
        ],
        "description": (
            "Remember every story you loved with the 'Cozy Book Club & Reading Journal Printable Bundle'!\n\n"
            "Crafted for avid readers, library lovers, and neighborhood book clubs, this warm large-print printable journal makes it a joy to log your favorite books, memorable quotes, star ratings, and lively book club conversations.\n\n"
            "📚 WHAT IS INCLUDED IN YOUR INSTANT DOWNLOAD PDF:\n"
            "• Full-Page Book Review & Reflection Sheet (Plot, Characters, Favorite Quotes & 5-Star Rating)\n"
            "• 100-Book Reading Challenge & Library Hold Tracker\n"
            "• 15 Universal Book Club Discussion Questions (Guaranteed Great Conversation!)\n"
            "• 'Books Recommended by Friends' & Lending Library Log\n\n"
            "🖨️ Ready to print on standard 8.5\" x 11\" US Letter paper or use digitally on your iPad!"
        ),
        "mockup_spec": {
            "badge": "For Book Lovers & Ladies' Book Clubs",
            "lines": ["Cozy Book Club &", "Reading Journal Bundle"],
            "sub": "Book Reviews, Library Hold Log & 15 Discussion Prompts",
            "bullets": [
                "Full-Page Book Review & Quote Log",
                "15 Universal Book Club Questions",
                "Library Hold & Friend Recommendations",
                "Books Loaned Out Tracker Sheet",
            ],
            "accent": (58, 45, 72),
        },
        "pdf_spec": {
            "eyebrow": "MetaDigitalGoods • Literary Keepsake Series",
            "t1": "Cozy Reading & Book Club Journal",
            "t2": "Large-Print Book Reviews, Favorite Quotes & Discussion Guide",
            "highlights": [
                "Spacious Large-Print Book Review & Star Rating Pages",
                "15 Thought-Provoking Book Club Discussion Questions",
                "To-Be-Read (TBR) & Library Hold Request Tracker",
                "'Books I Loaned Out' Log So Favorite Hardcovers Always Come Home",
                "Favorite Literary Quotes & Memorable Passages Collector",
            ],
            "sections": [
                (
                    "PAGE 1: BOOK REVIEW & REFLECTION LOG",
                    "Capture your thoughts while the story is still fresh in your heart",
                    [
                        "Book Title: ___________________________________________________________________",
                        "Author: ____________________________________   Rating:  ☆  ☆  ☆  ☆  ☆",
                        "Date Started: ______________   Date Finished: ______________   Format: [Print] [Audio] [eBook]",
                        "My Favorite Character & Why: __________________________________________________",
                        "Memorable Quote or Scene: _____________________________________________________",
                        "Would I Recommend This Book? To Whom?: ________________________________________",
                    ],
                ),
                (
                    "PAGE 2: 15 UNIVERSAL BOOK CLUB QUESTIONS",
                    "Spark warm, lively conversation at your next book club gathering",
                    [
                        "1. Which character would you most like to invite over for coffee or dinner?",
                        "2. Did the opening chapter hook you right away, or did the story grow on you?",
                        "3. What setting or time period detail felt most vivid and memorable?",
                        "4. Was there a decision a character made that you strongly agreed or disagreed with?",
                        "5. How did you feel about the ending? Would you change the final chapter?",
                        "6. If this book were made into a film, who would you cast in the lead roles?",
                    ],
                ),
                (
                    "PAGE 3: BOOKS TO READ & LIBRARY HOLD TRACKER",
                    "Never forget a great book recommendation from a friend again",
                    [
                        "1. Title & Author: ___________________________________  Recommended By: ____________",
                        "2. Title & Author: ___________________________________  Recommended By: ____________",
                        "3. Title & Author: ___________________________________  Recommended By: ____________",
                        "4. Title & Author: ___________________________________  Recommended By: ____________",
                        "5. Title & Author: ___________________________________  Recommended By: ____________",
                        "6. Title & Author: ___________________________________  Recommended By: ____________",
                    ],
                ),
            ],
        },
    },
    {
        "slug": "holiday-hostess-menu-planner",
        "pdf_name": "24_Holiday_Hostess_And_Family_Feast_Planner_Binder.pdf",
        "mockup_name": "Listing_24_Holiday_Hostess_Planner_Mockup.png",
        "title": "Holiday Hostess & Thanksgiving Christmas Planner Binder, Printable Oven Schedule, Feast Menu, Gift Budget and Guest List PDF",
        "price": 7.99,
        "tags": [
            "holiday planner pdf",
            "christmas binder",
            "thanksgiving menu",
            "hostess planner",
            "oven schedule pdf",
            "gift budget tracker",
            "christmas card log",
            "family dinner plan",
            "potluck sign up",
            "holiday baking log",
            "large print planner",
            "christmas organizer",
            "instant download",
        ],
        "description": (
            "Host peaceful, joyful family holidays without last-minute kitchen stress with the 'Holiday Hostess & Family Feast Planner Binder'!\n\n"
            "Whether you are hosting Thanksgiving dinner, Christmas morning brunch, or a festive church potluck, this large-print printable binder coordinates your oven schedule, grocery list, gift budget, and guest contributions in one place.\n\n"
            "🎄 WHAT IS INCLUDED IN YOUR INSTANT DOWNLOAD PDF:\n"
            "• Holiday Feast Master Menu & Who-Brings-What Potluck Sheet\n"
            "• Hour-by-Hour Oven & Stovetop Countdown Timer Schedule\n"
            "• Christmas & Holiday Gift List + Stocking Stuffer Budget Tracker\n"
            "• Holiday Greeting Card Address & Mailing Checklist\n\n"
            "🖨️ Prints on standard 8.5\" x 11\" US Letter paper — reuse it year after year!"
        ),
        "mockup_spec": {
            "badge": "Stress-Free Thanksgiving & Christmas Hosting",
            "lines": ["Holiday Hostess &", "Family Feast Planner"],
            "sub": "Oven Schedule, Feast Menu, Potluck Log & Gift Tracker",
            "bullets": [
                "Hour-by-Hour Oven & Burner Schedule",
                "Feast Menu & Who-Brings-What Sheet",
                "Holiday Gift & Stocking Budget Log",
                "Greeting Card Mailing Checklist",
            ],
            "accent": (118, 38, 42),
        },
        "pdf_spec": {
            "eyebrow": "MetaDigitalGoods • Peaceful Hosting Series",
            "t1": "Holiday Hostess & Feast Planner",
            "t2": "Oven Countdown Timeline, Family Menu, Potluck & Gift Organizer",
            "highlights": [
                "Hour-by-Hour Oven & Stovetop Schedule So Every Dish Finishes Warm",
                "Holiday Feast Menu & 'Who Is Bringing What' Guest Potluck Sheet",
                "Aisle-by-Aisle Holiday Grocery & Make-Ahead Prep Checklist",
                "Thoughtful Gift Tracker & Stocking Stuffer Budget Sheet",
                "Annual Holiday Card Address & Sent Checklist",
            ],
            "sections": [
                (
                    "PAGE 1: HOLIDAY FEAST MENU & GUEST POTLUCK LOG",
                    "Coordinate your main dish, sides, rolls, and desserts with ease",
                    [
                        "MAIN DISH / ROAST: ______________________________   Oven Temp & Time: __________",
                        "SIDE DISH 1: ____________________________________   Brought By: ________________",
                        "SIDE DISH 2: ____________________________________   Brought By: ________________",
                        "SIDE DISH 3: ____________________________________   Brought By: ________________",
                        "BREAD / ROLLS: __________________________________   Brought By: ________________",
                        "PIES & DESSERTS: ________________________________   Brought By: ________________",
                    ],
                ),
                (
                    "PAGE 2: HOUR-BY-HOUR OVEN & KITCHEN COUNTDOWN",
                    "Work backward from dinner time so nothing burns or gets forgotten in the fridge",
                    [
                        "2 DAYS BEFORE: Thaw roast/turkey, bake pies, set table linens & serving platters",
                        "1 DAY BEFORE: Chop celery/onions/herbs, assemble casseroles, chill beverages",
                        "4 HOURS BEFORE MEAL: Preheat oven, start main roast, set out appetizers",
                        "2 HOURS BEFORE MEAL: Prep potatoes & side dishes ready for oven",
                        "45 MINUTES BEFORE MEAL: Rest roast under foil, bake side casseroles & rolls",
                        "MEALTIME: Warm gravy, light candles, gather family & give thanks!",
                    ],
                ),
                (
                    "PAGE 3: HOLIDAY GIFT & THOUGHTFUL BUDGET TRACKER",
                    "Keep track of gift ideas, wrapping status, and shipping deadlines",
                    [
                        "1. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                        "2. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                        "3. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                        "4. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                        "5. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                        "6. Recipient: ___________________  Gift Idea: ________________________  [Bought] [Wrapped]",
                    ],
                ),
            ],
        },
    },
    {
        "slug": "caregivers-daily-companion-log",
        "pdf_name": "25_Caregivers_Daily_Companion_And_Senior_Care_Log.pdf",
        "mockup_name": "Listing_25_Caregivers_Daily_Companion_Mockup.png",
        "title": "Caregiver's Daily Companion & Senior Care Log Binder, Large Print Medication Schedule, Blood Pressure Vitals and Doctor Notes PDF",
        "price": 7.99,
        "tags": [
            "caregiver binder",
            "senior care log pdf",
            "medication tracker",
            "blood pressure log",
            "doctor visit notes",
            "elderly care planner",
            "daily vitals sheet",
            "hospital recovery",
            "large print medical",
            "home health binder",
            "family caregiver",
            "nursing shift log",
            "instant download",
        ],
        "description": (
            "Bring clarity, calm, and seamless communication to family caregiving with the 'Caregiver's Daily Companion & Senior Care Log Binder'!\n\n"
            "Designed for adult children caring for aging parents, spouses, and home health aides, these crystal-clear 18pt+ Large Print sheets keep daily medications, blood pressure readings, doctor questions, and shift handoff notes organized on the kitchen counter.\n\n"
            "💙 WHAT IS INCLUDED IN YOUR INSTANT DOWNLOAD PDF:\n"
            "• Daily Caregiver Shift Log (Morning, Afternoon, Evening & Overnight Checkboxes)\n"
            "• Blood Pressure, Pulse, Blood Sugar & Weight Vitals Tracker\n"
            "• Doctor Appointment Questions & Post-Visit Instructions Sheet\n"
            "• Daily Hydration, Meals, Mobility & Mood Log\n\n"
            "🖨️ Print unlimited copies at home on standard 8.5\" x 11\" US Letter paper!"
        ),
        "mockup_spec": {
            "badge": "Essential for Family Caregivers & Seniors",
            "lines": ["Caregiver's Daily", "Companion & Care Log"],
            "sub": "Large-Print Meds Checklists, Vitals Log & Doctor Notes",
            "bullets": [
                "Daily Morning / Noon / Night Med Check",
                "Blood Pressure & Vitals Ledger",
                "Doctor Visit Questions & Summary",
                "Family & Aide Shift Handoff Notes",
            ],
            "accent": (32, 62, 82),
        },
        "pdf_spec": {
            "eyebrow": "MetaDigitalGoods • Peace-of-Mind Care Series",
            "t1": "Caregiver's Daily Companion",
            "t2": "Large-Print Medication Checklists, Vitals Tracker & Doctor Visit Log",
            "highlights": [
                "Extra-Clear 18pt+ Large Print Designed for Countertop Clipboards",
                "Morning, Noon, Evening & Bedtime Medication Check-Off Grid",
                "Blood Pressure, Heart Rate, Temperature & Blood Sugar Log",
                "Doctor Appointment Question Prep & Care Plan Summary Sheet",
                "Daily Meals, Water Intake, Mobility & Caregiver Handoff Notes",
            ],
            "sections": [
                (
                    "PAGE 1: DAILY CAREGIVER & MEDICATION CHECKLIST",
                    "Keep on the kitchen counter so every family member or aide stays on the same page",
                    [
                        "Date: ________________________   Caregiver on Duty: ____________________________",
                        "MORNING MEDS GIVEN:  [  ] Yes   Time: ________   Breakfast & Water: ____________",
                        "MIDDAY MEDS GIVEN:   [  ] Yes   Time: ________   Lunch & Walk/Rest: ____________",
                        "EVENING MEDS GIVEN:  [  ] Yes   Time: ________   Dinner & Fluids: ______________",
                        "BEDTIME MEDS GIVEN:  [  ] Yes   Time: ________   Sleep & Comfort Notes: ________",
                        "IMPORTANT NOTES FOR NEXT CAREGIVER: ___________________________________________",
                    ],
                ),
                (
                    "PAGE 2: BLOOD PRESSURE & DAILY VITALS TRACKER",
                    "Bring this sheet to doctor appointments for an instant health snapshot",
                    [
                        "1. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                        "2. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                        "3. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                        "4. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                        "5. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                        "6. Date/Time: ____________  BP: ____ / ____  Pulse: _____  Temp/Sugar: _____  Notes: ______",
                    ],
                ),
                (
                    "PAGE 3: DOCTOR VISIT QUESTIONS & CARE SUMMARY",
                    "Write down questions before the appointment and record the doctor's exact advice",
                    [
                        "Doctor / Specialist Name: ___________________________   Visit Date: ____________",
                        "Top 3 Questions to Ask Today: _________________________________________________",
                        "New Symptoms or Medication Side Effects to Mention: ___________________________",
                        "Doctor's Instructions & Prescription Changes: _________________________________",
                        "Next Follow-Up Appointment Date & Lab Tests Needed: ___________________________",
                    ],
                ),
            ],
        },
    },
]


def main() -> None:
    client = EtsyClient()
    live_json_path = BRAND_DIR / "live_listings.json"
    existing_listings = []
    if live_json_path.exists():
        existing_listings = json.loads(live_json_path.read_text(encoding="utf-8"))
    existing_slugs = {item["slug"]: item for item in existing_listings}

    for item in NEW_LISTINGS:
        slug = item["slug"]
        pdf_path = PDF_DIR / item["pdf_name"]
        ps = item["pdf_spec"]
        build_multipage_pdf(
            out_path=pdf_path,
            eyebrow=ps["eyebrow"],
            title_line1=ps["t1"],
            title_line2=ps["t2"],
            highlights=ps["highlights"],
            sections=ps["sections"],
        )
        print(f"✓ Built multi-page PDF: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")

        image_paths = list(item.get("images", []))
        if "mockup_spec" in item:
            ms = item["mockup_spec"]
            m_path = MOCKUP_DIR / item["mockup_name"]
            build_hero_mockup(
                out_path=m_path,
                badge_text=ms["badge"],
                title_lines=ms["lines"],
                subtitle=ms["sub"],
                bullets=ms["bullets"],
                accent_rgb=ms["accent"],
            )
            image_paths.append(str(m_path))
            print(f"✓ Built 2000x2000 Hero Mockup: {m_path.name} ({m_path.stat().st_size:,} bytes)")

        if slug in existing_slugs:
            print(f"• {slug} already in live_listings.json ({existing_slugs[slug]['listing_id']}), skipping draft creation.")
            continue

        # 1. Create Draft Listing on Etsy
        time.sleep(0.6)
        draft_res = client.create_draft_listing(
            title=item["title"],
            description=item["description"],
            price=item["price"],
            tags=item["tags"],
            listing_type="download",
            confirm=True,
        )
        lid = str(draft_res["listing_id"])
        print(f"  → Created Etsy draft listing {lid} for '{slug}'")

        # 2. Upload Images
        for rank_idx, img_p in enumerate(image_paths, 1):
            if os.path.exists(img_p):
                time.sleep(0.6)
                img_res = client.upload_listing_image(
                    listing_id=lid,
                    image_path=img_p,
                    rank=rank_idx,
                    alt_text=item["title"][:240],
                )
                print(f"  → Uploaded image rank {rank_idx} (image_id={img_res.get('listing_image_id')})")

        # 3. Upload Printable PDF File
        time.sleep(0.6)
        file_res = client.upload_listing_file(
            listing_id=lid,
            file_path=str(pdf_path),
            name=pdf_path.name,
            rank=1,
        )
        print(f"  → Uploaded digital PDF '{pdf_path.name}' (file_id={file_res.get('listing_file_id')})")

        # 4. Activate Listing (`state: "active"`)
        time.sleep(0.6)
        act_res = client._request(
            f"/shops/{client.shop_id}/listings/{lid}",
            method="PATCH",
            payload={"state": "active"},
        )
        print(f"  ★ ACTIVATED Listing {lid} -> state={act_res.get('state')} (https://www.etsy.com/listing/{lid})")

        entry = {
            "slug": slug,
            "listing_id": lid,
            "title": item["title"],
            "price": item["price"],
            "etsy_url": f"https://www.etsy.com/listing/{lid}",
            "shop_manager_url": f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}",
        }
        existing_listings.append(entry)
        live_json_path.write_text(json.dumps(existing_listings, indent=2), encoding="utf-8")

    time.sleep(0.6)
    shop = client.get_shop()
    print(f"\n🎉 FINAL LIVE ETSY SHOP STATUS ({shop.get('shop_name')}):")
    print(f"   Active Listings:  {shop.get('listing_active_count')}")
    print(f"   Digital Listings: {shop.get('digital_listing_count')}")


if __name__ == "__main__":
    main()
