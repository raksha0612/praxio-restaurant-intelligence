# CLAUDE.md — Restaurant Intelligence Platform
> This file is the source of truth for how we think, build, and ship on this project.
> Read it fully before touching any code. Update it after every significant decision.

---

## What This Product Is

**Restaurant Intelligence** is a B2B sales intelligence tool for Praxiotech.
Sales reps use it to walk into a meeting with a restaurant and know exactly where that restaurant
is losing money — slow review responses, poor digital presence, invisible reputation.
Then close them on Praxiotech's product.

The data pipeline is: **Google Sheets (source of truth) → Pandas → Streamlit UI**.
Call notes and chat sessions are persisted in: **PostgreSQL (prod) / SQLite (dev)**.
The AI layer is: **Claude Opus for chat + PDF reports**.

This is an internal tool. One user (sales rep). Clarity and speed beat everything else.

---

## Mandatory Workflow — Every Single Task

No exceptions. This is how we work:

```
1. PLAN      → Lay out the full approach before writing a single line
2. SUBTASKS  → Break it into small, named steps (each step = one thing)
3. FINALIZE  → User confirms the plan before implementation starts
4. IMPLEMENT → Execute step by step, explain the why on each decision
5. REVIEW    → Re-read every changed file. Question it. Is it simpler? Is it correct?
6. QUESTION  → Flag anything uncertain. Ask. Never assume.
```

**Claude must ask before assuming.** If there are two ways to do something, present both with tradeoffs.
If a task touches infrastructure (DB schema, Docker, deploy scripts, Google Sheets), always confirm before running.

---

## Architecture — How the System Works

```
┌─────────────────────────────────────────────────────────┐
│                    Hetzner CX22                          │
│  178.104.78.225  (Ubuntu 24.04)                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  praxio_restaurant  — Streamlit :8502              │ │
│  │  Python 3.13                                       │ │
│  │  Reads data: Google Sheets (HTTP at runtime)       │ │
│  │  Reads/writes: PostgreSQL (call notes, history)    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Data flow:
  Google Sheets ──HTTP──▶ data_audit.py ──▶ Pandas DataFrames (in memory)
  Call notes (UI) ──▶ database.py ──▶ PostgreSQL
  Chat context ──▶ restaurant_chat.py ──▶ Claude API ──▶ response
```

**Why Google Sheets and not a DB for restaurant data?**
The restaurant dataset is updated manually — sales team adds restaurants, updates info.
Sheets gives non-technical users a familiar interface to maintain the data.
When this becomes painful (too slow, data quality issues, multi-city scale), we migrate to PostgreSQL.
Until then, don't over-engineer it.

**Why PostgreSQL for call notes but Sheets for restaurant data?**
Call notes are transactional — created, updated, queried by the app in real time.
That's what a database is for. Restaurant data is editorial — humans curate it.
That's what a spreadsheet is for. Use the right tool for the right job.

**Why Streamlit (for now)?**
Fast to build, works for one internal user. When it becomes clearly painful
(slow rerenders, multi-user auth, mobile UX, complex state) we evaluate a proper frontend.
Not before. "Not sure" is not a reason to rebuild. Identify the specific pain first.

---

## File Responsibilities — Who Owns What

Every file has ONE job. If a file is doing two jobs, split it.

