"""
restaurant_chat.py — Restaurant Intelligence Platform
=======================================================
Buffered (non-streaming) AI chat for Praxiotech sales reps.

Architecture:
  - Structured context block injected into the FIRST user message only
  - Subsequent turns pass plain text — Claude retains context in history
  - Non-streaming client.messages.create() — no mid-response drops
  - Call notes from previous visits are loaded and injected automatically
  - Follow-up questions auto-generated after every response

No LangChain, no vector DB — direct structured context injection.
All answers come from real Octoparse data.
"""

import json
import logging
import os
import re as _re
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ── Environment loading (local .env + Streamlit Cloud secrets) ──────────────
def _get_env(key: str, default: str = "") -> str:
    """Get config value: os.environ → st.secrets → default."""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return default

MODEL      = _get_env("CLAUDE_MODEL", "claude-opus-4-6")
MAX_TOKENS = int(_get_env("CLAUDE_MAX_TOKENS", "4096"))
CALL_NOTES_DIR = Path(__file__).resolve().parent / "scripts" / "data" / "call_notes"


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPTS
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are a Praxiotech restaurant intelligence assistant. Praxiotech helps restaurants grow through digital tools: AI review management, Google Business Profile optimisation, review velocity campaigns, sentiment monitoring, and booking infrastructure.

You have been given a complete data package for a specific restaurant — its dimension scores, benchmark comparisons, review sentiment, digital profile, competitor context, and any previous sales call notes.

Answer all questions using only the provided data. Be concise, specific, and commercially focused.
Your role: help a sales rep understand this restaurant's situation and pitch the right Praxiotech products.

IMPORTANT: You MUST always respond in ENGLISH regardless of the language used in the question.

Rules:
- Only use facts from the data package provided. Do not invent statistics.
- Always tie recommendations to concrete numbers (scores, ratings, response rates).
- When gaps exist, name the specific Praxiotech product that closes the gap.
- Use professional but conversational language — this is a sales tool, not a report.
- Format key numbers and recommendations clearly. Use bullet points for lists.
- If previous call notes exist, reference them (known objections, prior discussions).
- If asked something outside the provided data: "I don't have that data in this package."
- Keep responses 200-400 words unless genuinely more is needed.

FOLLOW-UP QUESTIONS:
After every response, add exactly this block on a new line:
<<<FOLLOWUPS>>>
1. [First follow-up question?]
2. [Second follow-up question?]
3. [Third follow-up question?]

Follow-up rules:
- Each question must be under 80 characters.
- Make them specific to what you just discussed — not generic.
- Focus on the next commercially useful insight the sales rep needs.
- Never repeat the question that was just asked.
- Write all follow-up questions in ENGLISH.
"""

SYSTEM_PROMPT_DE = """Du bist ein Praxiotech Restaurant Intelligence-Assistent. Praxiotech hilft Restaurants zu wachsen durch digitale Tools: KI-Bewertungsverwaltung, Google Business Profile-Optimierung, Bewertungsgeschwindigkeit-Kampagnen, Stimmungsüberwachung und Buchungsinfrastruktur.

Du hast ein vollständiges Datenpaket für ein bestimmtes Restaurant erhalten — seine Dimensionswerte, Benchmark-Vergleiche, Bewertungsstimmung, digitales Profil, Wettbewerbskontext und möglicherweise vorherige Verkaufsanrufnotizen.

WICHTIG: Du MUSST immer auf DEUTSCH antworten, unabhängig davon, in welcher Sprache die Frage gestellt wird.

Beantworte alle Fragen nur anhand der bereitgestellten Daten. Sei prägnant, spezifisch und kommerziell fokussiert.
Deine Rolle: Unterstütze einen Vertriebsmitarbeiter dabei, die Situation dieses Restaurants zu verstehen und die richtigen Praxiotech-Produkte zu verkaufen.

