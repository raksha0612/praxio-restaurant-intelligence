"""
scoring_engine.py — Restaurant Intelligence Platform
=====================================================
All scoring logic: 5 dimensions, composite, silent winner, persona, gaps.

Dimensions (weights in config.py):
  Reputation       (30%): star rating quality + review volume social proof
  Responsiveness   (25%): % of reviews with owner reply
  Digital Presence (20%): website + phone + booking info
  Intelligence     (15%): sentiment derived from review ratings
  Visibility       (10%): recency-weighted review velocity

Composite = weighted sum.
Silent Winner = rating >= 4.5 AND reviews >= 50 AND response_rate < 30%.
"""
import logging

import numpy as np
import pandas as pd
from datetime import datetime

from config import (
    SCORING_WEIGHTS,
    BENCHMARK_TARGETS,
    ASSUMED_RESTAURANT_REVENUE,
    SILENT_WINNER_MIN_RATING,
    SILENT_WINNER_MIN_REVIEWS,
    SILENT_WINNER_MAX_RESPONSE_RATE,
    MAX_REVIEW_VOLUME,
    MOMENTUM_RANDOM_SEED,
)
from data_audit import find_col, _url_slug

logger = logging.getLogger(__name__)


# ── Dimension scoring ─────────────────────────────────────────────────────────

