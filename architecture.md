# Restaurant Intelligence Engine — Architecture

## Overview

```
restaurant-intelligence/
├── app/
│   ├── app.py                ← Streamlit dashboard (3 tabs)
│   ├── data_audit.py         ← Octoparse CSV loader + enrichment
│   ├── scoring_engine.py     ← 5-dimension scoring + composite + persona
│   ├── restaurant_chat.py    ← Claude AI chat + context builder + call notes
│   ├── report_generator.py   ← 6-page PDF export (ReportLab + matplotlib)
│   └── data/                 ← Upload CSVs here (gitignored)
├── scripts/
│   └── data/call_notes/      ← JSON call notes per restaurant (gitignored)
├── docs/
│   └── architecture.md
├── logs/
├── pyproject.toml            ← uv project definition
├── do                        ← Run script (./do install / ./do app)
├── .python-version           ← 3.13
├── .env.example
├── .gitignore
└── README.md
```

## Scoring Logic

| Dimension | Weight | Source |
|-----------|--------|--------|
| Reputation | 30% | `(rating/5)×70 + min(reviews/500,1)×30` |
| Responsiveness | 25% | `replied_reviews / total_reviews × 100` |
| Digital Presence | 20% | website(50) + phone(25) + base(15) + price bonus |
| Intelligence | 15% | `((avg_review_rating-1)/4) × 100` |
| Visibility | 10% | `(reviews_in_90d×0.7 + reviews_in_180d×0.3) / total` |
| **Composite** | 100% | Weighted sum |

## AI Chat Architecture

1. On restaurant select → `build_restaurant_context()` assembles structured data block
2. Context injected into first user message only (not repeated each turn)
3. Claude retains context in conversation history
4. Each response ends with `<<<FOLLOWUPS>>>` block for 3 clickable questions
5. Call notes auto-loaded and injected into context if they exist

## Data Flow (Octoparse → Dashboard)

```
Octoparse → restaurants.csv + reviews.csv
                    ↓
              data_audit.py
          (load → clean → enrich)
                    ↓
           scoring_engine.py
        (5 dimensions + composite)
                    ↓
              app.py
     (dashboard + chat + call notes)
```

## PostgreSQL Migration Path

When ready to scale:
1. Replace `data_audit.load_and_clean_data()` with SQLAlchemy queries
2. Replace `save_call_notes()` JSON files with a `call_notes` table
3. Scheduled ETL: Octoparse export → staging table → production
4. Consider FastAPI + Streamlit separation for multi-user workloads
5. Streamlit remains valid for internal tools; swap to Next.js for public-facing
