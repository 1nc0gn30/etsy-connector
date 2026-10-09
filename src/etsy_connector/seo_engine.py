"""Etsy SEO Algorithm Auditor & Financial Profitability Engine.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def audit_title(title: str) -> Dict[str, Any]:
    """Audit Etsy listing title against search algorithm ranking factors."""
    clean_title = (title or "").strip()
    char_len = len(clean_title)
    words = clean_title.split()
    word_count = len(words)

    issues: List[str] = []
    recommendations: List[str] = []
    score = 100

    # Rule 1: Character length (Max 140 chars)
    if char_len == 0:
        return {
            "valid": False,
            "char_length": 0,
            "word_count": 0,
            "score": 0,
            "issues": ["Title cannot be empty"],
            "recommendations": ["Provide a descriptive title between 80 and 130 characters."],
        }

    if char_len > 140:
        score -= 40
        issues.append(f"Title exceeds Etsy's 140-character maximum limit ({char_len}/140 chars).")
        recommendations.append("Trim title to under 140 characters to prevent API rejection.")
    elif char_len < 40:
        score -= 25
        issues.append(f"Title is too short ({char_len}/140 chars). Missing critical keyword search real estate.")
        recommendations.append("Expand title to at least 70–120 characters with high-volume search phrases.")
    elif char_len >= 80 and char_len <= 135:
        # Ideal sweet spot
        pass

    # Rule 2: Front-loading first 40 characters (Mobile & Search Weight)
    first_40 = clean_title[:40].strip()
    if len(first_40.split()) < 3:
        score -= 10
        issues.append("First 40 characters lack descriptive long-tail search terms.")
        recommendations.append("Front-load primary product keywords in the first 40 characters for mobile display.")

    # Rule 3: Separator hygiene
    separators = [",", "|", "-", "/", "•"]
    sep_count = sum(clean_title.count(s) for s in separators)
    if sep_count > 6:
        score -= 15
        issues.append("Excessive separators detected. Excessive punctuation can look like keyword stuffing.")
        recommendations.append("Use natural phrasing or 2–4 clean separators like pipes '|' or commas.")

    # Rule 4: All-caps penalty
    if clean_title.isupper() and char_len > 15:
        score -= 20
        issues.append("Title is in ALL CAPS. Etsy algorithm and shoppers penalize aggressive all-caps titles.")
        recommendations.append("Use Title Case or Sentence Case for better buyer trust.")

    score = max(0, min(100, score))
    return {
        "valid": char_len <= 140 and char_len > 0,
        "char_length": char_len,
        "word_count": word_count,
        "first_40_chars": first_40,
        "score": score,
        "issues": issues,
        "recommendations": recommendations,
    }


def audit_tags(tags: List[str]) -> Dict[str, Any]:
    """Audit 13 Etsy search tags against character limits, count, and long-tail performance."""
    raw_tags = tags or []
    cleaned_tags = [t.strip().lower() for t in raw_tags if t and t.strip()]

    issues: List[str] = []
    recommendations: List[str] = []
    invalid_tags: List[Dict[str, Any]] = []
    score = 100

    tag_count = len(cleaned_tags)

    # Rule 1: Tag Count (Strictly 13 tags recommended)
    if tag_count < 13:
        penalty = (13 - tag_count) * 4
        score -= penalty
        issues.append(f"Only {tag_count}/13 tags used. You are leaving free search traffic on the table.")
        recommendations.append(f"Add {13 - tag_count} more multi-word tags to maximize search impression coverage.")
    elif tag_count > 13:
        score -= 30
        issues.append(f"Exceeded Etsy's limit of 13 tags ({tag_count} provided). API will reject this.")
        recommendations.append("Limit tag array to exactly 13 tags.")

    # Rule 2: Check each tag's character limit (Strictly <= 20 chars per tag)
    seen = set()
    single_word_count = 0

    for tag in cleaned_tags:
        t_len = len(tag)
        if t_len > 20:
            score -= 15
            invalid_tags.append({"tag": tag, "length": t_len, "error": "Exceeds 20-char limit"})
            issues.append(f"Tag '{tag}' is {t_len} characters (max allowed is 20).")
        elif t_len == 0:
            invalid_tags.append({"tag": tag, "length": 0, "error": "Empty tag"})
        
        # Check uniqueness
        if tag in seen:
            score -= 10
            issues.append(f"Duplicate tag '{tag}' detected.")
            recommendations.append("Remove duplicate tags to cover more distinct buyer searches.")
        seen.add(tag)

        # Single word vs multi-word long-tail
        if len(tag.split()) == 1:
            single_word_count += 1

    if single_word_count > 3:
        score -= 10
        issues.append(f"{single_word_count} single-word tags detected. Long-tail phrases (2–3 words) convert significantly higher.")
        recommendations.append("Replace single-word tags with specific 2-to-3 word phrases (e.g., 'wildflower mug' instead of 'mug').")

    score = max(0, min(100, score))
    return {
        "valid": len(invalid_tags) == 0 and tag_count <= 13 and tag_count > 0,
        "tag_count": tag_count,
        "tags": cleaned_tags,
        "invalid_tags": invalid_tags,
        "single_word_count": single_word_count,
        "score": score,
        "issues": issues,
        "recommendations": recommendations,
    }


def audit_listing(title: str, tags: List[str], description: str = "") -> Dict[str, Any]:
    """Perform comprehensive SEO audit across Title, 13 Tags, and Description."""
    t_audit = audit_title(title)
    tag_audit = audit_tags(tags)

    desc_clean = (description or "").strip()
    desc_len = len(desc_clean)
    desc_issues: List[str] = []
    desc_recommendations: List[str] = []
    desc_score = 100

    if desc_len < 100:
        desc_score -= 30
        desc_issues.append("Description is very brief (<100 characters).")
        desc_recommendations.append("Include sizing charts, materials, care instructions, and gift scenarios.")
    elif desc_len > 4000:
        desc_issues.append("Description is exceptionally long (>4000 chars).")

    # Check keyword overlap between title and tags
    title_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", title.lower()))
    tag_words = set()
    for tag in tags:
        for w in re.findall(r"\b[a-zA-Z]{3,}\b", tag.lower()):
            tag_words.add(w)

    shared_keywords = list(title_words.intersection(tag_words))

    # Overall weighted score
    overall_score = round(t_audit["score"] * 0.45 + tag_audit["score"] * 0.45 + desc_score * 0.10)

    grade = "A+" if overall_score >= 95 else ("A" if overall_score >= 88 else ("B" if overall_score >= 75 else ("C" if overall_score >= 60 else "F")))

    return {
        "overall_score": overall_score,
        "grade": grade,
        "is_ready_to_publish": t_audit["valid"] and tag_audit["valid"] and overall_score >= 75,
        "title_audit": t_audit,
        "tags_audit": tag_audit,
        "description_length": desc_len,
        "shared_keywords_count": len(shared_keywords),
        "shared_keywords": shared_keywords[:8],
        "summary": f"SEO Score {overall_score}/100 (Grade {grade}). Ready to Publish: {t_audit['valid'] and tag_audit['valid'] and overall_score >= 75}",
    }


def calculate_profit(
    retail_price: float,
    pod_base_cost: float,
    shipping_charged: float = 0.0,
    shipping_cost: float = 0.0,
    is_offsite_ads: bool = False,
) -> Dict[str, Any]:
    """Calculate Etsy seller fees, POD costs, net profit, and profit margins."""
    retail = max(0.0, float(retail_price))
    pod_cost = max(0.0, float(pod_base_cost))
    ship_charged = max(0.0, float(shipping_charged))
    ship_cost = max(0.0, float(shipping_cost))

    gross_revenue = retail + ship_charged

    # 1. Listing Fee: $0.20 fixed
    listing_fee = 0.20

    # 2. Transaction Fee: 6.5% of total paid by buyer (item + shipping)
    transaction_fee = round(gross_revenue * 0.065, 2)

    # 3. Payment Processing Fee (US rate: 3.0% + $0.25)
    payment_processing_fee = round(gross_revenue * 0.03 + 0.25, 2)

    # 4. Offsite Ads Fee (15% if customer clicked an offsite Google/Facebook ad)
    offsite_ads_fee = round(gross_revenue * 0.15, 2) if is_offsite_ads else 0.0

    total_etsy_fees = round(listing_fee + transaction_fee + payment_processing_fee + offsite_ads_fee, 2)
    total_production_cost = round(pod_cost + ship_cost, 2)
    total_costs = round(total_etsy_fees + total_production_cost, 2)

    net_profit = round(gross_revenue - total_costs, 2)
    net_margin_pct = round((net_profit / gross_revenue) * 100.0, 1) if gross_revenue > 0 else 0.0
    roi_pct = round((net_profit / total_production_cost) * 100.0, 1) if total_production_cost > 0 else 0.0

    return {
        "retail_price": retail,
        "shipping_charged": ship_charged,
        "gross_revenue": gross_revenue,
        "pod_base_cost": pod_cost,
        "shipping_cost": ship_cost,
        "total_production_cost": total_production_cost,
        "etsy_fees": {
            "listing_fee": listing_fee,
            "transaction_fee": transaction_fee,
            "payment_processing_fee": payment_processing_fee,
            "offsite_ads_fee": offsite_ads_fee,
            "total_etsy_fees": total_etsy_fees,
        },
        "total_costs": total_costs,
        "net_profit": net_profit,
        "net_margin_pct": net_margin_pct,
        "roi_pct": roi_pct,
        "profitable": net_profit > 0,
    }
