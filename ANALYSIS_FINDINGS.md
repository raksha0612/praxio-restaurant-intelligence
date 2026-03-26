# Analysis: Data Source, Security, and Scraping Quality

**Date:** March 25, 2026
**Files Analyzed:** Hamburg_rest.xlsx, Hamburg_Review(1).xlsx, URL_hamburg.xlsx, app.py, data_audit.py

---

## 1. GOOGLE SHEETS vs DATABASE: FRANKFURT DATA SOURCE

### Current Implementation (from app.py:406-420)

**You are CORRECT — Frankfurt uses Google Sheets, NOT a database.**

The code explicitly defines a `CITIES` dictionary with hardcoded Google Sheets URLs:

```python
CITIES = {
    "Frankfurt": {
        "rest": "https://docs.google.com/spreadsheets/d/1GzZWRuPr4y3yscDZYprWZtdgZ6Z6MkPBHwRTLH4bPR8/edit?usp=sharing",
        "rev":  "https://docs.google.com/spreadsheets/d/1zSAd91SkuYgXuIOQa5WVJneEV5dmPyM9XMnI66iNGb4/edit?usp=sharing",
    },
    "Hamburg": { ... },
    "Wedel": { ... },
}
```

### How It Works

1. **Runtime Loading** (data_audit.py:32-85):
   - The app calls `load_from_google_sheets(restaurants_url, reviews_url)`
   - This function extracts the spreadsheet ID from the share link
   - Converts it to a CSV export URL: `/export?format=csv`
   - Fetches CSV via HTTP at runtime with `pd.read_csv()`
   - **Data is never persisted** — it's loaded on every app rerun

2. **No Database for Restaurant Data**:
   - Restaurant data (64 Frankfurt entries) is managed manually in Google Sheets
   - The Sheets are the **source of truth**
   - Sales team edits directly in Sheets
   - **CallNotes and chat history ARE stored in PostgreSQL** (database.py)

### Why Google Sheets (from CLAUDE.md)

> "When this becomes painful (too slow, data quality issues, multi-city scale), we migrate to PostgreSQL.
> Until then, don't over-engineer it."

This is intentional — Sheets = editorial data (humans curate), DB = transactional data (app reads/writes).

---

## 2. SECURITY: GOOGLE SHEETS URLS SHOULD BE IN .env

### Current Risk ⚠️

**The URLs are hardcoded in app.py** (line 408-419). This is a **known issue** documented in CLAUDE.md:

> "Google Sheets URLs are currently hardcoded in `app/app.py`. This is a known issue.
> They should become environment variables: `RESTAURANTS_SHEET_URL` and `REVIEWS_SHEET_URL`."

### Problems with Hardcoding

1. **Security**: URLs exposed in source code (visible to anyone with repo access)
2. **Maintenance**: Changing URLs requires code changes + redeploy
3. **Multi-environment**: Can't use different Sheets for prod/staging
4. **Accidental exposure**: URLs might appear in logs/error messages

### Recommended Solution

**Move URLs to environment variables:**

```bash
# .env (never committed)
RESTAURANTS_SHEET_URL=https://docs.google.com/spreadsheets/d/1GzZWRuPr4y3yscDZYprWZtdgZ6Z6MkPBHwRTLH4bPR8/edit?usp=sharing
REVIEWS_SHEET_URL=https://docs.google.com/spreadsheets/d/1zSAd91SkuYgXuIOQa5WVJneEV5dmPyM9XMnI66iNGb4/edit?usp=sharing
```

```bash
# .env.example (committed with placeholders only)
RESTAURANTS_SHEET_URL=https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
REVIEWS_SHEET_URL=https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
```

**Update app.py:**

```python
@st.cache_data(show_spinner=False)
def load_google_data():
    rest_url = os.environ.get("RESTAURANTS_SHEET_URL")
    rev_url = os.environ.get("REVIEWS_SHEET_URL")

    if not rest_url or not rev_url:
        st.error("Missing RESTAURANTS_SHEET_URL or REVIEWS_SHEET_URL in .env")
        st.stop()

    df_rest, df_rev, benchmarks = load_from_google_sheets(rest_url, rev_url)
    # ... rest of logic
```

**With multi-city support:**

```python
CITY_SHEET_URLS = {
    "Frankfurt": {
        "rest": os.environ.get("FRANKFURT_REST_SHEET_URL"),
        "rev": os.environ.get("FRANKFURT_REV_SHEET_URL"),
    },
    "Hamburg": {
        "rest": os.environ.get("HAMBURG_REST_SHEET_URL"),
        "rev": os.environ.get("HAMBURG_REV_SHEET_URL"),
    },
}
```

---

## 3. HAMBURG REVIEWS — DATA QUALITY ASSESSMENT

### Dataset Summary

| Metric | Value |
|--------|-------|
| **Total Reviews** | 1,081 |
| **Unique Restaurants** | 31 |
| **Avg Reviews/Restaurant** | 34.9 |
| **Avg Review Length** | 266 characters |
| **Max Review Length** | 2,140 characters |

### Review Text Completeness ✅ **APPEARS COMPLETE**

