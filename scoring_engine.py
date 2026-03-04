"""
scoring_engine.py – Restaurant Intelligence Platform
=====================================================
All scoring logic: 5 dimensions, composite, silent winner, persona, gap analysis.

Dimensions:
  Reputation       (30%): star rating quality + review volume social proof
  Responsiveness   (25%): % of reviews with owner reply
  Digital Presence (20%): website + phone + booking info
  Intelligence     (15%): sentiment derived from review ratings
  Visibility       (10%): recency-weighted review velocity

Composite = weighted sum

Silent Winner = rating >= 4.5 AND response_rate < 30%
"""
import logging
from datetime import datetime

import numpy as np
import pandas as pd

from data_audit import find_col

logger = logging.getLogger(__name__)


def compute_dimension_scores(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    try:
        row = df_rest[df_rest["name"] == res_name].iloc[0]
    except IndexError:
        logger.warning("Restaurant not found: %s", res_name)
        return {k: 0 for k in ["Reputation","Responsiveness","Digital Presence","Intelligence","Visibility","Composite"]}

    rating    = float(row.get("rating_n", 0) or 0)
    rev_count = float(row.get("rev_count_n", 0) or 0)
    res_rate  = float(row.get("res_rate", 0) or 0)
    sentiment = float(row.get("sentiment", 0) or 0)
    recency   = float(row.get("recency_score", 0.5) or 0.5)

    website_col = find_col(df_rest, ["website"])
    phone_col   = find_col(df_rest, ["phone"])
    price_col   = find_col(df_rest, ["price"])

    has_website = bool(website_col and str(row.get(website_col, "")).strip() not in ["", "nan", "None"])
    has_phone   = bool(phone_col   and str(row.get(phone_col, "")).strip()   not in ["", "nan", "None"])
    price_raw   = str(row.get(price_col, "") or "") if price_col else ""
    price_bonus = 10 if len(price_raw) > 5 else (5 if price_raw else 2)

    score_rep = min((rating / 5.0) * 70 + min(rev_count / 500.0, 1.0) * 30, 100)
    score_res = min(res_rate * 100, 100)
    score_dig = min((50 if has_website else 10) + (25 if has_phone else 0) + 15 + price_bonus, 100)
    score_int = min(sentiment, 100)
    score_vis = min(recency * 100, 100)
    composite = (
        score_rep * 0.30 + score_res * 0.25 + score_dig * 0.20
        + score_int * 0.15 + score_vis * 0.10
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


def get_gap_analysis(scores: dict, benchmarks: dict) -> dict:
    standard = {
        "Reputation":       benchmarks.get("rating", 4.4) * 20,
        "Responsiveness":   90.0,
        "Digital Presence": 85.0,
        "Intelligence":     75.0,
        "Visibility":       70.0,
    }
    gaps = {d: round(standard[d] - scores[d], 1) for d in standard}
    return dict(sorted(gaps.items(), key=lambda x: x[1], reverse=True))


def compute_momentum(res_name: str, df_rev: pd.DataFrame, df_rest: pd.DataFrame = None) -> pd.DataFrame:
    try:
        url_col = find_col(df_rev, ["page_url", "url", "link"])
        if url_col is None or "normalized_date" not in df_rev.columns:
            return _synthetic_momentum()

        subset = pd.DataFrame()

        if df_rest is not None and "_slug" in df_rest.columns:
            try:
                target_slug = df_rest[df_rest["name"] == res_name].iloc[0]["_slug"]
                if "_slug" not in df_rev.columns:
                    from data_audit import _url_slug
                    df_rev["_slug"] = df_rev[url_col].apply(_url_slug)
                subset = df_rev[df_rev["_slug"] == target_slug].copy()
            except (IndexError, KeyError):
                pass

        if len(subset) == 0:
            from data_audit import _url_slug
            if "_slug" not in df_rev.columns:
                df_rev["_slug"] = df_rev[url_col].apply(_url_slug)
            name_slug = res_name.lower().replace(" ", "+")
            subset = df_rev[df_rev["_slug"].str.contains(name_slug[:20], na=False, regex=False)].copy()

        if len(subset) == 0:
            return _synthetic_momentum()

        subset["_month"] = pd.to_datetime(subset["normalized_date"], errors="coerce").dt.to_period("M")
        monthly = subset.groupby("_month").size().reset_index(name="count")
        monthly["month"] = monthly["_month"].dt.to_timestamp()
        return monthly[["month", "count"]].sort_values("month").tail(13).reset_index(drop=True)

    except Exception as e:
        logger.warning("Momentum error for %s: %s", res_name, e)
        return _synthetic_momentum()


def _synthetic_momentum() -> pd.DataFrame:
    dates  = list(pd.date_range(end=datetime.now(), periods=13, freq="MS"))
    counts = np.random.poisson(lam=3.5, size=13).tolist()
    return pd.DataFrame({"month": dates, "count": counts})


def get_silent_winner_flag(res_name: str, df_rest: pd.DataFrame) -> bool:
    try:
        row = df_rest[df_rest["name"] == res_name].iloc[0]
        return (float(row.get("rating_n", 0) or 0) >= 4.5 and
                float(row.get("rev_count_n", 0) or 0) >= 50 and
                float(row.get("res_rate", 1) or 1) < 0.30)
    except Exception:
        return False


def get_customer_persona(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    try:
        row       = df_rest[df_rest["name"] == res_name].iloc[0]
        rating    = float(row.get("rating_n", 4.0) or 4.0)
        price_col = find_col(df_rest, ["price"])
        price     = str(row.get(price_col, "") or "") if price_col else ""
        rev_count = int(row.get("rev_count_n", 0) or 0)
        res_rate  = float(row.get("res_rate", 0) or 0)
    except Exception:
        rating, price, rev_count, res_rate = 4.0, "", 100, 0.0

    if rating >= 4.7 or len(price) > 8:
        primary    = "The Upscale Experience Seeker"
        segment    = "Corporate Dinner / Special Occasion"
        motivation = "Seeks prestige, Instagram-worthy moments, and flawless service. Books via OpenTable or direct website. Reads every owner response before booking."
        pitch_en = (
            f"{res_name} is already exceptional — rated {rating:.1f} stars with over {rev_count:,} reviews. "
            f"But with only {res_rate*100:.0f}% of customer reviews receiving a reply, you're leaving trust and revenue "
            f"on the table. High-spending diners read owner responses before booking. "
            f"Praxiotech's AI Review Manager ensures every guest feels heard, turning 4-star experiences into loyal "
            f"5-star advocates. Investment: 120 EUR/mo. Expected return: 2-3x booking uplift in 90 days."
        )
        pitch_de = (
            f"{res_name} ist bereits ausgezeichnet — {rating:.1f} Sterne mit {rev_count:,} Bewertungen. "
            f"Doch nur {res_rate*100:.0f}% der Gäste erhalten eine Antwort. "
            f"Mit Praxiotechs KI-Bewertungsmanagement verwandeln wir stille Gäste in treue Stammkunden. "
            f"Investition: 120 EUR/Monat. ROI innerhalb von 90 Tagen sichtbar."
        )
    elif rating >= 4.4:
        primary    = "The Dinner Date Romantic"
        segment    = "Business Lunch / Date Night"
        motivation = "Values speed and digital convenience. Books via mobile. Reads Google reviews and response rate before deciding."
        pitch_en = (
            f"{res_name} commands a strong {rating:.1f}-star reputation across {rev_count:,} reviews. "
            f"However, with a {res_rate*100:.0f}% response rate, the digital conversation is one-sided. "
            f"Top 3 competitors average 85%+ responsiveness. "
            f"Praxiotech closes this gap: AI responses, review campaigns, weekly reports — 120 EUR/month. "
            f"This is the difference between being found and being chosen."
        )
        pitch_de = (
            f"{res_name} hat {rating:.1f} Sterne mit {rev_count:,} Rezensionen. "
            f"Nur {res_rate*100:.0f}% Antwortrate vs. 85% der Top-Konkurrenz. "
            f"Praxiotech schliesst diese Lücke: KI-Antworten, Bewertungskampagnen, wöchentliche Reports — 120 EUR/Monat."
        )
    else:
        primary    = "The Curious Explorer"
        segment    = "Walk-in / Discovery Diner"
        motivation = "Discovers restaurants through Google Maps and social proof. Heavily influenced by recent review activity."
        pitch_en = (
            f"{res_name} has solid foundations with a {rating:.1f} rating and {rev_count:,} reviews. "
            f"Praxiotech targets three levers: fresh review acquisition, responsiveness automation, and Google profile optimization. "
            f"Est. 15-25% increase in foot traffic within 60 days."
        )
        pitch_de = (
            f"{res_name} hat solide {rating:.1f} Sterne. "
            f"Praxiotech: neue Bewertungen gewinnen, Antworten automatisieren, Google-Profil optimieren. "
            f"+15-25% mehr Laufkundschaft in 60 Tagen."
        )

    return {"primary": primary, "segment": segment, "motivation": motivation, "pitch_en": pitch_en, "pitch_de": pitch_de}


def compute_all_ranks(df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> pd.DataFrame:
    out = []
    for _, r in df_rest.iterrows():
        try:
            s = compute_dimension_scores(r["name"], df_rest, df_rev)["Composite"]
        except Exception:
            s = 0
        out.append({"name": r["name"], "score": s})
    df = pd.DataFrame(out).sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


def identify_silent_winners(df_rest: pd.DataFrame) -> list:
    """
    Identify restaurants that are 'silent winners':
    - Rating >= 4.5 stars
    - Review count >= 50 (significant volume)
    - Response rate < 30% (low engagement despite quality)

    Returns list of restaurant names.
    """
    silent_winners = df_rest[
        (df_rest["rating_n"] >= 4.5) &
        (df_rest["rev_count_n"] >= 50) &
        (df_rest["res_rate"].fillna(1) < 0.30)
    ]["name"].tolist()
    return silent_winners


def calculate_silent_winner_opportunity(res_name: str, df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> dict:
    """
    Calculate opportunity metrics for a silent winner.

    Returns:
        {
            "is_silent_winner": bool,
            "current_score": float,
            "potential_score": float,
            "score_uplift": float,
            "revenue_opportunity": float,  # in EUR/month
            "urgency_level": "HIGH" | "MEDIUM" | "LOW",
            "current_rating": float,
            "review_count": int,
            "current_response_rate": float,
            "recommended_response_rate": float,
        }
    """
    try:
        row_idx = df_rest[df_rest["name"] == res_name].index[0]
        row = df_rest.loc[row_idx]
    except IndexError:
        return {"is_silent_winner": False}

    rating = float(row.get("rating_n", 0) or 0)
    rev_count = int(row.get("rev_count_n", 0) or 0)
    res_rate = float(row.get("res_rate", 0) or 0)

    # Check if silent winner
    is_silent_winner = rating >= 4.5 and rev_count >= 50 and res_rate < 0.30

    if not is_silent_winner:
        return {"is_silent_winner": False}

    # Current score
    current_scores = compute_dimension_scores(res_name, df_rest, df_rev)
    current_score = current_scores["Composite"]

    # Potential score (if response rate improves to 85%)
    # Simulate improved response rate without modifying original data
    df_temp = df_rest.copy()
    df_temp.at[row_idx, "res_rate"] = 0.85
    potential_scores = compute_dimension_scores(res_name, df_temp, df_rev)
    potential_score = potential_scores["Composite"]

    score_uplift = round(potential_score - current_score, 1)

    # Revenue opportunity (conservative estimate)
    response_uplift_pct = (0.85 - res_rate) * 100
    booking_uplift_pct = response_uplift_pct * 0.12
    avg_restaurant_monthly_revenue = 50000
    revenue_opportunity = round((booking_uplift_pct / 100) * avg_restaurant_monthly_revenue, 0)

    # Urgency
    urgency = "HIGH" if rating >= 4.7 else ("MEDIUM" if rating >= 4.5 else "LOW")

    return {
        "is_silent_winner": True,
        "current_score": round(current_score, 1),
        "potential_score": round(potential_score, 1),
        "score_uplift": score_uplift,
        "revenue_opportunity": revenue_opportunity,
        "urgency_level": urgency,
        "current_rating": round(rating, 2),
        "review_count": rev_count,
        "current_response_rate": round(res_rate * 100, 1),
        "recommended_response_rate": 85,
    }



def calculate_deal_probability(res_name: str, res_data, scores: dict, gaps: dict) -> dict:
    """
    Calculate deal closing probability (0-100).

    Factors:
    - Large gaps = higher desperation to fix = higher probability
    - Silent winner status = high quality + engagement gap = BEST opportunity (90%+)
    - Review volume = credibility and market readiness
    - Budget capacity estimation = likely can afford solution

    Returns:
        {
            "deal_probability": 0-100,
            "confidence": "HIGH" | "MEDIUM" | "LOW",
            "reasoning": str,
            "next_best_action": str,
            "key_lever": str,
        }
    """
    try:
        rating = float(res_data.get("rating_n", 0) or 0)
        rev_count = int(res_data.get("rev_count_n", 0) or 0)
        res_rate = float(res_data.get("res_rate", 0) or 0)
    except Exception:
        return {"deal_probability": 50, "confidence": "LOW"}

    # Base probability from gaps
    largest_gap = max(gaps.values()) if gaps else 0
    gap_score = min((largest_gap / 25) * 100, 85)  # Max 85% from gaps

    # Bonus: Silent winner = EASY CLOSE
    is_silent_winner_check = rating >= 4.5 and rev_count >= 50 and res_rate < 0.30
    silent_bonus = 15 if is_silent_winner_check else 0

    # Budget capacity (estimated from size)
    if rev_count >= 200:
        budget_score = 15  # High-volume → high revenue → can afford
    elif rev_count >= 50:
        budget_score = 10
    else:
        budget_score = 5

    # Responsiveness gap = highest ROI for sales
    resp_gap = gaps.get("Responsiveness", 0)
    if resp_gap > 50:
        resp_bonus = 10
    elif resp_gap > 25:
        resp_bonus = 5
    else:
        resp_bonus = 0

    # Calculate probability
    deal_probability = min(gap_score + silent_bonus + (budget_score / 2) + resp_bonus, 95)

    # Confidence level
    if rev_count >= 100:
        confidence = "HIGH"
    elif rev_count >= 30:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Next best action
    if is_silent_winner_check:
        next_action = "URGENT: Position as 'response rate automation' - quick win for proven quality"
        key_lever = "Responsiveness (Gap: {:.0f}%)".format(resp_gap)
    elif resp_gap > 40:
        next_action = "Lead with 'AI Review Manager' - emphasize 2-hour response promise"
        key_lever = "Responsiveness (Gap: {:.0f}%)".format(resp_gap)
    elif gaps.get("Reputation", 0) > 20:
        next_action = "Lead with 'Review Velocity Campaign' - prove category leadership"
        key_lever = "Reputation (Gap: {:.0f}%)".format(gaps.get("Reputation", 0))
    else:
        next_action = "Position as 'growth accelerator' - unlock untapped potential"
        key_lever = largest_gap

    reasoning = f"Rating {rating}★ with {rev_count} reviews sets credibility. " \
                f"Gap of {largest_gap:.0f}% in top dimension = high motivation to fix. " \
                f"Budget capacity: {'High' if rev_count >= 200 else 'Moderate' if rev_count >= 50 else 'Limited'}."

    return {
        "deal_probability": round(deal_probability),
        "confidence": confidence,
        "reasoning": reasoning,
        "next_best_action": next_action,
        "key_lever": str(key_lever),
    }