| File | Owns | Does NOT own |
|------|------|--------------|
| `app/app.py` | Streamlit UI only — layout, widgets, CSS, user interaction | Business logic, DB queries, scoring |
| `data_audit.py` | Load from Google Sheets → clean → enrich DataFrames | Scoring, UI, PDF |
| `scoring_engine.py` | 5-dimension scores, composite, silent winner, persona, gaps | Data loading, UI, AI |
| `restaurant_chat.py` | Claude API calls, context building, follow-up parsing | UI rendering, DB writes |
| `database.py` | All DB reads/writes for call notes + score history | Restaurant data (that's Sheets) |
| `report_generator.py` | PDF generation with ReportLab | Data loading, scoring |
| `excel_exporter.py` | Excel export of call notes + pipeline summary | Everything else |
| `translations.py` | EN/DE string dictionary + `t()` helper | Anything else |

**If you find business logic in `app.py`, move it out. No exceptions.**
**`get_actionable_solutions` and `get_rating_split` live in `scoring_engine.py`. Not in `app.py`.**

---

## Scoring System — Understand This Before Touching It

Five dimensions. Each has a weight. Composite = weighted sum.

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Reputation | 30% | Star rating quality + review volume |
| Responsiveness | 25% | % of reviews with owner reply |
| Digital Presence | 20% | Website + phone + booking platform |
| Intelligence | 15% | Sentiment derived from review ratings |
| Visibility | 10% | Recency-weighted review velocity |

**Why these weights?**
Reputation and responsiveness drive the most immediate revenue impact for a restaurant.
A restaurant with 4.8 stars that never replies to reviews is leaving money on the table —
that's the exact pitch our product solves. The weights reflect the sales narrative.

**Silent Winner** = rating ≥ 4.5 AND response rate < 30%.
This is our best prospect. High quality, low digital effort. Easy sell.

Do not change the weights without a business reason and a data analysis to back it up.

---

## Code Standards — Non-Negotiable

### Functions must be short and explainable
- **Target: 10–20 lines per function.** If it's longer, it's doing more than one thing.
- Every function should be explainable in one sentence. If you can't, split it.
- Name functions by what they DO: `calculate_response_rate()` not `response_rate_calc()`.

### Why short functions
A 15-line function has one bug path. A 100-line function has ten.
Short functions are testable, readable, and safe to change.
When a function is short, its name IS the documentation.

### Imports
- All imports at the top of the file. Never inside functions (except guarded `try: import anthropic`).
- Standard library → third-party → local. One blank line between groups.
- No star imports. Always name what you import.

### Error handling
- Never use bare `except:`. Always `except Exception as e:` minimum.
- Log it: `logger.warning("context: %s", e)`. Silent failures hide bugs.
- Return a safe default. Let the caller decide what to do with it.

### Comments
- Comments explain WHY, not WHAT. The code shows what. The comment explains why.
- If logic took more than 5 minutes to figure out, it needs a comment.
- No commented-out code. Git history remembers everything.

### Type hints
- Always type-hint function signatures.
- `Optional[X]` for values that can be None. Don't hide it.

### Google Sheets URLs
These are currently hardcoded in `app/app.py`. This is a known issue.
They should become environment variables: `RESTAURANTS_SHEET_URL` and `REVIEWS_SHEET_URL`.
When we move them, add to `.env` and `.env.example` (with placeholder only — never real URLs in example).

---

## Brand Colors — Memorise These

```python
NAVY     = "#0F172A"   # primary text — very dark blue
TEAL     = "#0EA5E9"   # primary accent — sky blue
TEAL2    = "#14B8A6"   # secondary accent — teal green
BG       = "#F0F4F8"   # app background
WHITE    = "#FFFFFF"   # cards, inputs
MUTED    = "#64748B"   # secondary text
SUCCESS  = "#22C55E"
WARNING  = "#F59E0B"
DANGER   = "#EF4444"
BORDER   = "#E2E8F0"
ACCENT   = "#2563EB"
SECONDARY = "#8B5CF6"
```

**Sidebar:** dark navy gradient. `[data-testid="stSidebar"] *` → `color: #CBD5E1`.
Any custom class inside the sidebar must use light/white-family colors.

---

## Known Gotchas — Lessons Paid For

Do not repeat these mistakes.

### 1. Call notes split-brain (FIXED — stay vigilant)
Call notes are saved to DB via `database.py`. Chat context (`_build_call_notes_block`) previously
read from flat JSON files — meaning notes saved via the UI were invisible to Claude.
**Rule: `_build_call_notes_block` reads from DB first. Flat file is fallback only.**
Never add a new way to save call notes without also updating the chat context reader.

### 2. Duplicate functions cause silent staleness
`get_actionable_solutions` and `get_rating_split` were duplicated in `app.py` and `scoring_engine.py`.
When one was updated, the other wasn't. The rule: **each function exists in exactly one place.**
If `app.py` needs it, import it. Never redefine it.

### 3. Unreachable code hides logic errors
`get_next_best_action` had a return statement after a complete if/elif/else chain — unreachable.
This suggests the function logic was incomplete. Before adding an else/fallback, check: can all code paths
actually reach it? If not, the function has a structural bug.

### 4. Streamlit config.toml must be COPY'd into Docker
Same rule as salon: the `[theme]` section with `textColor` must be in the image.
Generate it at build time and you lose the theme → white-on-white text in prod.

### 5. `_synthetic_momentum` is non-deterministic
When real momentum data isn't available, it generates random numbers. Every rerender shows different data.
This is misleading. Either show a "no data" state or use `np.random.seed(42)` for consistency.
Don't show fake data that looks real.

### 6. docker-compose healthcheck uses `start_period` (underscore)
Not `start-period` (hyphen). The hyphen causes a validation error and the container won't start.
Check this every time you touch `docker-compose.yml`.

---

## Git Workflow — Rules

We use short-lived feature branches. `main` is always deployable.

### Branch naming (Claude proposes and explains, you confirm before creating)
```
feat/short-description      # new feature
fix/short-description       # bug fix
data/source-name            # data pipeline changes
chore/short-description     # infra, deps, config
test/short-description      # adding tests
refactor/short-description  # code restructure, no behaviour change
```

### Rules
1. Claude proposes the branch name and explains why before creating it.
2. Never commit directly to `main`. Always branch + PR, even solo.
3. One PR = one thing. No mixing bug fixes with features.
4. PR description must state: what changed, why, and how to test it manually.
5. No force pushes to `main`. Ever.
6. `.env` is never committed. Check `.gitignore` before every first commit on a branch.

### Commit message format
```
type(scope): short description

Why: reason for this change
```
Examples:
```
fix(chat): read call notes from DB instead of flat files
Why: notes saved via UI went to DB but chat context read flat files — split-brain bug

feat(scoring): add momentum chart seed for deterministic output
Why: random seed prevents chart from changing on every rerender, misleading users
```

---

## Deploy Workflow

```bash
# From praxio-restaurant-intelligence/ directory
export PRAXIO_SERVER_IP=178.104.78.225
bash deploy/deploy.sh
```

**What this does:**
1. rsync all files (except .git, .venv, __pycache__, .env) to `/opt/praxiotech/restaurant-intelligence/`
2. Copies `.env` separately via scp (secrets never go through rsync with other files)
3. SSH → `docker compose up -d --build`
4. Health check: waits 10s, runs `docker compose ps`

**SSH key:** `~/.ssh/id_ed25519_praxio`
**Container name:** `praxio_restaurant`
**App URL:** `http://178.104.78.225:8502`

After every deploy: open the URL and verify the app loads, data loads, and chat responds.
Don't just trust the health check — the health check only checks if the process is alive.

---

## Testing Strategy

### Why we test
Tests are the proof that the code does what we think it does.
Without tests, every refactor is a gamble. With tests, refactors are safe.
Tests also document behaviour — reading a test tells you exactly what the code should do.

### Test structure (to be built)
```
tests/
  unit/
    test_scoring_engine.py       # pure math — no DB, no API, no Sheets
    test_data_audit.py           # data loading + enrichment logic (mocked Sheets)
    test_report_generator.py     # PDF generation (check structure, not content)
  integration/
    test_database.py             # real DB operations against a test DB
    test_restaurant_chat.py      # Claude API (mock + real)
  scenarios/
    chat_scenarios.py            # named conversations — see below
```

### Chat testing — three levels

**Level 1 — Mock (fast, always runs, no API cost):**
Mock `anthropic.Anthropic()`. Assert that:
- The context block sent to Claude contains the restaurant name
- The context block includes the correct score breakdown
- Call notes from DB are included when they exist
- The system prompt is in the right language (EN vs DE)

**Level 2 — Real API (run manually before release):**
Hit the real Claude API with a fixed restaurant context. Assert:
- Response contains the restaurant name
- Response mentions at least one specific gap dimension
- `parse_followups()` correctly extracts follow-up questions
- Response is within acceptable token length

**Level 3 — Chat scenario explorer (to build):**
A dedicated page or standalone script listing named conversation scenarios:
```python
SCENARIOS = [
    {
        "name": "Cold open — silent winner restaurant",
        "restaurant": {"name": "Osteria Roma", "rating_n": 4.8, "response_rate": 12},
        "call_notes": [],
        "question": "What's the best opening pitch for this restaurant?",
        "expect_contains": ["response rate", "silent winner", "12%"],
    },
    {
        "name": "Second call — budget objection",
        "restaurant": {...},
        "call_notes": [{"interest_level": 3, "main_objection": "too expensive"}],
        "question": "How do I overcome the budget objection?",
        "expect_contains": ["ROI", "cost", "120"],
    },
]
```
This lets you explore Claude's behaviour across representative sales situations.
Run it before any release that touches `restaurant_chat.py`.

### Running tests (once scaffolded)
```bash
pytest tests/unit/              # fast, no external deps
pytest tests/integration/       # needs DB
python tests/scenarios/chat_scenarios.py  # needs API key, run manually
```

---

## Scraper Roadmap (Restaurant Data)

Currently restaurant data comes from Google Sheets (manually curated).
The next step is adding a scraper pipeline similar to salon-intelligence.

### What the scraper will do
1. Search Google Maps for restaurants in a city/district
2. Extract: name, address, rating, review count, reply rate, website, phone, booking platform
3. Scrape recent reviews (last 90 days)
4. Write to Google Sheets OR directly to PostgreSQL (decision pending)

### CLI target
```bash
python scripts/scrape.py --city Munich --type restaurant --limit 300
```

### Build order
1. Shared scraper base class (reuse salon scraper logic — don't duplicate)
2. Restaurant-specific extractor (different fields from salon)
3. Google Sheets writer OR PostgreSQL direct insert (decide when we get here)
4. Deduplication (`ON CONFLICT DO UPDATE`)
5. Incremental reviews (only new reviews since last run)
6. Scheduling (weekly cron on Hetzner)

---

## What Claude Must Always Do

- **Read the relevant files before suggesting changes.** No assumptions.
- **State the full plan and get confirmation before implementing anything non-trivial.**
- **Explain the why.** Every decision, every pattern, every tradeoff — explain it.
- **Question the current code.** If something looks fragile, say so and propose the fix.
- **Update this CLAUDE.md** after every significant architectural decision.
- **Propose the branch name and explain it** before creating a branch.
- **Run the deploy and open the app** after every deployment — don't just check `docker compose ps`.
- **After every change ask:** does this need a test? If yes, write the test before closing the task.
- **When in doubt, ask.** A 30-second question beats a 30-minute wrong implementation.

## What Claude Must Never Do

- **Never assume a file hasn't changed.** Always re-read before editing.
- **Never put business logic in `app.py`.** UI only.
- **Never define a function that already exists in `scoring_engine.py`** inside `app.py`.
- **Never commit `.env`** or any file containing secrets or real API keys.
- **Never push directly to `main`.** Always a branch.
- **Never use bare `except:`.** Always `except Exception as e:`.
- **Never save call notes via a new path** without also updating `_build_call_notes_block`.
- **Never add random/synthetic data** to a chart without making it obviously labelled as synthetic.
- **Never deploy without explaining what will change**, even for a "small" fix.
- **Never close a task without asking:** is there a test we should write for this?