Regeln:
- Verwende nur Fakten aus dem bereitgestellten Datenpaket. Erfinde keine Statistiken.
- Beziehe Empfehlungen immer auf konkrete Zahlen (Bewertungen, Sterne, Antwortquoten).
- Wenn es Lücken gibt, nenne das spezifische Praxiotech-Produkt, das die Lücke schließt.
- Verwende professionelle, aber umgangssprachliche Sprache — dies ist ein Sales-Tool, kein Bericht.
- Formatiere wichtige Zahlen und Empfehlungen deutlich. Verwende Aufzählungen für Listen.
- Wenn vorherige Anrufnotizen existieren, beziehe dich auf sie (bekannte Einwände, vorherige Diskussionen).
- Wenn du nach etwas außerhalb der bereitgestellten Daten gefragt wirst: „Ich habe diese Daten nicht in diesem Paket."
- Halte Antworten auf 200-400 Wörter, es sei denn, mehr ist notwendig.

ANSCHLUSSFRAGEN:
Nach jeder Antwort füge genau diesen Block auf einer neuen Zeile hinzu:
<<<FOLLOWUPS>>>
1. [Erste Anschlussfrage?]
2. [Zweite Anschlussfrage?]
3. [Dritte Anschlussfrage?]

Regeln für Anschlussfragen:
- Jede Frage muss unter 80 Zeichen lang sein.
- Mache sie spezifisch für das, was du gerade besprochen hast — nicht allgemein.
- Konzentriere dich auf den nächsten kommerziell wertvollen Einblick, den der Vertriebsmitarbeiter benötigt.
- Wiederhole nie die Frage, die gerade gestellt wurde.
- Schreibe alle Anschlussfragen auf DEUTSCH.
"""


# ─────────────────────────────────────────────────────────────
# PRODUCT PITCH MAP
# ─────────────────────────────────────────────────────────────

_PITCH_MAP = {
    "Responsiveness": (
        "AI Review Manager (120 EUR/mo) — automates owner responses within 2 hours, "
        "turning every review into a booking trust signal."
    ),
    "Digital Presence": (
        "Profile Optimization Bundle (60 EUR/mo) — website audit, Google Business Profile "
        "refresh, booking CTA setup. Converts 3x more Maps viewers to reservations."
    ),
    "Reputation": (
        "Review Velocity Campaign (80 EUR/mo) — SMS post-visit follow-up that targets "
        "15+ new reviews per quarter, strengthening local search ranking."
    ),
    "Visibility": (
        "Engagement Booster (60 EUR/mo) — recency-focused review acquisition that keeps "
        "the Google Maps algorithm ranking the restaurant in the top 3 locally."
    ),
    "Intelligence": (
        "Sentiment Monitoring (80 EUR/mo) — real-time alerts for negative review themes "
        "so the owner can act before they damage the star rating."
    ),
}


# ─────────────────────────────────────────────────────────────
# CALL NOTES — SAVE / LOAD
# ─────────────────────────────────────────────────────────────

def load_call_notes(restaurant_id: str) -> list:
    path = CALL_NOTES_DIR / f"{restaurant_id}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("calls", [])
    except Exception as e:
        logger.warning("Could not load call notes for %s: %s", restaurant_id, e)
        return []


def save_call_notes(restaurant_id: str, call: dict) -> None:
    CALL_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = CALL_NOTES_DIR / f"{restaurant_id}.json"
    existing = load_call_notes(restaurant_id)
    existing.append(call)
    path.write_text(
        json.dumps({"restaurant_id": restaurant_id, "calls": existing}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Call note saved for %s (%d total)", restaurant_id, len(existing))


def delete_call_note(restaurant_id: str, index: int) -> bool:
    """Delete a call note by index and persist changes."""
    CALL_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = CALL_NOTES_DIR / f"{restaurant_id}.json"
    existing = load_call_notes(restaurant_id)
    try:
        existing.pop(index)
    except Exception:
        return False
    try:
        path.write_text(
            json.dumps({"restaurant_id": restaurant_id, "calls": existing}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Call note deleted for %s (%d remaining)", restaurant_id, len(existing))
        return True
    except Exception as e:
        logger.error("Failed to write call notes for %s: %s", restaurant_id, e)
        return False


def _build_call_notes_block(restaurant_id: str) -> str:
    calls = load_call_notes(restaurant_id)
    if not calls:
        return ""
    last = calls[-1]
    products = ", ".join(last.get("products_discussed", [])) or "none noted"
    return (
        f"PREVIOUS SALES CALL ({len(calls)} total on record):\n"
        f"  Date: {last.get('call_date', 'unknown')}\n"
        f"  Contact: {last.get('contact_name', 'not recorded')}\n"
        f"  Interest level: {last.get('interest_level', '?')}/5\n"
        f"  Main objection: {last.get('main_objection', 'none noted')}\n"
        f"  Products discussed: {products}\n"
        f"  Budget mentioned: {last.get('budget_range', 'not discussed')}\n"
        f"  Next steps: {last.get('next_steps', 'none')}\n"
        f"  Rep notes: {last.get('notes', '—')}"
    )


# ─────────────────────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────────────────────

def build_restaurant_context(
    res_name: str,
    res_data,
    scores: dict,
    gaps: dict,
    benchmarks: dict,
    df_rest,
    df_rev,
    cur_rank: int,
    total: int,
    persona: dict,
    momentum,
) -> str:
    """
    Assemble a structured context block for the target restaurant.
    Injected once into the first user message — Claude holds it in history.
    """
    rating    = float(res_data.get("rating_n", 0) or 0)
    rev_count = int(res_data.get("rev_count_n", 0) or 0)
    res_rate  = float(res_data.get("res_rate", 0) or 0)
    health    = scores["Composite"]

    # Momentum summary
    mom_summary = "No momentum data"
    if momentum is not None and len(momentum) > 0:
        avg_vel = momentum["count"].mean()
        recent3 = momentum["count"].tail(3).mean()
        trend   = "ACCELERATING" if recent3 > avg_vel * 1.1 else ("DECLINING" if recent3 < avg_vel * 0.8 else "STABLE")
        mom_summary = f"{avg_vel:.1f} reviews/month avg | 3-month trend: {trend}"

    identity = (
        f"RESTAURANT: {res_name}\n"
        f"HEADLINE METRICS:\n"
        f"  Health Score: {health:.1f}/100 | Rank: #{cur_rank} of {total}\n"
        f"  Google Rating: {rating:.1f}★ | Reviews: {rev_count:,}\n"
        f"  Owner Response Rate: {res_rate*100:.0f}%\n"
        f"  Review Momentum: {mom_summary}"
    )

    dim_lines = ["DIMENSION SCORES (score / benchmark):"]
    bench_targets = {
        "Reputation": benchmarks.get("rating", 4.4) * 20,
        "Responsiveness": 90.0,
        "Digital Presence": 85.0,
        "Intelligence": 75.0,
        "Visibility": 70.0,
    }
    for dim, bench in bench_targets.items():
        sc   = scores.get(dim, 0)
        diff = sc - bench
        icon = "✓" if diff >= 0 else ("!" if diff > -15 else "!!")
        dim_lines.append(f"  {icon} {dim}: {sc:.0f} / {bench:.0f} (gap: {diff:+.0f})")
    dim_block = "\n".join(dim_lines)

    # Top gaps → product pitches
    top_gaps = sorted(
        [(d, bench_targets[d] - scores.get(d, 0)) for d in bench_targets],
        key=lambda x: x[1], reverse=True
    )
    pitch_lines = ["KEY GAPS & PRAXIOTECH SOLUTIONS:"]
    for dim, gap in top_gaps[:3]:
        if gap > 0:
            pitch = _PITCH_MAP.get(dim, "See Praxiotech product catalogue.")
            severity = "CRITICAL" if gap > 25 else ("OPPORTUNITY" if gap > 10 else "MINOR")
            pitch_lines.append(f"  [{severity}] {dim} (gap: +{gap:.0f}): {pitch}")
    if len(pitch_lines) == 1:
        pitch_lines.append("  Restaurant is at or near benchmark — focus on growth & retention.")
    pitch_block = "\n".join(pitch_lines)

    # Persona
    persona_block = (
        f"CUSTOMER PERSONA:\n"
        f"  Primary: {persona['primary']}\n"
        f"  Segment: {persona['segment']}\n"
        f"  Motivation: {persona['motivation']}"
    )

    # Sample reviews
    review_texts = res_data.get("_review_texts", [])
    if isinstance(review_texts, list) and review_texts:
        excerpts = "\n".join(f"  - {t[:280]}" for t in review_texts[:8])
        review_block = f"SAMPLE CUSTOMER REVIEWS:\n{excerpts}"
    else:
        review_block = "SAMPLE CUSTOMER REVIEWS: None available in dataset."

    # Competitors (top 3 by score in same dataset)
    competitor_lines = ["TOP COMPETITORS IN DATASET:"]
    try:
        from scoring_engine import compute_all_ranks
        df_ranks = compute_all_ranks(df_rest, df_rev)
        others = df_ranks[df_ranks["name"] != res_name].head(3)
        for _, row in others.iterrows():
            r_data = df_rest[df_rest["name"] == row["name"]].iloc[0]
            competitor_lines.append(
                f"  #{row['rank']}. {row['name']} — score {row['score']:.0f}/100 | "
                f"{r_data.get('rating_n', 0):.1f}★ ({int(r_data.get('rev_count_n', 0)):,} reviews) | "
                f"Response rate: {r_data.get('res_rate', 0)*100:.0f}%"
            )
    except Exception as e:
        competitor_lines.append(f"  Could not compute ({e})")
    competitor_block = "\n".join(competitor_lines)

    # Benchmarks
    market_block = (
        f"MARKET CONTEXT:\n"
        f"  Dataset size: {total} restaurants | Benchmark (top 25%): avg rating {benchmarks.get('avg_rating',0):.2f}★ | "
        f"Median reviews: {int(benchmarks.get('median_reviews',0)):,} | "
        f"Benchmark response rate: {benchmarks.get('response_rate',0)*100:.0f}%"
    )

    # Call notes
    restaurant_id = res_name.lower().replace(" ", "_").replace("-", "_")[:40]
    call_notes_block = _build_call_notes_block(restaurant_id)

    parts = [identity, dim_block, pitch_block, persona_block, review_block, competitor_block, market_block]
    context = "\n\n".join(parts)
    if call_notes_block:
        context += "\n\n" + call_notes_block

    logger.info(
        "Context built for '%s' — %d chars (~%d tokens) | call notes: %s",
        res_name, len(context), len(context) // 4,
        "yes" if call_notes_block else "none",
    )
    return context


# ─────────────────────────────────────────────────────────────
# GET RESPONSE — buffered, non-streaming
# ─────────────────────────────────────────────────────────────

def get_response(messages: list, restaurant_context: str, language: str = "EN") -> str:
    """
    Non-streaming Claude response. Context injected on first turn only.

    Args:
        messages: list of {"role": "user"/"assistant", "content": "..."} dicts
        restaurant_context: full data block — injected into first user message
        language: "EN" for English or "DE" for German

    Returns:
        Full response text as a string.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # Fallback 1: Streamlit Cloud secrets (works on hosted deployments)
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass

    # Fallback 2: local .env file (works on localhost)
    if not api_key:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    logger.info("get_response — model: %s | api_key: %s", MODEL, "present" if api_key else "MISSING")

    if not api_key:
        return (
            "**ANTHROPIC_API_KEY not configured.**\n\n"
            "Add `ANTHROPIC_API_KEY=sk-ant-...` to your `.env` file and restart the app."
        )

    try:
        import httpx
    except ImportError:
        return (
            "**Error: httpx library not installed**\n\n"
            "Please install it with:\n"
            "`pip install httpx`\n\n"
            "Or if using uv:\n"
            "`uv pip install httpx`"
        )

    try:
        import anthropic
    except ImportError:
        return (
            "**Error: Anthropic client library not installed.**\n\n"
            "The app can use Anthropic for AI responses, but the `anthropic` Python package is required.\n"
            "Install it in your environment with:\n"
            "`pip install anthropic httpx`\n\n"
            "After installing, restart the Streamlit app."
        )

    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=httpx.Timeout(60.0, read=180.0),
        )
    except Exception as e:
        logger.error("Failed to initialize Anthropic client: %s", e)
        return (
            f"**Error initializing AI assistant: {str(e)}**\n\n"
            "Please check your ANTHROPIC_API_KEY and try again."
        )

    api_messages = []
    for i, msg in enumerate(messages):
        if i == 0 and msg["role"] == "user":
            content = f"[RESTAURANT DATA PACKAGE]\n\n{restaurant_context}\n\n[QUESTION]\n{msg['content']}"
        else:
            content = msg["content"]
        api_messages.append({"role": msg["role"], "content": content})

    try:
        # Select language-specific system prompt
        system_prompt = SYSTEM_PROMPT_DE if language.upper() == "DE" else SYSTEM_PROMPT_EN

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=api_messages,
        )
        text = response.content[0].text
        logger.info("Response received — %d chars | tokens in/out: %d/%d",
                    len(text), response.usage.input_tokens, response.usage.output_tokens)
        return text
    except Exception as e:
        logger.error("Anthropic/API error or other failure: %s", e)
        return f"[Claude API error: {e}]"


