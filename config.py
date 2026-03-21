"""
config.py — Restaurant Intelligence Platform
=============================================
Single source of truth for all business constants.

Why: magic numbers scattered across files cause silent drift.
Change a price, a weight, or a benchmark here → everywhere updates.
"""

# ── Scoring weights ───────────────────────────────────────────────────────────
# These reflect the sales narrative: reputation + responsiveness drive the most
# immediate revenue impact. Weights approved by product team — change only with
# data analysis to back it up.
SCORING_WEIGHTS = {
    "Reputation":       0.30,
    "Responsiveness":   0.25,
    "Digital Presence": 0.20,
    "Intelligence":     0.15,
    "Visibility":       0.10,
}

# ── Benchmark targets ─────────────────────────────────────────────────────────
# What top-quartile German restaurants look like.
# Responsiveness (90%) and Digital (85%) are aspirational — that's the gap we
# sell into. Reputation is derived from typical top-quartile rating × 20.
BENCHMARK_TARGETS = {
    "Reputation":       88.0,   # 4.4 stars × 20 — typical top-quartile
    "Responsiveness":   90.0,
    "Digital Presence": 85.0,
    "Intelligence":     75.0,
    "Visibility":       70.0,
}

# ── Product pricing (EUR/month) ───────────────────────────────────────────────
# All Praxiotech product prices. Update here when pricing changes.
PRODUCT_PRICING = {
    "ai_review_manager":   120,
    "profile_optimization": 60,
    "review_velocity":      80,
    "engagement_booster":   60,
    "sentiment_monitoring": 80,
}

# ── Revenue assumption ────────────────────────────────────────────────────────
# Assumed average annual revenue for a mid-tier German sit-down restaurant.
# Used in silent winner opportunity revenue calculation.
# Source: German restaurant industry average (Dehoga 2023 report).
ASSUMED_RESTAURANT_REVENUE = 50_000

# ── Silent winner thresholds ──────────────────────────────────────────────────
# High quality (rating + reviews) + low digital effort (response rate) = easy sell.
SILENT_WINNER_MIN_RATING        = 4.5
SILENT_WINNER_MIN_REVIEWS       = 50
SILENT_WINNER_MAX_RESPONSE_RATE = 0.30

# ── Scoring constants ─────────────────────────────────────────────────────────
# Max review count for reputation log-scaling. Above this, additional reviews
# have diminishing returns on the score.
MAX_REVIEW_VOLUME = 500

# ── Momentum chart ────────────────────────────────────────────────────────────
# Fixed seed keeps synthetic momentum chart consistent across rerenders.
# When real review trend data is missing we show synthetic — it must not
# change on every rerender or it looks like live data.
MOMENTUM_RANDOM_SEED = 42
