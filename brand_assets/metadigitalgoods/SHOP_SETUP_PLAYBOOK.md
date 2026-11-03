# MetaDigitalGoods — Etsy Storefront Setup & Automation Playbook

## 1. Generated Brand Assets & First Product Pack
All files are located in `~/NullAITech/etsy-connector/brand_assets/metadigitalgoods/`:
- **Shop Icon (500x500 px)**: `shop_icon_500x500.png`
- **Big Shop Banner (3360x840 px)**: `shop_banner_big_3360x840.png`
- **Mini Shop Banner (1200x160 px)**: `shop_banner_mini_1200x160.png`
- **Listing #1 Digital Download PDF (8 Pages, Large Print)**: `Listing_1_Golden_Era_Trivia_Bingo_Pack.pdf`
- **Listing #1 Hero Thumbnail Mockup (2000x2000 px)**: `Listing_1_Hero_Mockup_2000x2000.png`

---

## 2. Ready-to-Paste Shop Copy (Or Push via Terminal `shop-update`)

### Shop Title (Tagline — 118/140 chars)
```text
Easy-to-Read Large Print Party Games, Family Health & Recipe Binders, Quilting Planners & Heirloom Home Printables
```

### Shop Announcement
```text
✨ Welcome to MetaDigitalGoods! ✨
We craft thoughtful, easy-to-read Large-Print Printable Games, Family & Medical Organizer Binders, Heirloom Recipe Cards, and Cozy Craft Planners designed to print effortlessly at home on standard 8.5" x 11" US Letter paper.

✔ 100% Instant Digital Downloads — No waiting for shipping!
✔ Easy-on-the-Eyes Large Print formatting
✔ Print unlimited copies at home, your local library, or Staples/OfficeMax

Need help downloading or printing your files? Send us a message anytime—we're always happy to help!
```

### Digital Message to Buyers (Sent automatically on every order)
```text
Thank you so much for your order from MetaDigitalGoods! 🌸

Your printable files are ready for instant download right now:
1. Using a Computer/Tablet Browser (Recommended): Visit www.etsy.com/your/purchases and click "Download Files" next to your order. (Note: The Etsy mobile app does not support downloading digital files directly—please use Safari, Chrome, or Edge).
2. Printing Tip: Open the PDF file and select "Actual Size" or "Fit to Printable Area" on standard 8.5" x 11" US Letter paper.

If you ever need your files emailed directly to you or have any questions at all, just reply to this message and we will take care of you right away!
```

---

## 3. Terminal Commands (`etsy-connector`)

### Step A: Save Your Etsy API Key & Connect OAuth2
```bash
cd ~/NullAITech/etsy-connector

# 1. Generate the OAuth2 PKCE link using your Keystring from developers.etsy.com:
./bin/etsy-connector auth --key <YOUR_ETSY_API_KEYSTRING>

# 2. Save your API Key, OAuth Access Token, and Shop Name:
./bin/etsy-connector config --key <YOUR_ETSY_API_KEYSTRING> --token <YOUR_OAUTH_TOKEN> --shop metadigitalgoods
```

### Step B: Push Your Shop Title, Announcement & Buyer Message from Terminal
```bash
./bin/etsy-connector shop-update \
  --title "Easy-to-Read Large Print Party Games, Family Health & Recipe Binders, Quilting Planners & Heirloom Home Printables" \
  --announcement "Welcome to MetaDigitalGoods! We craft thoughtful, easy-to-read Large-Print Printable Games, Family & Medical Organizer Binders, Heirloom Recipe Cards, and Cozy Craft Planners designed to print effortlessly at home on standard 8.5x11 US Letter paper." \
  --digital-msg "Thank you so much for your order from MetaDigitalGoods! Visit www.etsy.com/your/purchases in your web browser to download your printable PDF files." \
  --confirm
```

### Step C: Create & Upload Listing #1 (Draft + Mockup Image + Printable PDF) from Terminal
```bash
./bin/etsy-connector draft-digital \
  --title "1950s & 1960s Golden Era Trivia and Bingo Printable Bundle | Large Print Senior Party Games | Nostalgic Family Reunion Activity PDF" \
  --price 6.99 \
  --tags "50s 60s trivia game,large print bingo,senior party games,golden era trivia,printable bingo pdf,retirement party,church social games,family reunion game,nostalgia game pack,senior activity pdf,1950s party game,1960s music bingo,ladies tea party" \
  --desc "Enjoy a heartwarming trip down memory lane with the 1950s & 1960s Golden Era Trivia and Bingo Printable Bundle! Designed with easy-on-the-eyes 18pt+ Large Print that prints effortlessly at home on standard 8.5x11 US Letter paper. Includes 20 nostalgic trivia questions, full host answer key, and unique Large-Print Bingo cards. Instant digital download PDF." \
  --image ~/NullAITech/etsy-connector/brand_assets/metadigitalgoods/Listing_1_Hero_Mockup_2000x2000.png \
  --file ~/NullAITech/etsy-connector/brand_assets/metadigitalgoods/Listing_1_Golden_Era_Trivia_Bingo_Pack.pdf \
  --confirm
```