# ─────────────────────────────────────────────────────────────
# FOLLOW-UP PARSING
# ─────────────────────────────────────────────────────────────

def parse_followups(text: str) -> tuple:
    """Split response into (display_text, [followup_questions])."""
    marker = "<<<FOLLOWUPS>>>"
    if marker not in text:
        return text.strip(), []

    main_part, fu_part = text.split(marker, 1)
    questions = []
    for line in fu_part.strip().splitlines():
        line = _re.sub(r"^\d+\.\s*", "", line.strip()).strip()
        if line and len(line) > 5:
            if not line.endswith("?"):
                line += "?"
            questions.append(line)
        if len(questions) >= 3:
            break
    return main_part.strip(), questions


# ─────────────────────────────────────────────────────────────
# SUGGESTED QUESTIONS — EN + DE
# ─────────────────────────────────────────────────────────────

_GAP_QUESTIONS_EN = {
    "Responsiveness":   "Why is the response rate so low, and what's the revenue impact?",
    "Digital Presence": "What's the impact of missing booking infrastructure?",
    "Reputation":       "How does review volume compare to competitors?",
    "Visibility":       "What does the review recency trend tell us?",
    "Intelligence":     "What sentiment themes are driving the current rating?",
}

_GAP_QUESTIONS_DE = {
    "Responsiveness":   "Warum ist die Antwortrate so niedrig, und welchen Umsatzeinfluss hat das?",
    "Digital Presence": "Welche Auswirkungen hat die fehlende Buchungsinfrastruktur?",
    "Reputation":       "Wie vergleicht sich das Bewertungsvolumen mit Mitbewerbern?",
    "Visibility":       "Was sagt uns der Aktualitätstrend der Bewertungen?",
    "Intelligence":     "Welche Stimmungsthemen beeinflussen die aktuelle Bewertung?",
}

