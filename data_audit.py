"""
data_audit.py  –  Restaurant Intelligence Platform
====================================================
Loads and enriches Octoparse restaurant + review CSVs.

restaurants.csv expected columns (auto-detected):
  Page_URL, name, address, rating, review_count, website, phone, price

reviews.csv expected columns (auto-detected):
  Page_URL, reviewer_name, reviewer_data, review_date, review_rating,
  review_text, owner_response, owner_response_content, owner_reply_time
"""
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)


# ── Google Sheets loader ─────────────────────────────────────────────────────────────
def load_from_google_sheets(restaurants_url: str, reviews_url: str) -> tuple:
    """
    Load data from public Google Sheets URLs.

    Converts shareable links to CSV export format:
    https://docs.google.com/spreadsheets/d/{ID}/edit...
    → https://docs.google.com/spreadsheets/d/{ID}/export?format=csv

    Args:
        restaurants_url: Google Sheets share link for restaurants data
        reviews_url: Google Sheets share link for reviews data

    Returns:
        (df_rest, df_rev, benchmarks) tuple
    """
    def extract_sheet_id(url: str) -> str:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid Google Sheets URL: {url}")

    def sheet_url_to_csv(url: str) -> str:
        sheet_id = extract_sheet_id(url)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    try:
        rest_csv_url = sheet_url_to_csv(restaurants_url)
        rev_csv_url = sheet_url_to_csv(reviews_url)

        logger.info("Loading restaurants from Google Sheets: %s", rest_csv_url)
        logger.info("Loading reviews from Google Sheets: %s", rev_csv_url)

        df_rest = pd.read_csv(rest_csv_url, encoding="utf-8-sig")
        df_rev = pd.read_csv(rev_csv_url, encoding="utf-8-sig")

        # Process through standard pipeline
        df_rest.columns = [c.strip() for c in df_rest.columns]
        df_rev.columns = [c.strip() for c in df_rev.columns]

        # Apply the same enrichment as local data
        df_rest = _load_restaurants_from_df(df_rest)
        df_rev = _load_reviews_from_df(df_rev)
        df_rest = _enrich_restaurants(df_rest, df_rev)
        benchmarks = _compute_benchmarks(df_rest)

        logger.info(
            "Google Sheets data loaded — %d restaurants, %d reviews, benchmark avg rating %.2f",
            len(df_rest), len(df_rev), benchmarks["avg_rating"],
        )
        return df_rest, df_rev, benchmarks

    except Exception as e:
        logger.error("Error loading from Google Sheets: %s", e)
        raise


# ── Path resolution ───────────────────────────────────────────────────────────────
def _resolve_path(filename: str) -> str:
    module_dir = Path(__file__).parent
    candidates = [
        Path(filename),
        module_dir / filename,
        module_dir / "data" / filename,
        Path(os.environ.get("RESTAURANT_DATA_PATH", "")) if "restaurant" in filename.lower() else Path(""),
        Path(os.environ.get("REVIEWS_DATA_PATH", "")) if "review" in filename.lower() else Path(""),
    ]
    for p in candidates:
        if p and p.exists():
            return str(p)
    return filename


# ── Public entry point ────────────────────────────────────────────────────────────
def load_and_clean_data(
    restaurants_path: str = "restaurants.csv",
    reviews_path: str = "reviews.csv",
):
    abs_rest = _resolve_path(restaurants_path)
    abs_rev  = _resolve_path(reviews_path)
    logger.info("Loading restaurants: %s", abs_rest)
    logger.info("Loading reviews:     %s", abs_rev)

    df_rest = _load_restaurants(abs_rest)
    df_rev  = _load_reviews(abs_rev)
    df_rest = _enrich_restaurants(df_rest, df_rev)
    benchmarks = _compute_benchmarks(df_rest)

    logger.info(
        "Data loaded — %d restaurants, %d reviews, benchmark avg rating %.2f",
        len(df_rest), len(df_rev), benchmarks["avg_rating"],
    )
    return df_rest, df_rev, benchmarks