| Finding | Status |
|---------|--------|
| Reviews ending with "..." | 4 (0.4%) ✅ |
| Average text length | 266 chars (substantial) ✅ |
| Contains full sentences | Yes ✅ |
| Max length | 2,140 (not truncated) ✅ |

**Conclusion:** The scraping **captured full review text**. The "mehr" (more) button was likely expanded by Octoparse before extraction.

### Distribution Breakdown

```
(0, 50] chars:      134 reviews  (12%)   — Very short (OK - natural variation)
(50, 100] chars:     93 reviews   (9%)   — Short
(100, 200] chars:   284 reviews  (26%)   — Medium
(200, 300] chars:   299 reviews  (28%)   — Medium-Long
(300, 500] chars:   142 reviews  (13%)   — Long
(500-2140] chars:   129 reviews  (12%)   — Very Long
```

### Owner Response Coverage

- **37.9%** of reviews have owner responses (410/1,081)
- This is a critical metric for "responsiveness" scoring

### Rating Bias

```
5★ (Sterne):  899 reviews (83%)  — Heavily positive skew
4★ (Sterne):  106 reviews (10%)
3★ (Sterne):   35 reviews (3%)
2★ (Sterne):   19 reviews (2%)
```

**⚠️ Issue:** 83% 5-star reviews suggests data quality issues:
- Octoparse may be filtering/selecting only positive reviews
- Or: only happy customers leave reviews (selection bias)
- Or: Octoparse picked a subset of restaurants with good ratings

### Review Dates

Most reviews are historical (1-6 years old):
- "vor einem Jahr" (1 year ago): 150 reviews (14%)
- "vor 2 Jahren" (2 years ago): 139 reviews (13%)
- "vor 3 Jahren" (3 years ago): 136 reviews (13%)

**Implication:** Scraper is pulling historical data, not recent reviews.

### Restaurants Data Quality (Hamburg_rest.xlsx)

| Column | Completeness |
|--------|--------------|
| name | 109/109 (100%) ✅ |
| address | 109/109 (100%) ✅ |
| rating | 109/109 (100%) ✅ |
| review_count | 108/109 (99.1%) ✅ |
| website | 104/109 (95.4%) ✅ |
| phone | 103/109 (94.5%) ✅ |
| price | 66/109 (60.6%) ⚠️ |

**Note:** Prices are only 60% complete — this is a limitation of Google Maps data.

---

## 4. RECOMMENDATIONS

### Immediate (Security)

1. **Move Google Sheets URLs to .env** before next deployment
2. **Update .env.example** with placeholders (never real URLs)
3. **Add validation** in app.py to fail fast if URLs are missing

### Short-term (Data Quality)

1. **Verify Octoparse configuration**:
   - Is it clicking "Mehr anzeigen" on ALL reviews?
   - Is it handling pagination (next page)?
   - Are filters being applied (star rating)?

2. **Check for selection bias**:
   - Why are 83% of reviews 5-stars?
   - Is the scraper configured to only get recent reviews?
   - Are very old reviews being collected (1-6 years ago)?

3. **Validate against ground truth**:
   - Pick 5 restaurants
   - Manually check Google Maps
   - Count total reviews vs. what Octoparse captured
   - Check if text matches (same language, same content)

### Medium-term (Architecture)

1. **Create a scraper pipeline** (as documented in CLAUDE.md):
   - Scheduled cron job (weekly?)
   - Incremental updates (only new reviews)
   - Deduplication (avoid duplicates)
   - Direct DB storage (not Google Sheets)

2. **Add tests for data quality**:
   ```python
   # Validate review text is substantial
   assert df_reviews['text_length'].mean() > 200
   # Validate owner response data exists
   assert df_reviews['Owner_response'].notna().sum() > 100
   # Validate mixed ratings (not all 5-stars)
   assert df_reviews['Reviewer_rating'].nunique() > 2
   ```

3. **Consider multi-source reviews**:
   - Google (current)
   - Tripadvisor
   - Yelp
   - Trustpilot
   - Facebook

---

## 5. SUMMARY TABLE

| Question | Answer | Status |
|----------|--------|--------|
| Frankfurt data source? | **Google Sheets** (you were right) | ✅ Confirmed |
| DB or Sheets? | **Sheets for restaurants, DB for call notes** | ✅ Correct architecture |
| URLs in code? | **Yes (hardcoded)** ⚠️ | 🔴 Security issue |
| Should move to .env? | **Yes, immediately** | 📋 TODO |
| Hamburg reviews complete? | **Mostly yes (text is full)** ✅ | ✅ Good quality |
| Truncation in "Reviewer_text"? | **No (0.4% only)** | ✅ Complete |
| Reviews per restaurant? | **35 average** | ⚠️ May be incomplete |
| Quality issues? | **High rating skew (83% 5★)** | ⚠️ Investigate |

---

## Next Steps

1. ✅ **Confirm findings with user** (this document)
2. 📋 **Move URLs to .env** (quick win for security)
3. 🔍 **Audit Octoparse config** (verify scraping rules)
4. 🧪 **Run validation tests** on Hamburg data
5. 📅 **Schedule scraper review** (weekly runs, incremental updates)