_GENERAL_QUESTIONS_EN = [
    "What objections should I expect, and how do I handle them?",
    "What's the fastest win Praxiotech can deliver here in 30 days?",
    "How should I open this sales conversation?",
    "If the owner has a €200/month budget, what's the single best product?",
    "Give me a one-sentence pitch I can open the call with.",
    "What would closing this client be worth to Praxiotech annually?",
    "What does this restaurant do better than its top 3 competitors?",
    "Which Praxiotech products are the best fit here, and why?",
]

_GENERAL_QUESTIONS_DE = [
    "Welche Einwände sollte ich erwarten, und wie gehe ich damit um?",
    "Was ist der schnellste Erfolg, den Praxiotech hier in 30 Tagen erzielen kann?",
    "Wie sollte ich dieses Verkaufsgespräch eröffnen?",
    "Wenn der Inhaber ein Budget von 200 €/Monat hat, was ist das beste Produkt?",
    "Gib mir einen Ein-Satz-Pitch, mit dem ich das Gespräch eröffnen kann.",
    "Was wäre der Jahreswert für Praxiotech, wenn dieser Kunde gewonnen wird?",
    "Was macht dieses Restaurant besser als seine Top-3-Konkurrenten?",
    "Welche Praxiotech-Produkte passen hier am besten, und warum?",
]