# ── Restaurant loader ─────────────────────────────────────────────────────────────
def _load_restaurants(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Restaurants CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    logger.info("Restaurants raw columns: %s", list(df.columns))
    return _load_restaurants_from_df(df)


def _load_restaurants_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """Process restaurant DataFrame (already loaded)."""
    # Rating
    rating_col = find_col(df, ["rating"])
    if rating_col:
        df["rating_n"] = (
            df[rating_col].astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("\xa0", "", regex=False)
            .str.extract(r"(\d+\.?\d*)", expand=False)
            .astype(float).fillna(0)
        )
    else:
        df["rating_n"] = 0.0

    # Review count
    rev_col = find_col(df, ["review_count", "review_co", "reviews", "rev_count"])
    df["rev_count_n"] = df[rev_col].apply(_parse_int) if rev_col else 0

    # Ensure name column
    name_col = find_col(df, ["name", "restaurant_name", "title", "business_name"])
    if name_col and name_col != "name":
        df["name"] = df[name_col]
    elif "name" not in df.columns:
        df["name"] = df.iloc[:, 1]
    df["name"] = df["name"].astype(str).str.strip()

    # Default columns
    if not find_col(df, ["district"]):
        df["district"] = "City"
    if not find_col(df, ["price"]):
        df["price"] = ""

    return df


# ── Review loader ─────────────────────────────────────────────────────────────────
def _load_reviews(path: str) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Reviews CSV not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    logger.info("Reviews raw columns: %s", list(df.columns))
    return _load_reviews_from_df(df)


def _load_reviews_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """Process reviews DataFrame (already loaded)."""
    date_col = find_col(df, ["review_date", "date", "review_time", "reviewer_data"])
    df["normalized_date"] = (
        df[date_col].apply(_parse_relative_date) if date_col else datetime.now()
    )

    rating_col = find_col(df, ["review_rating", "rating", "stars"])
    if rating_col:
        df["review_rating"] = pd.to_numeric(
            df[rating_col].astype(str).str.replace("\xa0", "", regex=False).str.strip(),
            errors="coerce",
        ).fillna(5)
    else:
        df["review_rating"] = 5.0

    return df


# ── Enrichment ────────────────────────────────────────────────────────────────────
def _enrich_restaurants(df_rest: pd.DataFrame, df_rev: pd.DataFrame) -> pd.DataFrame:
    r_url = find_col(df_rest, ["page_url", "url", "link"])
    v_url = find_col(df_rev,  ["page_url", "url", "link"])

    resp_content_col = find_col(df_rev, ["owner_response_content"])
    resp_flag_col    = find_col(df_rev, ["owner_response"])

    if r_url and v_url:
        df_rest["_slug"] = df_rest[r_url].apply(_url_slug)
        df_rev["_slug"]  = df_rev[v_url].apply(_url_slug)
        rev_by_slug = {slug: grp for slug, grp in df_rev.groupby("_slug")}

        rates, sm, rm, rev_texts = {}, {}, {}, {}
        c90  = datetime.now() - timedelta(days=90)
        c180 = datetime.now() - timedelta(days=180)

        for slug in df_rest["_slug"]:
            sub = rev_by_slug.get(slug)
            if sub is None or len(sub) == 0:
                continue

            # Response rate
            responded = pd.Series([False] * len(sub), index=sub.index)
            if resp_content_col and resp_content_col in sub.columns:
                vals = sub[resp_content_col].astype(str).str.strip()
                responded |= sub[resp_content_col].notna() & (vals != "") & (vals.str.lower() != "nan")
            if resp_flag_col and resp_flag_col in sub.columns:
                vals = sub[resp_flag_col].astype(str).str.strip()
                responded |= sub[resp_flag_col].notna() & (vals != "") & (vals.str.lower() != "nan")
            rates[slug] = responded.sum() / len(sub)

            # Sentiment from ratings
            if "review_rating" in sub.columns:
                sm[slug] = ((sub["review_rating"].mean() - 1) / 4.0) * 100

            # Recency score
            if "normalized_date" in sub.columns:
                d = pd.to_datetime(sub["normalized_date"], errors="coerce")
                rm[slug] = min(((d > c90).sum() * 0.7 + (d > c180).sum() * 0.3) / len(sub), 1.0)

            # Sample review texts for AI chat context
            text_col = find_col(sub, ["review_text", "text", "review_content"])
            if text_col:
                texts = sub[text_col].dropna().astype(str).str.strip()
                texts = texts[texts.str.len() > 20].head(10).tolist()
                rev_texts[slug] = texts

        df_rest["res_rate"]      = df_rest["_slug"].map(rates).fillna(0.0)
        df_rest["sentiment"]     = df_rest["_slug"].map(sm).fillna(((df_rest["rating_n"] - 1) / 4.0) * 100)
        df_rest["recency_score"] = df_rest["_slug"].map(rm).fillna(0.5)
        df_rest["_review_texts"] = df_rest["_slug"].map(rev_texts).apply(lambda x: x if isinstance(x, list) else [])
    else:
        logger.warning("No URL column found — using synthetic enrichment")
        np.random.seed(42)
        df_rest["res_rate"]      = np.random.beta(2, 3, size=len(df_rest))
        df_rest["sentiment"]     = ((df_rest["rating_n"] - 1) / 4.0) * 100
        df_rest["recency_score"] = 0.5
        df_rest["_review_texts"] = [[] for _ in range(len(df_rest))]

    return df_rest


# ── Benchmarks ────────────────────────────────────────────────────────────────────
def _compute_benchmarks(df_rest: pd.DataFrame) -> dict:
    return {
        "rating":          float(df_rest["rating_n"].quantile(0.75)),
        "response_rate":   0.90,
        "recency":         0.70,
        "review_volume":   float(df_rest["rev_count_n"].quantile(0.75)),
        "top_rating":      float(df_rest["rating_n"].max()),
        "avg_rating":      float(df_rest["rating_n"].mean()),
        "median_reviews":  float(df_rest["rev_count_n"].median()),
        "total_count":     len(df_rest),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────────
def find_col(df: pd.DataFrame, candidates: list) -> str | None:
    col_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in col_map:
            return col_map[c.lower()]
    return None


def _url_slug(url: str) -> str:
    m = re.search(r"/place/([^/@]+)", str(url))
    return m.group(1).lower() if m else str(url).lower()[:80]


def _parse_int(x) -> int:
    found = re.findall(r"\d+", str(x))
    return int("".join(found[:2])) if found else 0


def _parse_relative_date(date_str) -> datetime:
    today = datetime.now()
    s = str(date_str).lower()
    s = re.sub(r"^bearbeitet:\s*", "", s).strip()
    n_match = re.search(r"\d+", s)
    n = int(n_match.group()) if n_match else 1

    mapping = [
        (["einem monat", "a month ago"],          lambda: today - timedelta(days=30)),
        (["monat", "month"],                       lambda: today - timedelta(days=n * 30)),
        (["einem jahr", "a year ago"],             lambda: today - timedelta(days=365)),
        (["jahr", "year"],                         lambda: today - timedelta(days=n * 365)),
        (["einer woche", "a week ago"],            lambda: today - timedelta(days=7)),
        (["woche", "week"],                        lambda: today - timedelta(days=n * 7)),
        (["tag", "day"],                           lambda: today - timedelta(days=n)),
        (["stunde", "hour"],                       lambda: today - timedelta(hours=n)),
        (["gestern", "yesterday"],                 lambda: today - timedelta(days=1)),
        (["heute", "today"],                       lambda: today),
    ]
    for keywords, fn in mapping:
        if any(kw in s for kw in keywords):
            return fn()

    for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
        try:
            return datetime.strptime(str(date_str), fmt)
        except Exception:
            pass
    return today - timedelta(days=90)