def compute_dimension_scores(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    """Compute all 5 dimension scores + composite for one restaurant."""
    try:
        row = df_rest[df_rest["name"] == res_name].iloc[0]
    except IndexError:
        logger.warning("Restaurant not found in dataset: %s", res_name)
        return {k: 0 for k in ["Reputation", "Responsiveness", "Digital Presence", "Intelligence", "Visibility", "Composite"]}

    rating    = float(row.get("rating_n",     0) or 0)
    rev_count = float(row.get("rev_count_n",  0) or 0)
    res_rate  = float(row.get("res_rate",     0) or 0)
    sentiment = float(row.get("sentiment",    0) or 0)
    recency   = float(row.get("recency_score", 0.5) or 0.5)

    website_col = find_col(df_rest, ["website"])
    phone_col   = find_col(df_rest, ["phone"])
    price_col   = find_col(df_rest, ["price"])

    has_website = bool(website_col and str(row.get(website_col, "")).strip() not in ["", "nan", "None"])
    has_phone   = bool(phone_col   and str(row.get(phone_col,   "")).strip() not in ["", "nan", "None"])
    price_raw   = str(row.get(price_col, "") or "") if price_col else ""
    price_bonus = 10 if len(price_raw) > 5 else (5 if price_raw else 2)

    score_rep = _score_reputation(rating, rev_count)
    score_res = min(res_rate * 100, 100)
    score_dig = _score_digital(has_website, has_phone, price_bonus)
    score_int = min(sentiment, 100)
    score_vis = min(recency * 100, 100)

    w = SCORING_WEIGHTS
    composite = (
        score_rep * w["Reputation"]
        + score_res * w["Responsiveness"]
        + score_dig * w["Digital Presence"]
        + score_int * w["Intelligence"]
        + score_vis * w["Visibility"]
    )

    scores = {
        "Reputation":       round(score_rep, 1),
        "Responsiveness":   round(score_res, 1),
        "Digital Presence": round(score_dig, 1),
        "Intelligence":     round(score_int, 1),
        "Visibility":       round(score_vis, 1),
        "Composite":        round(composite, 1),
    }
    logger.debug("Scores for %s: %s", res_name, scores)
    return scores


def _score_reputation(rating: float, rev_count: float) -> float:
    """Map rating + review volume to a 0–100 reputation score."""
    rating_component  = (rating / 5.0) * 70
    volume_component  = min(rev_count / MAX_REVIEW_VOLUME, 1.0) * 30
    return min(rating_component + volume_component, 100)


def _score_digital(has_website: bool, has_phone: bool, price_bonus: int) -> float:
    """Map digital presence signals to a 0–100 score."""
    base = 50 if has_website else 10
    phone_pts = 25 if has_phone else 0
    # 15 pts baseline for being discoverable, plus price_bonus for price visibility
    return min(base + phone_pts + 15 + price_bonus, 100)


# ── Gap analysis ──────────────────────────────────────────────────────────────

def get_gap_analysis(scores: dict, benchmarks: dict) -> dict:
    """Return gap between each dimension score and its benchmark target."""
    targets = _build_benchmark_targets(benchmarks)
    gaps = {dim: round(targets[dim] - scores[dim], 1) for dim in targets}
    return dict(sorted(gaps.items(), key=lambda x: x[1], reverse=True))


def _build_benchmark_targets(benchmarks: dict) -> dict:
    """
    Build benchmark targets for gap analysis.
    Reputation uses live data (top-quartile rating × 20).
    All others come from config — they are aspirational sales targets.
    """
    return {
        "Reputation":       benchmarks.get("rating", 4.4) * 20,
        "Responsiveness":   BENCHMARK_TARGETS["Responsiveness"],
        "Digital Presence": BENCHMARK_TARGETS["Digital Presence"],
        "Intelligence":     BENCHMARK_TARGETS["Intelligence"],
        "Visibility":       BENCHMARK_TARGETS["Visibility"],
    }


# ── Review momentum ───────────────────────────────────────────────────────────

def compute_momentum(res_name: str, df_rev: pd.DataFrame, df_rest: pd.DataFrame = None) -> pd.DataFrame:
    """Return monthly review counts for a restaurant over the last 13 months."""
    try:
        url_col = find_col(df_rev, ["page_url", "url", "link"])
        if url_col is None or "normalized_date" not in df_rev.columns:
            return _synthetic_momentum()

        subset = _find_review_subset(res_name, df_rest, df_rev, url_col)

        if len(subset) == 0:
            return _synthetic_momentum()

        subset["_month"] = pd.to_datetime(subset["normalized_date"], errors="coerce").dt.to_period("M")
        monthly = subset.groupby("_month").size().reset_index(name="count")
        monthly["month"] = monthly["_month"].dt.to_timestamp()
        return monthly[["month", "count"]].sort_values("month").tail(13).reset_index(drop=True)

    except Exception as e:
        logger.warning("Momentum error for %s: %s", res_name, e)
        return _synthetic_momentum()


def _find_review_subset(res_name: str, df_rest, df_rev: pd.DataFrame, url_col: str) -> pd.DataFrame:
    """Find the review rows that belong to a specific restaurant."""
    if df_rest is not None and "_slug" in df_rest.columns:
        try:
            target_slug = df_rest[df_rest["name"] == res_name].iloc[0]["_slug"]
            if "_slug" not in df_rev.columns:
                df_rev["_slug"] = df_rev[url_col].apply(_url_slug)
            subset = df_rev[df_rev["_slug"] == target_slug].copy()
            if len(subset) > 0:
                return subset
        except (IndexError, KeyError):
            pass

    # Fallback: fuzzy match by name slug in URL
    if "_slug" not in df_rev.columns:
        df_rev["_slug"] = df_rev[url_col].apply(_url_slug)
    name_slug = res_name.lower().replace(" ", "+")
    return df_rev[df_rev["_slug"].str.contains(name_slug[:20], na=False, regex=False)].copy()


def _synthetic_momentum() -> pd.DataFrame:
    """
    Fallback momentum when real review data is unavailable.
    Seeded so the chart is deterministic — fake data must not change on every
    rerender or it looks like real live data.
    """
    np.random.seed(MOMENTUM_RANDOM_SEED)
    dates  = list(pd.date_range(end=datetime.now(), periods=13, freq="MS"))
    counts = np.random.poisson(lam=3.5, size=13).tolist()
    return pd.DataFrame({"month": dates, "count": counts})


# ── Silent winners ────────────────────────────────────────────────────────────

def get_silent_winner_flag(res_name: str, df_rest: pd.DataFrame) -> bool:
    """Return True if the restaurant meets all silent winner criteria."""
    try:
        row = df_rest[df_rest["name"] == res_name].iloc[0]
        return (
            float(row.get("rating_n",   0) or 0) >= SILENT_WINNER_MIN_RATING
            and float(row.get("rev_count_n", 0) or 0) >= SILENT_WINNER_MIN_REVIEWS
            and float(row.get("res_rate",    1) or 1) <  SILENT_WINNER_MAX_RESPONSE_RATE
        )
    except Exception:
        return False


def identify_silent_winners(df_rest: pd.DataFrame) -> list:
    """Return list of restaurant names that are silent winners."""
    mask = (
        (df_rest["rating_n"]  >= SILENT_WINNER_MIN_RATING)
        & (df_rest["rev_count_n"] >= SILENT_WINNER_MIN_REVIEWS)
        & (df_rest["res_rate"].fillna(1) < SILENT_WINNER_MAX_RESPONSE_RATE)
    )
    return df_rest[mask]["name"].tolist()


def calculate_silent_winner_opportunity(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    """Calculate the revenue opportunity for a silent winner restaurant."""
    try:
        row_idx = df_rest[df_rest["name"] == res_name].index[0]
        row     = df_rest.loc[row_idx]
    except IndexError:
        return {"is_silent_winner": False}

    rating    = float(row.get("rating_n",    0) or 0)
    rev_count = int(row.get("rev_count_n",   0) or 0)
    res_rate  = float(row.get("res_rate",    0) or 0)

    if not (rating >= SILENT_WINNER_MIN_RATING and rev_count >= SILENT_WINNER_MIN_REVIEWS and res_rate < SILENT_WINNER_MAX_RESPONSE_RATE):
        return {"is_silent_winner": False}

    current_score   = compute_dimension_scores(res_name, df_rest, df_rev)["Composite"]
    potential_score = _score_at_target_response(res_name, row_idx, df_rest, df_rev)
    score_uplift    = round(potential_score - current_score, 1)

    response_uplift_pct = (0.85 - res_rate) * 100
    booking_uplift_pct  = response_uplift_pct * 0.12
    # Why ASSUMED_RESTAURANT_REVENUE: we need a revenue baseline to translate
    # % booking uplift into EUR. This is the German restaurant industry average.
    revenue_opportunity = round((booking_uplift_pct / 100) * ASSUMED_RESTAURANT_REVENUE, 0)

    return {
        "is_silent_winner":          True,
        "current_score":             round(current_score, 1),
        "potential_score":           round(potential_score, 1),
        "score_uplift":              score_uplift,
        "revenue_opportunity":       revenue_opportunity,
        "urgency_level":             "HIGH" if rating >= 4.7 else "MEDIUM",
        "current_rating":            round(rating, 2),
        "review_count":              rev_count,
        "current_response_rate":     round(res_rate * 100, 1),
        "recommended_response_rate": 85,
    }


def _score_at_target_response(res_name: str, row_idx, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> float:
    """Simulate the composite score if response rate reached 85%."""
    df_temp = df_rest.copy()
    df_temp.at[row_idx, "res_rate"] = 0.85
    return compute_dimension_scores(res_name, df_temp, df_rev)["Composite"]


# ── Customer persona ──────────────────────────────────────────────────────────

def get_customer_persona(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    """Classify the restaurant into a sales persona and generate a pitch."""
    try:
        row       = df_rest[df_rest["name"] == res_name].iloc[0]
        rating    = float(row.get("rating_n",    4.0) or 4.0)
        price_col = find_col(df_rest, ["price"])
        price     = str(row.get(price_col, "") or "") if price_col else ""
        rev_count = int(row.get("rev_count_n",  0) or 0)
        res_rate  = float(row.get("res_rate",   0) or 0)
    except Exception:
        rating, price, rev_count, res_rate = 4.0, "", 100, 0.0

    price_mo = PRODUCT_PRICING_DISPLAY

    if rating >= 4.7 or len(price) > 8:
        return _persona_upscale(res_name, rating, rev_count, res_rate, price_mo)
    elif rating >= 4.4:
        return _persona_dinner_date(res_name, rating, rev_count, res_rate, price_mo)
    else:
        return _persona_explorer(res_name, rating, rev_count, price_mo)


# Why a separate display string: persona pitches need EUR formatting, not raw int.
# Update PRODUCT_PRICING in config.py — this string auto-updates.
from config import PRODUCT_PRICING as _pp
PRODUCT_PRICING_DISPLAY = f"{_pp['ai_review_manager']} EUR/mo"


def _persona_upscale(res_name: str, rating: float, rev_count: int, res_rate: float, price_mo: str) -> dict:
    return {
        "primary":    "The Upscale Experience Seeker",
        "segment":    "Corporate Dinner / Special Occasion",
        "motivation": "Seeks prestige, Instagram-worthy moments, and flawless service. Books via OpenTable or direct website. Reads every owner response before booking.",
        "pitch_en": (
            f"{res_name} is already exceptional — rated {rating:.1f} stars with {rev_count:,} reviews. "
            f"But with only {res_rate*100:.0f}% of reviews receiving a reply, you're leaving trust and revenue on the table. "
            f"High-spending diners read owner responses before booking. "
            f"Praxiotech's AI Review Manager ensures every guest feels heard, turning 4-star experiences into loyal 5-star advocates. "
            f"Investment: {price_mo}. Expected return: 2–3× booking uplift in 90 days."
        ),
        "pitch_de": (
            f"{res_name} ist bereits ausgezeichnet — {rating:.1f} Sterne mit {rev_count:,} Bewertungen. "
            f"Doch nur {res_rate*100:.0f}% der Gäste erhalten eine Antwort. "
            f"Mit Praxiotechs KI-Bewertungsmanagement verwandeln wir stille Gäste in treue Stammkunden. "
            f"Investition: {price_mo}. ROI innerhalb von 90 Tagen sichtbar."
        ),
    }


def _persona_dinner_date(res_name: str, rating: float, rev_count: int, res_rate: float, price_mo: str) -> dict:
    return {
        "primary":    "The Dinner Date Romantic",
        "segment":    "Business Lunch / Date Night",
        "motivation": "Values speed and digital convenience. Books via mobile. Reads Google reviews and response rate before deciding.",
        "pitch_en": (
            f"{res_name} commands a strong {rating:.1f}-star reputation across {rev_count:,} reviews. "
            f"However, with a {res_rate*100:.0f}% response rate, the digital conversation is one-sided. "
            f"Top competitors average 85%+ responsiveness. "
            f"Praxiotech closes this gap: AI responses, review campaigns, weekly reports — {price_mo}. "
            f"This is the difference between being found and being chosen."
        ),
        "pitch_de": (
            f"{res_name} hat {rating:.1f} Sterne mit {rev_count:,} Rezensionen. "
            f"Nur {res_rate*100:.0f}% Antwortrate vs. 85% der Top-Konkurrenz. "
            f"Praxiotech schließt diese Lücke: KI-Antworten, Bewertungskampagnen, wöchentliche Reports — {price_mo}."
        ),
    }


def _persona_explorer(res_name: str, rating: float, rev_count: int, price_mo: str) -> dict:
    return {
        "primary":    "The Curious Explorer",
        "segment":    "Walk-in / Discovery Diner",
        "motivation": "Discovers restaurants through Google Maps and social proof. Heavily influenced by recent review activity.",
        "pitch_en": (
            f"{res_name} has solid foundations with a {rating:.1f} rating and {rev_count:,} reviews. "
            f"Praxiotech targets three levers: fresh review acquisition, responsiveness automation, and Google profile optimization. "
            f"Est. 15–25% increase in foot traffic within 60 days."
        ),
        "pitch_de": (
            f"{res_name} hat solide {rating:.1f} Sterne. "
            f"Praxiotech: neue Bewertungen gewinnen, Antworten automatisieren, Google-Profil optimieren. "
            f"+15–25% mehr Laufkundschaft in 60 Tagen."
        ),
    }


# ── Leaderboard ───────────────────────────────────────────────────────────────

def compute_all_ranks(df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> pd.DataFrame:
    """Compute composite scores for all restaurants and return a ranked DataFrame."""
    out = []
    for _, r in df_rest.iterrows():
        try:
            score = compute_dimension_scores(r["name"], df_rest, df_rev)["Composite"]
        except Exception as e:
            logger.warning("Scoring failed for %s: %s", r.get("name", "?"), e)
            score = 0
        out.append({"name": r["name"], "score": score})

    df = pd.DataFrame(out).sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


# ── Actionable solutions ──────────────────────────────────────────────────────

def get_actionable_solutions(res_name: str, res_data, top_gaps: list, language: str = "EN") -> list:
    """Return 5 prioritised action items based on top gap dimensions."""
    rating  = float(res_data.get("rating_n", 4.6) or 4.6)
    est_pts = min(int(top_gaps[0][1] * 0.6), 999) if top_gaps else 0

    if language.upper() == "DE":
        return _solutions_de(est_pts, rating)
    return _solutions_en(est_pts, rating)


def _solutions_en(est_pts: int, rating: float) -> list:
    return [
        {"emoji": "⚡", "title": "Optimize Response Time",   "priority": "HIGH",   "priority_color": "#DC2626",
         "desc": "Reduce avg reply to under 2 hours — top revenue lever",             "est": f"Est. +{est_pts} pts score lift"},
        {"emoji": "⭐", "title": "Launch Review Campaign",   "priority": "MEDIUM", "priority_color": "#F59E0B",
         "desc": "Target 15 new reviews this quarter via post-visit SMS",              "est": "Est. +12% visibility"},
        {"emoji": "🔗", "title": "Update Google Profile",    "priority": "LOW",    "priority_color": "#10B981",
         "desc": "Refresh photos, menu links & booking CTA",                          "est": "Est. +8% CTR"},
        {"emoji": "🤖", "title": "AI Review Management",     "priority": "HIGH",   "priority_color": "#DC2626",
         "desc": f"Automate personalised responses at scale — {PRODUCT_PRICING['ai_review_manager']} EUR/mo", "est": "Est. 3× response rate"},
        {"emoji": "📡", "title": "Sentiment Monitoring",     "priority": "MEDIUM", "priority_color": "#F59E0B",
         "desc": "Real-time alerts for negative reviews across platforms",             "est": f"Protect {rating:.1f} star rating"},
    ]


def _solutions_de(est_pts: int, rating: float) -> list:
    return [
        {"emoji": "⚡", "title": "Antwortzeit optimieren",     "priority": "HOCH",    "priority_color": "#DC2626",
         "desc": "Durchschn. Antwortzeit unter 2 Stunden — wichtigster Umsatzhebel",   "est": f"Est. +{est_pts} Punkte Score-Steigerung"},
        {"emoji": "⭐", "title": "Bewertungskampagne starten", "priority": "MITTEL",  "priority_color": "#F59E0B",
         "desc": "Ziel: 15 neue Bewertungen dieses Quartal via Post-Visit SMS",         "est": "Est. +12% Sichtbarkeit"},
        {"emoji": "🔗", "title": "Google Profil aktualisieren","priority": "NIEDRIG", "priority_color": "#10B981",
         "desc": "Fotos, Menülinks & Buchungs-CTA aktualisieren",                      "est": "Est. +8% CTR"},
        {"emoji": "🤖", "title": "KI-Bewertungsmanagement",    "priority": "HOCH",    "priority_color": "#DC2626",
         "desc": f"Personalisierte Antworten automatisieren — {PRODUCT_PRICING['ai_review_manager']} EUR/Mo", "est": "Est. 3× Antwortrate"},
        {"emoji": "📡", "title": "Stimmungsüberwachung",       "priority": "MITTEL",  "priority_color": "#F59E0B",
         "desc": "Echtzeit-Benachrichtigungen für negative Bewertungen",                "est": f"{rating:.1f} Sterne Bewertung schützen"},
    ]


# ── Rating split ──────────────────────────────────────────────────────────────

def get_rating_split(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> tuple:
    """Return (values, labels) for the star rating distribution chart."""
    try:
        row  = df_rest[df_rest["name"] == res_name].iloc[0]
        slug = row.get("_slug", "")
        if slug and "_slug" in df_rev.columns:
            sub = df_rev[df_rev["_slug"] == slug]
        else:
            sub = pd.DataFrame()
        if len(sub) > 0 and "review_rating" in sub.columns:
            rc = sub["review_rating"].value_counts().sort_index(ascending=False)
            return rc.values.tolist(), rc.index.tolist()
    except Exception as e:
        logger.warning("get_rating_split failed for %s: %s", res_name, e)
    # Fallback: representative distribution
    return [40, 30, 15, 10, 5], [5, 4, 3, 2, 1]


# ── Deal probability ──────────────────────────────────────────────────────────

def calculate_deal_probability(res_name: str, res_data, scores: dict, gaps: dict) -> dict:
    """
    Calculate deal closing probability (0–100).

    Factors:
      - Large gaps = high motivation to fix = higher probability
      - Silent winner = high quality + engagement gap = best opportunity
      - Review volume = market credibility and budget capacity proxy
    """
    try:
        rating    = float(res_data.get("rating_n",   0) or 0)
        rev_count = int(res_data.get("rev_count_n",  0) or 0)
        res_rate  = float(res_data.get("res_rate",   0) or 0)
    except Exception:
        return {"deal_probability": 50, "confidence": "LOW"}

    largest_gap  = max(gaps.values()) if gaps else 0
    gap_score    = min((largest_gap / 25) * 100, 85)
    silent_bonus = 15 if (rating >= SILENT_WINNER_MIN_RATING and rev_count >= SILENT_WINNER_MIN_REVIEWS and res_rate < SILENT_WINNER_MAX_RESPONSE_RATE) else 0
    budget_score = 15 if rev_count >= 200 else (10 if rev_count >= 50 else 5)
    resp_gap     = gaps.get("Responsiveness", 0)
    resp_bonus   = 10 if resp_gap > 50 else (5 if resp_gap > 25 else 0)
    deal_prob    = min(gap_score + silent_bonus + (budget_score / 2) + resp_bonus, 95)

    confidence = "HIGH" if rev_count >= 100 else ("MEDIUM" if rev_count >= 30 else "LOW")
    next_action, key_lever = _deal_action(rating, rev_count, res_rate, resp_gap, gaps, largest_gap)

    return {
        "deal_probability": round(deal_prob),
        "confidence":       confidence,
        "reasoning":        f"Rating {rating} stars, {rev_count} reviews. Largest gap {largest_gap:.0f}%. Budget capacity: {'High' if rev_count >= 200 else 'Moderate' if rev_count >= 50 else 'Limited'}.",
        "next_best_action": next_action,
        "key_lever":        str(key_lever),
    }


def _deal_action(rating, rev_count, res_rate, resp_gap, gaps, largest_gap) -> tuple:
    """Return (next_action description, key_lever label) based on signals."""
    is_sw = rating >= SILENT_WINNER_MIN_RATING and rev_count >= SILENT_WINNER_MIN_REVIEWS and res_rate < SILENT_WINNER_MAX_RESPONSE_RATE
    if is_sw:
        return "URGENT: Position as 'response rate automation' — quick win for proven quality", f"Responsiveness (Gap: {resp_gap:.0f}%)"
    if resp_gap > 40:
        return "Lead with 'AI Review Manager' — emphasise 2-hour response promise", f"Responsiveness (Gap: {resp_gap:.0f}%)"
    if gaps.get("Reputation", 0) > 20:
        return "Lead with 'Review Velocity Campaign' — prove category leadership", f"Reputation (Gap: {gaps.get('Reputation', 0):.0f}%)"
    return "Position as 'growth accelerator' — unlock untapped potential", str(largest_gap)


# keep PRODUCT_PRICING importable from this module for templates that use it
from config import PRODUCT_PRICING  # noqa: E402, F401