def get_suggested_questions(gaps: dict, res_name: str, language: str = "EN") -> list:
    """Return first 4 questions for the initial chip row — in the selected language."""
    is_de = language.upper() == "DE"
    gap_q = _GAP_QUESTIONS_DE if is_de else _GAP_QUESTIONS_EN
    gen_q = _GENERAL_QUESTIONS_DE if is_de else _GENERAL_QUESTIONS_EN

    if is_de:
        summary_q = f"Fassen Sie die 3 wichtigsten Verkaufsargumente für {res_name} zusammen."
    else:
        summary_q = f"Summarise the top 3 pitch points for {res_name}."

    questions = []
    top_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)
    for dim, gap_val in top_gaps:
        if gap_val > 0 and dim in gap_q:
            questions.append(gap_q[dim])
    questions.append(summary_q)
    for q in gen_q:
        if q not in questions:
            questions.append(q)
    return questions[:4]


def get_all_questions(gaps: dict, res_name: str, language: str = "EN") -> list:
    """Return full ordered question pool (up to 12) — in the selected language."""
    is_de = language.upper() == "DE"
    gap_q = _GAP_QUESTIONS_DE if is_de else _GAP_QUESTIONS_EN
    gen_q = _GENERAL_QUESTIONS_DE if is_de else _GENERAL_QUESTIONS_EN

    if is_de:
        summary_q = f"Fassen Sie die 3 wichtigsten Verkaufsargumente für {res_name} zusammen."
    else:
        summary_q = f"Summarise the top 3 pitch points for {res_name}."

    questions = []
    top_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)
    for dim, gap_val in top_gaps:
        if gap_val > 0 and dim in gap_q:
            questions.append(gap_q[dim])
    questions.append(summary_q)
    for q in gen_q:
        if q not in questions:
            questions.append(q)
    return questions[:12]


def get_similar_questions(last_question: str, response: str, restaurant_name: str, gaps: dict, language: str = "EN") -> list:
    """
    Generate 3 similar/related questions based on the last question and response.
    Uses Claude to understand context and suggest logical follow-ups.

    Args:
        last_question: The user's last question
        response: Claude's response to that question
        restaurant_name: Target restaurant name
        gaps: Gap analysis dict for context
        language: "EN" or "DE"

    Returns:
        List of 2-3 similar question suggestions in the selected language
    """
    import os
    try:
        import anthropic
    except ImportError:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # Fallback: Streamlit Cloud secrets
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass

    if not api_key:
        return []

    is_de = language.upper() == "DE"

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=__import__('httpx').Timeout(15.0, read=30.0))

        if is_de:
            prompt = f"""Du hilfst einem Vertriebsmitarbeiter, tiefer in Erkenntnisse über die Restaurantleistung einzutauchen.

Restaurant: {restaurant_name}
Letzte Frage des Vertriebsmitarbeiters: {last_question}
Claudes Antwort (Auszug): {response[:500]}

Erstelle 3 ähnliche/verwandte Fragen, die der Vertriebsmitarbeiter als nächstes stellen könnte. Diese sollen:
1. Das gleiche Thema aus einem anderen Blickwinkel untersuchen
2. Tiefer in nicht vollständig abgedeckte Details eintauchen
3. Sich von typischen Folgefragen unterscheiden

Formatiere als nummerierte Liste, halte jede unter 100 Zeichen. Schreibe alle Fragen auf DEUTSCH."""
            system_msg = "Du bist ein Verkaufsexperte, der strategische Folgefragen auf Deutsch generiert. Halte die Fragen spezifisch und umsetzbar."
        else:
            prompt = f"""You are helping a sales rep dig deeper into insights about restaurant performance.

Restaurant: {restaurant_name}
Sales Rep's Last Question: {last_question}
Claude's Response (excerpt): {response[:500]}

Generate 3 similar/related questions the sales rep might ask next. These should:
1. Explore the same topic but from a different angle
2. Dig deeper into specifics not fully covered
3. Be distinct from typical follow-ups (don't just rephrase the response)

Format as numbered list, keep each under 100 chars. Write all questions in ENGLISH."""
            system_msg = "You are a sales expert helping generate strategic follow-up questions in English. Keep questions specific and actionable."

        msg = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=system_msg,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text if msg.content else ""
        questions = []
        for line in text.splitlines():
            line = _re.sub(r"^\d+\.\s*", "", line.strip()).strip()
            if line and len(line) > 5 and not line.startswith("*"):
                if not line.endswith("?"):
                    line += "?"
                questions.append(line)
                if len(questions) >= 3:
                    break
        return questions[:3]
    except Exception:
        return []


def get_next_best_action(res_name: str, call_history: list, scores: dict, gaps: dict) -> str:
    """
    Suggest next best action based on call history and restaurant metrics.
    """
    from datetime import datetime, timedelta

    if not call_history:
        largest_gap = max(gaps.values()) if gaps else 0
        top_gap_dim = max(gaps.items(), key=lambda x: x[1])[0] if gaps else "Responsiveness"
        return f"🎯 OPENING: Lead with {top_gap_dim} gap (${largest_gap:.0f} opportunity). Use this pitch: \"{_PITCH_MAP.get(top_gap_dim, 'See our product catalogue.')}\""

    last_call = call_history[-1]
    call_date = datetime.strptime(last_call.get("call_date", "1900-01-01"), "%Y-%m-%d")
    days_since = (datetime.now() - call_date).days
    interest = last_call.get("interest_level", 2)
    objection = last_call.get("main_objection", "").lower()

    if days_since > 14:
        if interest >= 4:
            return "🔥 URGENT CLOSE: High interest for 2+ weeks. Send contract + 48hr deadline. This deal is slipping."
        elif interest >= 2:
            return "⏰ RE-ENGAGE: 2 weeks passed. Send case study from similar restaurant + ask 'any new budget allocated?'"
        else:
            return "📌 RECONSIDER: Low interest + time passed. Pause this opportunity, mark for Q4 re-approach."
    elif days_since > 7:
        if interest >= 4:
            return "🎬 MOVE TO CLOSE: Interest high + week has passed. Schedule product demo + pricing discussion."
        elif interest >= 2:
            return "📧 SEND PROOF: Share customer success story matching their gap. Follow up in 3 days."
        else:
            return "💭 REPOSITION: Low interest. Identify real blocker - budget? Wrong product? Schedule brief call to clarify."
    elif days_since >= 3:
        if interest >= 4:
            return "✅ CLOSING WINDOW OPEN: Send proposal with flexible terms. Goal: signature within 48 hours."
        elif interest >= 2:
            return f"💡 OVERCOME OBJECTION: They said '{objection}'. Response strategy: show ROI calculation + free trial."
        else:
            return "🤔 UNDERSTAND HESITATION: Ask direct question: 'What would need to change for this to work?' Listen on next call."
    else:
        if interest >= 4:
            return "🚀 MOMENTUM: Strike while hot. Send proposal today + schedule follow-up for 24 hours."
        elif interest >= 2:
            return "📞 MILD INTEREST: Send additional resources addressing their main concern. Re-contact in 3 days."
        else:
            return "❓ UNCLEAR SIGNAL: Low interest but engaged. Send thank-you + soft CTA: 'Happy to answer questions.'"

    return "No action history to guide - use Opening pitch above."