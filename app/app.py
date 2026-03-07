"""
app.py - Restaurant Intelligence Engine v2.0
"""
import base64
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
except ImportError:
    pass

import streamlit as st

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_audit import load_from_google_sheets, find_col, load_and_clean_data
from scoring_engine import (
    compute_dimension_scores,
    get_gap_analysis,
    compute_momentum,
    get_silent_winner_flag,
    get_customer_persona,
    compute_all_ranks,
    identify_silent_winners,
    calculate_silent_winner_opportunity,
    calculate_deal_probability,
)
from report_generator import generate_pdf_report
from restaurant_chat import (
    build_restaurant_context, get_response, get_suggested_questions,
    get_all_questions, load_call_notes, save_call_notes, parse_followups,
    get_next_best_action, delete_call_note, get_similar_questions,
)
from translations import t

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


# ── HELPER FUNCTIONS (defined here so no import needed from scoring_engine) ──

def get_actionable_solutions(res_name, res_data, top_gaps, language="EN"):
    rating  = float(res_data.get("rating_n", 4.6) or 4.6)
    est_pts = min(int(top_gaps[0][1] * 0.6), 999) if top_gaps else 0
    if language.upper() == "DE":
        return [
            {"emoji": "⚡", "title": "Antwortzeit optimieren",      "priority": "HOCH",    "priority_color": "#DC2626",
             "desc": "Durchschn. Antwortzeit auf unter 2 Stunden senken - wichtigster Umsatzhebel",
             "est": f"Est. +{est_pts} Punkte Score-Steigerung"},
            {"emoji": "⭐", "title": "Bewertungskampagne starten",   "priority": "MITTEL",  "priority_color": "#F59E0B",
             "desc": "Ziel: 15 neue Bewertungen dieses Quartal via Post-Visit SMS",
             "est": "Est. +12% Sichtbarkeit"},
            {"emoji": "🔗", "title": "Google Profil aktualisieren", "priority": "NIEDRIG", "priority_color": "#10B981",
             "desc": "Fotos, Menulinks & Buchungs-CTA aktualisieren",
             "est": "Est. +8% CTR"},
            {"emoji": "🤖", "title": "KI-Bewertungsmanagement",     "priority": "HOCH",    "priority_color": "#DC2626",
             "desc": "Personalisierte Antworten automatisieren - 120 EUR/Mo",
             "est": "Est. 3x Antwortrate"},
            {"emoji": "📡", "title": "Stimmungsueberwachung",       "priority": "MITTEL",  "priority_color": "#F59E0B",
             "desc": "Echtzeit-Benachrichtigungen fuer negative Bewertungen auf allen Plattformen",
             "est": f"{rating:.1f} Sterne Bewertung schuetzen"},
        ]
    return [
        {"emoji": "⚡", "title": "Optimize Response Time", "priority": "HIGH",   "priority_color": "#DC2626",
         "desc": "Reduce avg reply to under 2 hours - top revenue lever",
         "est": f"Est. +{est_pts} pts score lift"},
        {"emoji": "⭐", "title": "Launch Review Campaign",  "priority": "MEDIUM", "priority_color": "#F59E0B",
         "desc": "Target 15 new reviews this quarter via post-visit SMS",
         "est": "Est. +12% visibility"},
        {"emoji": "🔗", "title": "Update Google Profile",   "priority": "LOW",    "priority_color": "#10B981",
         "desc": "Refresh photos, menu links & booking CTA",
         "est": "Est. +8% CTR"},
        {"emoji": "🤖", "title": "AI Review Management",    "priority": "HIGH",   "priority_color": "#DC2626",
         "desc": "Automate personalized responses at scale - 120 EUR/mo",
         "est": "Est. 3x response rate"},
        {"emoji": "📡", "title": "Sentiment Monitoring",    "priority": "MEDIUM", "priority_color": "#F59E0B",
         "desc": "Real-time alerts for negative reviews across platforms",
         "est": f"Protect {rating:.1f} star rating"},
    ]


def get_rating_split(res_name, df_rest, df_rev):
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
    except Exception:
        pass
    return [40, 30, 15, 10, 5], [5, 4, 3, 2, 1]


# ── APP CONFIG ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Restaurant Intelligence Engine v2.0",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

NAVY, TEAL, TEAL2, BG, WHITE, MUTED, SUCCESS, WARNING, DANGER, BORDER = (
    "#0F172A", "#0EA5E9", "#14B8A6", "#F0F4F8", "#FFFFFF", "#64748B", "#22C55E", "#F59E0B", "#EF4444", "#E2E8F0"
)
ACCENT = "#2563EB"
SECONDARY = "#8B5CF6"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif !important; }}
#MainMenu, footer, .stDeployButton, [data-testid="stHeader"], [data-testid="stToolbar"] {{ visibility: hidden; display: none; }}
.stApp {{ background: {BG}; }}
.main .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }}
@keyframes fadeInSlide {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes messageSlideIn {{ 0% {{ opacity: 0; transform: translateY(10px) scaleY(0.9); }} 100% {{ opacity: 1; transform: translateY(0) scaleY(1); }} }}
@keyframes glow {{ 0%, 100% {{ box-shadow: 0 0 10px rgba(14,165,233,0.5); }} 50% {{ box-shadow: 0 0 20px rgba(14,165,233,0.8); }} }}
label {{ color: {NAVY} !important; font-weight: 600 !important; font-size: 12px !important; }}
[data-testid="stLabel"] {{ color: {NAVY} !important; }}
[data-testid="stLabel"] p {{ color: {NAVY} !important; }}
.stForm label {{ color: {NAVY} !important; }}
.stForm [data-testid="stLabel"] {{ color: {NAVY} !important; }}
.stDateInput label {{ color: {NAVY} !important; }}
.stTextInput label {{ color: {NAVY} !important; }}
.stSelectbox label {{ color: {NAVY} !important; }}
.stSlider label {{ color: {NAVY} !important; }}
.stTextArea label {{ color: {NAVY} !important; }}
.stMultiSelect label {{ color: {NAVY} !important; }}
input[type="text"], input[type="password"], input[type="number"], input[type="date"], textarea {{
    color: {NAVY} !important; background-color: {WHITE} !important;
    font-size: 12px !important; font-family: 'Inter', sans-serif !important;
}}
input::placeholder, textarea::placeholder {{ color: #94A3B8 !important; font-size: 12px !important; }}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="base-input"] input {{
    color: {NAVY} !important; background-color: {WHITE} !important; font-size: 12px !important;
}}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] {{ background-color: {WHITE} !important; }}
.main [data-testid="stSlider"] [data-testid="stMarkdownContainer"] p {{ color: {WHITE} !important; font-size: 12px !important; font-weight: 700 !important; }}
.main [data-testid="stSlider"] span, .main [data-testid="stSlider"] div {{ color: {NAVY} !important; }}
.main .stSlider p {{ color: {NAVY} !important; }}
.main [data-baseweb="select"] > div, .main [data-baseweb="select"] > div:focus-within {{
    background-color: {WHITE} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important;
}}
.main [data-baseweb="select"] span, .main [data-baseweb="select"] div,
.main [data-baseweb="select"] input, .main [data-baseweb="select"] p {{
    color: {NAVY} !important; background-color: transparent !important;
}}
[data-baseweb="menu"], [data-baseweb="popover"] ul, [data-baseweb="popover"] li {{
    background-color: {WHITE} !important; color: {NAVY} !important;
}}
[data-baseweb="menu"] li:hover, [data-baseweb="menu"] [aria-selected="true"] {{
    background-color: #EFF6FF !important; color: {NAVY} !important;
}}
.main [data-baseweb="tag"] {{ background-color: #E0F2FE !important; color: {NAVY} !important; }}
.main [data-baseweb="tag"] span {{ color: {NAVY} !important; }}
[data-testid="stMetricValue"] {{ color: {NAVY} !important; font-size: 13px !important; }}
[data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-size: 10px !important; }}
div[data-testid="stAlert"][data-baseweb="notification"] {{
    background-color: #FEE2E2 !important; border: 1.5px solid #EF4444 !important; border-radius: 10px !important;
}}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span, div[data-testid="stAlert"] svg {{
    color: #991B1B !important; fill: #991B1B !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: linear-gradient(175deg, {NAVY} 0%, #101d33 100%) !important; border-right: none !important; }}
[data-testid="stSidebar"] * {{ color: #CBD5E1 !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: rgba(255,255,255,0.08) !important; border: 1px solid rgba(255,255,255,0.18) !important; border-radius: 8px !important; }}
.kpi-card {{ background: {WHITE}; border-radius: 12px; padding: 18px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.07); border: 1px solid {BORDER}; position: relative; overflow: hidden; animation: fadeInSlide 0.5s ease-out; }}
.kpi-card::before {{ content: ''; position: absolute; top:0; left:0; right:0; height:3px; background: linear-gradient(90deg, {TEAL}, {TEAL2}); border-radius: 12px 12px 0 0; }}
.kpi-label {{ font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:{MUTED}; margin-bottom:6px; }}
.kpi-value {{ font-size:32px; font-weight:800; color:{NAVY}; line-height:1; font-family:'Space Mono',monospace; }}
.kpi-sub {{ font-size:12px; color:{MUTED}; margin-top:8px; }}
.section-card {{ background: {WHITE}; border-radius: 12px; padding: 22px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.07); border: 1px solid {BORDER}; margin-bottom: 18px; animation: fadeInSlide 0.6s ease-out; }}
.card-header {{ font-size:13px; font-weight:700; color:{NAVY}; padding-bottom:12px; margin-bottom:14px; border-bottom:1px solid {BORDER}; }}
.chat-msg-user {{ background: linear-gradient(135deg, {TEAL}, {TEAL2}); color: white; padding: 14px 18px; border-radius: 20px 20px 4px 20px; margin-left: 15%; margin-bottom: 10px; font-size: 13px; line-height: 1.6; box-shadow: 0 4px 16px rgba(14,165,233,0.25); word-wrap: break-word; }}
.chat-msg-ai {{ background: {WHITE}; color: {NAVY}; border: 2px solid #CAE6FD; padding: 15px 18px; border-radius: 20px 20px 20px 4px; margin-right: 10%; margin-bottom: 10px; font-size: 13px; line-height: 1.7; box-shadow: 0 4px 12px rgba(14,165,233,0.12); word-wrap: break-word; }}
[data-testid="stChatMessage"] p {{ color: {NAVY} !important; }}
[data-testid="stChatMessage"] {{ color: {NAVY} !important; }}
[data-testid="stChatMessage"] a {{ color: #2563EB !important; text-decoration: underline; }}
[data-testid="stChatMessage"] * {{ color: {NAVY} !important; }}
.stChatMessage {{ color: {NAVY} !important; }}
.stButton > button {{ background: linear-gradient(135deg, {TEAL}, {TEAL2}) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s ease !important; }}
.stButton > button:hover {{ transform: translateY(-2px) !important; box-shadow: 0 8px 16px rgba(14,165,233,0.3) !important; }}
.table-container {{ overflow-x: auto; margin: 20px 0; }}
.table-card {{ background: {WHITE}; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.07); border: 1px solid {BORDER}; }}
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span, [data-testid="stExpander"] summary {{ color: {NAVY} !important; font-size: 12px !important; font-weight: 600 !important; }}
[data-testid="stExpander"] {{ background: {WHITE} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; margin-bottom: 4px !important; }}
</style>
""", unsafe_allow_html=True)

# SESSION STATE
for key, default in [
    ("data_loaded", False), ("df_rest", None), ("df_rev", None), ("benchmarks", None),
    ("chat_messages", []), ("chat_context", None), ("active_page", "dashboard"),
    ("selected_city", "All Cities"), ("language", "EN"),
    ("min_rating_filter", 0.0), ("min_reviews_filter", 0), ("min_response_filter", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

@st.cache_data(show_spinner=False)
def load_google_data():
    rest_url = "https://docs.google.com/spreadsheets/d/1GzZWRuPr4y3yscDZYprWZtdgZ6Z6MkPBHwRTLH4bPR8/edit?usp=sharing"
    rev_url  = "https://docs.google.com/spreadsheets/d/1zSAd91SkuYgXuIOQa5WVJneEV5dmPyM9XMnI66iNGb4/edit?usp=sharing"
    try:
        return load_from_google_sheets(rest_url, rev_url)
    except Exception as e:
        logger.error(f"Error loading Google Sheets: {e}")
        return None, None, None

if not st.session_state.data_loaded:
    df_rest, df_rev, benchmarks = load_google_data()
    if df_rest is not None:
        st.session_state.df_rest     = df_rest
        st.session_state.df_rev      = df_rev
        st.session_state.benchmarks  = benchmarks
        st.session_state.data_loaded = True

# SIDEBAR
with st.sidebar:
    st.markdown(f"""
    <div style="padding:18px 0 20px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <span style="font-size:20px">🍽️</span>
        <span style="font-size:17px;font-weight:800;color:white">{t('sidebar_title', st.session_state.language)}</span>
      </div>
      <div style="font-size:11px;color:#475569">{t('sidebar_subtitle', st.session_state.language)}</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.data_loaded and st.session_state.df_rest is not None:
        _df = st.session_state.df_rest

        st.markdown('<p style="color:#94A3B8;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">🌍 City Filter</p>', unsafe_allow_html=True)
        cities = sorted(_df["district"].dropna().unique().tolist()) if "district" in _df.columns else []
        if "All Cities" not in cities:
            cities = ["All Cities"] + cities
        selected_city = st.selectbox("", cities, label_visibility="collapsed", key="city_select")
        st.session_state.selected_city = selected_city

        if selected_city != "All Cities" and "district" in _df.columns:
            _city_df = _df[_df["district"] == selected_city]
        else:
            _city_df = _df

        st.markdown('<p style="color:#94A3B8;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-top:14px;margin-bottom:6px">⚙️ Advanced Filters</p>', unsafe_allow_html=True)
        _max_rev = int(_df["rev_count_n"].max()) if len(_df) > 0 else 1000
        _min_rat = st.slider(t("min_rating",   st.session_state.language), 0.0, 5.0,      float(st.session_state.min_rating_filter),  0.1, key="filter_rating")
        _min_rev = st.slider(t("min_reviews",  st.session_state.language), 0,   _max_rev, int(st.session_state.min_reviews_filter),    10,  key="filter_reviews")
        _min_res = st.slider(t("min_response", st.session_state.language), 0,   100,      int(st.session_state.min_response_filter),   5,   key="filter_response")
        st.session_state.min_rating_filter   = _min_rat
        st.session_state.min_reviews_filter  = _min_rev
        st.session_state.min_response_filter = _min_res

        _adv_df = _city_df[
            (_city_df["rating_n"] >= _min_rat) &
            (_city_df["rev_count_n"] >= _min_rev) &
            (_city_df["res_rate"].fillna(0) * 100 >= _min_res)
        ]
        if len(_adv_df) == 0:
            _adv_df = _city_df

        st.markdown('<p style="color:#94A3B8;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-top:14px;margin-bottom:6px">🏪 Select Restaurant</p>', unsafe_allow_html=True)
        sidebar_names = sorted(_adv_df["name"].dropna().unique().tolist())
        _prev_sel     = st.session_state.get("rest_select")
        _default_idx  = sidebar_names.index(_prev_sel) if _prev_sel in sidebar_names else 0
        st.selectbox("", sidebar_names, index=_default_idx, label_visibility="collapsed", key="rest_select")

        st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:14px 0'>", unsafe_allow_html=True)
        silent_winners_all = identify_silent_winners(_df)
        if silent_winners_all:
            st.markdown(f'<p style="color:#FCA5A5;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">{t("silent_winners_detected", st.session_state.language).format(len(silent_winners_all))}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#475569;font-size:11px;margin-top:14px">Total: <b>{len(sidebar_names)}</b> restaurants in {selected_city}</p>', unsafe_allow_html=True)

# NO DATA STATE
if not st.session_state.data_loaded:
    st.markdown(f"""<div style="text-align:center;padding:60px 40px">
    <div style="font-size:48px;margin-bottom:20px">🍽️</div>
    <h1 style="font-size:28px;font-weight:800;color:{NAVY};margin-bottom:12px">{t("loading", st.session_state.language)}</h1>
    </div>""", unsafe_allow_html=True)
    st.stop()

# LANGUAGE SELECTOR
col_empty, col_lang = st.columns([4, 1])
with col_lang:
    lang_options  = {"🇬🇧 English": "EN", "🇩🇪 Deutsch": "DE"}
    selected_lang = st.selectbox(t("language", st.session_state.language), list(lang_options.keys()),
                                 index=0 if st.session_state.language == "EN" else 1,
                                 label_visibility="collapsed", key="lang_select")
    if lang_options[selected_lang] != st.session_state.language:
        st.session_state.language = lang_options[selected_lang]
        st.rerun()

df_rest, df_rev, benchmarks = st.session_state.df_rest, st.session_state.df_rev, st.session_state.benchmarks

_city = st.session_state.get("selected_city", "All Cities")
if _city and _city != "All Cities" and "district" in df_rest.columns:
    _df_city = df_rest[df_rest["district"] == _city].copy()
else:
    _df_city = df_rest.copy()

df_rest_filtered = _df_city[
    (_df_city["rating_n"] >= st.session_state.min_rating_filter) &
    (_df_city["rev_count_n"] >= st.session_state.min_reviews_filter) &
    (_df_city["res_rate"].fillna(0) * 100 >= st.session_state.min_response_filter)
].copy()
if len(df_rest_filtered) == 0:
    df_rest_filtered = _df_city.copy()

names    = sorted(df_rest_filtered["name"].dropna().unique().tolist())
selected = st.session_state.get("rest_select", names[0] if names else None)

if not selected:
    st.warning(t("no_restaurants", st.session_state.language))
    st.stop()

# COMPUTE METRICS
res_data    = df_rest[df_rest["name"] == selected].iloc[0]
scores      = compute_dimension_scores(selected, df_rest, df_rev)
gaps        = get_gap_analysis(scores, benchmarks)
momentum    = compute_momentum(selected, df_rev, df_rest)
persona     = get_customer_persona(selected, df_rest, df_rev)
silent_flag = get_silent_winner_flag(selected, df_rest)
deal_prob   = calculate_deal_probability(selected, res_data, scores, gaps)

df_ranks_all = compute_all_ranks(df_rest, df_rev)
cur_rank     = int(df_ranks_all[df_ranks_all["name"] == selected]["rank"].values[0])
total        = len(df_ranks_all)

try:
    df_ranks = compute_all_ranks(df_rest_filtered, df_rev) if len(df_rest_filtered) > 0 else pd.DataFrame(columns=["name", "score", "rank"])
except Exception as _e:
    logger.warning(f"compute_all_ranks (filtered) failed: {_e}")
    df_ranks = pd.DataFrame(columns=["name", "score", "rank"])

# PAGE HEADER
silent_badge = (
    f'&nbsp;&nbsp;<span style="background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:20px;'
    f'font-size:11px;font-weight:700;animation:glow 2s ease-in-out infinite">'
    f'{t("silent_winner_badge", st.session_state.language)}</span>'
) if silent_flag else ""

st.markdown(f"""
<div style="background:{WHITE};border-radius:12px;padding:18px 26px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.07);border:1px solid {BORDER}">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <h1 style="font-size:26px;font-weight:800;color:{NAVY};margin:0">{selected}</h1>
      <div style="font-size:12px;color:{MUTED};margin-top:4px">
        📍 {t("ranked", st.session_state.language)} <strong>#{cur_rank}</strong> {t("of", st.session_state.language)} {total} |
        {t("score", st.session_state.language)}: <strong>{scores['Composite']:.1f}/100</strong> {silent_badge}
      </div>
    </div>
    <div style="text-align:right;font-size:11px;color:{MUTED}">
      <strong>{t("rating", st.session_state.language)}:</strong> {float(res_data.get('rating_n', 0)):.1f}★ |
      <strong>{t("reviews", st.session_state.language)}:</strong> {int(res_data.get('rev_count_n', 0)):,}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# NAV BUTTONS
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button(t("btn_dashboard",      st.session_state.language), use_container_width=True, key="btn_dashboard"):      st.session_state.active_page = "dashboard"
with col2:
    if st.button(t("btn_assistant",      st.session_state.language), use_container_width=True, key="btn_assistant"):      st.session_state.active_page = "assistant"
with col3:
    if st.button(t("btn_notes",          st.session_state.language), use_container_width=True, key="btn_notes"):          st.session_state.active_page = "notes"
with col4:
    if st.button(t("btn_silent_winners", st.session_state.language), use_container_width=True, key="btn_silent_winners"): st.session_state.active_page = "silent_winners"

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ============================================================
# DASHBOARD
# ============================================================
if st.session_state.active_page == "dashboard":
    c1, c2, c3, c4, c5 = st.columns(5)
    tiles = [
        (c1, t("kpi_score",     st.session_state.language), f"{scores['Composite']:.1f}",                    t("out_of_100",      st.session_state.language), "⚡ Active", True),
        (c2, t("kpi_rank",      st.session_state.language), f"#{cur_rank}",                                   f"{total} {t('total', st.session_state.language, count=total)}", "↗ +2", True),
        (c3, t("kpi_response",  st.session_state.language), f"{float(res_data.get('res_rate',0))*100:.0f}%",  t("owner_replies",   st.session_state.language), (f"↗ {t('good',       st.session_state.language)}" if float(res_data.get('res_rate',0))>=0.5 else f"↘ {t('low',        st.session_state.language)}"), float(res_data.get('res_rate',0))>=0.5),
        (c4, t("kpi_sentiment", st.session_state.language), f"{scores['Intelligence']:.0f}%",                 t("review_sentiment",st.session_state.language), (f"↗ {t('strong',     st.session_state.language)}" if scores['Intelligence']>=75 else f"↘ {t('needs_work', st.session_state.language)}"), scores['Intelligence']>=75),
        (c5, t("kpi_freshness", st.session_state.language), f"{scores['Visibility']:.0f}%",                   t("review_velocity", st.session_state.language), (f"↗ {t('active',     st.session_state.language)}" if scores['Visibility']>=50 else f"↘ {t('slow_status',st.session_state.language)}"), scores['Visibility']>=50),
    ]
    for col, label, val, sub, delta, pos in tiles:
        dc = "✅" if pos else "⚠️"
        col.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div><div class="kpi-sub">{sub}&nbsp;<span style="color:{'#22C55E' if pos else '#EF4444'};font-weight:700;">{dc} {delta}</span></div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    col_r, col_g = st.columns(2)
    with col_r:
        st.markdown(f'<div class="section-card"><div class="card-header"> {t("dimension_radar", st.session_state.language)}</div>', unsafe_allow_html=True)
        dim_labels = ["Reputation","Responsiveness","Digital\nPresence","Intelligence","Visibility"]
        if go is None:
            st.info("Plotly not installed.")
        else:
            sv = [scores[d] for d in ["Reputation","Responsiveness","Digital Presence","Intelligence","Visibility"]]
            bv = [benchmarks.get("rating",4.4)*20, 90, 85, 75, 70]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=sv+[sv[0]], theta=dim_labels+[dim_labels[0]], fill="toself", name="Score",
                line=dict(color=TEAL, width=2.5), fillcolor="rgba(14,165,233,0.13)", marker=dict(size=5, color=TEAL)))
            fig.add_trace(go.Scatterpolar(r=bv+[bv[0]], theta=dim_labels+[dim_labels[0]], fill="toself", name="Benchmark",
                line=dict(color="#A855F7", width=1.5, dash="dot"), fillcolor="rgba(168,85,247,0.05)", marker=dict(size=4, color="#A855F7")))
            fig.update_layout(polar=dict(bgcolor="white",
                radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=9, color=NAVY), gridcolor="#F0E2E2"),
                angularaxis=dict(tickfont=dict(color=NAVY, size=11, family="Inter"))),
                legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, font=dict(size=11)),
                height=340, margin=dict(l=40,r=40,t=20,b=40), paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g:
        st.markdown(f'<div class="section-card"><div class="card-header"> {t("gap_analysis", st.session_state.language)}</div>', unsafe_allow_html=True)
        for key, score_key, target in [
            ("responsiveness","Responsiveness",90),("market_sentiment","Intelligence",75),
            ("review_freshness","Visibility",70),("brand_visibility","Digital Presence",80),
            ("reputation","Reputation",benchmarks.get("rating",4.4)*20),
        ]:
            label   = t(key, st.session_state.language)
            current = scores[score_key]
            diff    = round(current - target, 1)
            color   = SUCCESS if diff >= 0 else DANGER
            sign    = "+" if diff >= 0 else ""
            st.markdown(f"""<div style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;margin-bottom:5px">
              <span style="font-size:12px;font-weight:600;color:{NAVY}">{label}</span><span style="font-size:12px;font-weight:700;color:{color}">{sign}{diff}%</span></div>
              <div style="position:relative;height:8px;background:#F1F5F9;border-radius:4px">
                <div style="position:absolute;left:0;top:0;height:100%;width:{min(current,100)}%;background:linear-gradient(90deg,{TEAL},{TEAL2});border-radius:4px"></div>
                <div style="position:absolute;top:-3px;left:{min(target,100)}%;width:2px;height:14px;background:{NAVY};border-radius:2px"></div>
              </div></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    col_ai, col_act = st.columns(2)
    with col_ai:
        st.markdown(f'<div class="section-card"><div class="card-header">{t("customer_insights", st.session_state.language)}</div>', unsafe_allow_html=True)
        p = persona
        st.markdown(f"""<div style="margin-bottom:12px"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin-bottom:3px">{t("primary_persona", st.session_state.language)}</div>
          <div style="font-size:15px;font-weight:700;color:{NAVY}">{p["primary"]}</div></div>
          <div style="margin-bottom:12px"><div style="font-size:10px;font-weight:700;color:#94A3B8">{t("segment", st.session_state.language)}</div><div style="font-size:13px;color:#334155">{p["segment"]}</div></div>
          <div style="background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;padding:10px">
            <span style="font-size:11px;font-weight:700;color:#0369A1">{t("motivation", st.session_state.language)}</span><span style="font-size:11px;color:{NAVY}">{p["motivation"]}</span></div>
        </div>""", unsafe_allow_html=True)
        try:
            pdf_bytes = generate_pdf_report(selected, res_data, scores, gaps, momentum, persona, benchmarks, df_rest_filtered, df_rev, cur_rank, total, st.session_state.language)
            st.download_button(t("export_pdf", st.session_state.language), data=pdf_bytes, file_name=f"Intelligence_{selected.replace(' ','_')}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"PDF error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_act:
        st.markdown(f'<div class="section-card"><div class="card-header"> {t("actionable_solutions", st.session_state.language)}</div>', unsafe_allow_html=True)
        top_gaps  = sorted(gaps.items(), key=lambda x: x[1], reverse=True)[:5]
        solutions = get_actionable_solutions(selected, res_data, top_gaps, st.session_state.language)
        for sol in solutions:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{sol['priority_color']}15,{sol['priority_color']}05);border:1px solid {sol['priority_color']}40;border-radius:10px;padding:14px;margin-bottom:10px;border-left:4px solid {sol['priority_color']}">
              <div style="display:flex;align-items:flex-start;gap:12px">
                <div style="font-size:20px">{sol['emoji']}</div>
                <div style="flex:1">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    <span style="font-size:13px;font-weight:700;color:{NAVY}">{sol['title']}</span>
                    <span style="background:{sol['priority_color']};color:white;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">{sol['priority']}</span>
                  </div>
                  <div style="font-size:11px;color:{MUTED};margin-bottom:6px;line-height:1.5">{sol['desc']}</div>
                  <div style="font-size:10px;font-weight:600;color:{TEAL}">→ {sol['est']}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="section-card"><div class="card-header"> {t("momentum", st.session_state.language)}</div>', unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns([3,1,1])
    with col_m1:
        if momentum is not None and len(momentum) > 0 and go is not None:
            fig_m = go.Figure()
            fig_m.add_trace(go.Scatter(x=momentum["month"], y=momentum["count"], mode="lines+markers",
                line=dict(color=TEAL, width=2.5, shape="spline"), fill="tozeroy", fillcolor="rgba(14,165,233,0.08)",
                marker=dict(size=6, color=TEAL, line=dict(color="white", width=1.5))))
            fig_m.update_layout(height=210, margin=dict(l=40,r=20,t=10,b=30), paper_bgcolor="white", plot_bgcolor="white",
                showlegend=False, xaxis=dict(tickfont=dict(color=NAVY)), yaxis=dict(tickfont=dict(color=NAVY)))
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
    with col_m2:
        if go is not None:
            rc_values, rc_index = get_rating_split(selected, df_rest, df_rev)
            fig_d = go.Figure(go.Pie(values=rc_values, labels=[f"{i}★" for i in rc_index], hole=0.6,
                marker=dict(colors=["#22C55E","#86EFAC","#FCD34D","#FCA5A5","#EF4444"]), textfont=dict(size=9, color=NAVY)))
            fig_d.update_layout(title=dict(text=t("rating_split", st.session_state.language), font=dict(size=11), x=0.5),
                height=210, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="white")
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})
    with col_m3:
        if go is not None:
            fig_g = go.Figure(go.Indicator(mode="gauge+number", value=scores["Composite"],
                number={"font": {"size": 26, "family": "Space Mono", "color": NAVY}},
                gauge={"axis": {"range": [0,100], "tickfont": {"size":8, "color": NAVY}},
                       "bar": {"color": TEAL, "thickness": 0.28}, "bgcolor": "#F1F5F9", "bordercolor": BORDER,
                       "steps": [{"range":[0,50],"color":"#FEE2E2"},{"range":[50,75],"color":"#FEF3C7"},{"range":[75,100],"color":"#DCFCE7"}]}))
            fig_g.update_layout(title=dict(text=t("health", st.session_state.language), font=dict(size=11), x=0.5),
                height=210, margin=dict(l=20,r=20,t=30,b=0), paper_bgcolor="white")
            st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="section-card"><div class="card-header"> {t("top_restaurants", st.session_state.language)}</div>', unsafe_allow_html=True)
    top_10 = df_ranks.head(10)
    if go is not None and len(top_10) > 0:
        fig_top = go.Figure(go.Bar(x=top_10["name"], y=top_10["score"],
            marker=dict(color=top_10["score"], colorscale="RdYlGn", cmin=0, cmax=100, showscale=False),
            text=top_10["score"].round(1), textposition="auto"))
        fig_top.update_layout(height=300, margin=dict(l=50,r=20,t=10,b=80), paper_bgcolor="white", plot_bgcolor="white",
            xaxis_tickangle=-45, showlegend=False, font=dict(family="Inter", color=NAVY, size=10),
            xaxis=dict(tickfont=dict(color=NAVY, size=10), showgrid=False),
            yaxis=dict(tickfont=dict(color=NAVY, size=10), showgrid=True, gridcolor="#F0F0F0", gridwidth=1))
        fig_top.update_traces(textposition="outside", textfont=dict(color=NAVY, size=10))
        st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No data to display.")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# AI ASSISTANT
# ============================================================
elif st.session_state.active_page == "assistant":
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {TEAL}, {TEAL2});border-radius:12px;padding:20px 24px;margin-bottom:20px;border:none;box-shadow:0 8px 24px rgba(14,165,233,0.25)">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:rgba(255,255,255,0.85);margin-bottom:6px">{t("ai_assistant_header", st.session_state.language)}</div>
      <div style="font-size:18px;font-weight:800;color:white;margin-bottom:3px">{t("ai_assistant_subtitle", st.session_state.language)} <span style="background:rgba(255,255,255,0.2);padding:4px 10px;border-radius:6px;margin-left:6px">{selected}</span></div>
      <div style="font-size:12px;color:rgba(255,255,255,0.8);margin-top:6px;line-height:1.5">{t("ai_assistant_description", st.session_state.language)}</div>
      <div style="font-size:10px;color:rgba(255,255,255,0.7);margin-top:8px"> {t("powered_by", st.session_state.language)}</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.chat_context is None or st.session_state.get("_chat_restaurant") != selected:
        st.session_state.chat_context     = build_restaurant_context(selected, res_data, scores, gaps, benchmarks, df_rest, df_rev, cur_rank, total, persona, momentum)
        st.session_state.chat_messages    = []
        st.session_state._chat_restaurant = selected

    user_input = st.chat_input(t("ask_placeholder", st.session_state.language, selected=selected))
    if user_input or st.session_state.get("pending_question"):
        question = st.session_state.get("pending_question") or user_input
        st.session_state.pending_question = None
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.spinner(t("claude_thinking", st.session_state.language)):
            response = get_response(st.session_state.chat_messages, st.session_state.chat_context, st.session_state.language)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.session_state.chat_messages:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.chat_message("user").markdown(msg["content"])
            else:
                display_text, _ = parse_followups(msg["content"])
                st.chat_message("assistant").markdown(display_text)

        last_ai = next((m for m in reversed(st.session_state.chat_messages) if m["role"] == "assistant"), None)
        if last_ai:
            _, followups = parse_followups(last_ai["content"])
            if followups:
                st.markdown(f"<div style='margin:20px 0 12px;'><p style='font-size:11px;color:#64748B;font-weight:700;margin-bottom:8px'> {t('followup_questions', st.session_state.language)}</p>", unsafe_allow_html=True)
                for i, q in enumerate(followups):
                    if st.button(f"💬 {q[:50]}{'...' if len(q)>50 else ''}", key=f"fu_{i}_{hash(q)}", use_container_width=True):
                        st.session_state.pending_question = q
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            if len(st.session_state.chat_messages) >= 2:
                last_user = next((m for m in reversed(st.session_state.chat_messages) if m["role"] == "user"), None)
                if last_user and last_ai:
                    with st.spinner("Generating related questions..."):
                        similar = get_similar_questions(last_user["content"], last_ai["content"][:800], selected, gaps, language=st.session_state.language)
                    if similar:
                        st.markdown(f"<div style='margin:16px 0 12px;'><p style='font-size:11px;color:#64748B;font-weight:700;margin-bottom:8px'> {t('similar_questions', st.session_state.language)}</p>", unsafe_allow_html=True)
                        for i, q in enumerate(similar):
                            if st.button(f"🔍 {q[:50]}{'...' if len(q)>50 else ''}", key=f"sim_{i}_{hash(q)}", use_container_width=True):
                                st.session_state.pending_question = q
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    else:
        st.markdown(f'<p style="font-size:11px;color:{MUTED};margin-bottom:8px"> {t("suggested_questions", st.session_state.language)}</p>', unsafe_allow_html=True)
        suggested = get_suggested_questions(gaps, selected, language=st.session_state.language)
        for i, q in enumerate(suggested[:4]):
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

# ============================================================
# CALL NOTES
# ============================================================
elif st.session_state.active_page == "notes":
    restaurant_id  = selected.lower().replace(" ", "_").replace("-", "_")[:40]
    existing_calls = load_call_notes(restaurant_id)

    st.markdown(f"""
    <div style="background:{WHITE};border-radius:12px;padding:18px 24px;margin-bottom:20px;border:1px solid {BORDER};box-shadow:0 1px 3px rgba(0,0,0,0.07)">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#94A3B8;margin-bottom:4px">📞 SALES CALL NOTES</div>
      <div style="font-size:18px;font-weight:800;color:{NAVY}">{selected}</div>
      <div style="font-size:12px;color:{MUTED};margin-top:3px">
        {len(existing_calls)} call(s) logged &nbsp;·&nbsp;
        <span style="color:{TEAL};font-weight:600">Active Account</span>
      </div>
    </div>""", unsafe_allow_html=True)

    col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
    with col_exp1:
        if st.button("📊 Export Master Excel", use_container_width=True, key="export_btn"):
            try:
                import importlib, sys as _sys
                # Force fresh load every single time — never use cached version
                for _mod in list(_sys.modules.keys()):
                    if "excel_exporter" in _mod:
                        del _sys.modules[_mod]
                import excel_exporter as _xls
                importlib.reload(_xls)
                call_notes_path = PROJECT_ROOT / "scripts" / "data" / "call_notes"
                call_notes_path.mkdir(parents=True, exist_ok=True)
                excel_bytes = _xls.export_call_notes_to_excel(call_notes_path)
                st.download_button("⬇️ Download Excel", data=excel_bytes,
                    file_name=f"CallNotes_Master_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_excel_btn")
            except Exception as e:
                import traceback
                st.error(f"Export Error: {e}\n{traceback.format_exc()}")
    with col_exp2:
        if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_notes_btn"):
            st.rerun()

    st.markdown(f"""
    <div style="font-size:13px;font-weight:700;padding:12px 16px;background:linear-gradient(135deg,{TEAL},{TEAL2});color:white;border-radius:10px;margin:20px 0 14px;letter-spacing:0.03em">
      ➕ Log New Call
    </div>""", unsafe_allow_html=True)

    with st.form("call_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">📋 Call Details</p>', unsafe_allow_html=True)
            call_date    = st.date_input("Call Date",    key="call_date_input")
            contact_name = st.text_input("Contact Name", placeholder="e.g. Marco Rossi", key="contact_name_input")
            interest     = st.slider("Interest Level", 1, 5, 3, key="interest_input", help="1=Cold 3=Warm 5=Hot")
        with col2:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">💼 Sales Context</p>', unsafe_allow_html=True)
            objection  = st.text_input("Main Objection", placeholder="e.g. Budget too high", key="objection_input")
            budget     = st.text_input("Budget Range",   placeholder="e.g. 100-200/mo",      key="budget_input")
            confidence = st.slider("Confidence Level (Close %)", 0, 100, 50, 10, key="confidence_input")

        st.markdown("<hr style='border:none;border-top:1px solid #E2E8F0;margin:12px 0'>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">📅 Follow-up</p>', unsafe_allow_html=True)
            next_steps     = st.text_input("Next Steps",     placeholder="e.g. Send proposal", key="next_steps_input")
            follow_up_date = st.date_input("Follow-up Date",                                   key="followup_date_input")
        with col4:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">🧠 Preparation</p>', unsafe_allow_html=True)
            decision_timeline = st.text_input("Decision Timeline",          placeholder="e.g. 30 days, Q2 budget",       key="timeline_input")
            competitor_tools  = st.text_input("Competitor Tools Mentioned", placeholder="e.g. Google My Business only",  key="competitor_input")

        st.markdown("<hr style='border:none;border-top:1px solid #E2E8F0;margin:12px 0'>", unsafe_allow_html=True)
        col_prod, col_out = st.columns([2, 1])
        with col_prod:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">📦 Products Discussed</p>', unsafe_allow_html=True)
            products = st.multiselect("Products",
                ["AI Review Manager (120 EUR/mo)", "Review Velocity (80 EUR/mo)",
                 "Profile Optimization (60 EUR/mo)", "Sentiment Monitoring (80 EUR/mo)",
                 "Engagement Booster (60 EUR/mo)", "Full Suite (340 EUR/mo)"],
                key="products_input", label_visibility="collapsed")
        with col_out:
            st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">🏁 Outcome</p>', unsafe_allow_html=True)
            outcome = st.selectbox("Outcome", ["Pending", "Won", "Lost"], key="outcome_input", label_visibility="collapsed")

        notes = st.text_area("📝 Detailed Notes", height=90,
                             placeholder="Key discussion points, objections raised, agreements made...", key="notes_input")
        st.markdown("<hr style='border:none;border-top:1px solid #E2E8F0;margin:12px 0'>", unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;font-weight:700;color:{TEAL};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em">📸 Attach Images (optional)</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;color:{MUTED};margin-bottom:8px">Upload screenshots, business cards, or any relevant visuals.</p>', unsafe_allow_html=True)
        uploaded_images = st.file_uploader("Upload Images", type=["png","jpg","jpeg","webp"],
                                           accept_multiple_files=True, key="images_input", label_visibility="collapsed")
        submitted = st.form_submit_button("💾 Save Call", use_container_width=True)

    if submitted:
        images_b64 = []
        if uploaded_images:
            for img_file in uploaded_images:
                try:
                    b64 = base64.b64encode(img_file.read()).decode("utf-8")
                    images_b64.append({"filename": img_file.name, "type": img_file.type, "data": b64})
                except Exception as img_err:
                    logger.warning(f"Could not encode image {img_file.name}: {img_err}")
        call_record = {
            "call_date": str(call_date), "contact_name": contact_name,
            "interest_level": interest, "main_objection": objection,
            "budget_range": budget, "confidence_level": confidence,
            "next_steps": next_steps, "follow_up_date": str(follow_up_date),
            "decision_timeline": decision_timeline, "competitor_tools": competitor_tools,
            "products_discussed": products, "outcome": outcome,
            "notes": notes, "images": images_b64,
        }
        save_call_notes(restaurant_id, call_record)
        st.session_state.chat_context = None
        img_msg = f" + {len(images_b64)} image(s)" if images_b64 else ""
        st.success(f"✅ Call saved for {selected}{img_msg}")
        st.rerun()

    if existing_calls:
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:13px;font-weight:700;color:white;background:linear-gradient(135deg,{TEAL},{TEAL2});
                    padding:11px 16px;border-radius:10px;margin-bottom:16px">
          📞 Previous Calls &nbsp;
          <span style="background:rgba(255,255,255,0.25);padding:2px 10px;border-radius:20px;font-size:11px">{len(existing_calls)} total</span>
        </div>""", unsafe_allow_html=True)

        for i, call in enumerate(reversed(existing_calls), 1):
            actual_index = len(existing_calls) - i
            interest_val = call.get("interest_level", 0)
            outcome_val  = call.get("outcome", "Pending")
            call_images  = call.get("images", [])
            int_stars    = "★" * int(interest_val) + "☆" * (5 - int(interest_val))
            out_colors   = {"Won": SUCCESS, "Lost": DANGER, "Pending": WARNING}
            out_color    = out_colors.get(outcome_val, WARNING)

            with st.container():
                c_left, c_right = st.columns([3, 1])
                with c_left:
                    st.markdown(f'<div style="font-size:14px;font-weight:800;color:{NAVY};margin-bottom:2px">Call #{len(existing_calls)-i+1} &nbsp;·&nbsp; <span style="font-weight:500;font-size:12px;color:{MUTED}">{call.get("call_date","?")}</span></div>', unsafe_allow_html=True)
                with c_right:
                    st.markdown(f'<div style="text-align:right"><span style="background:{out_color}22;color:{out_color};border:1px solid {out_color}55;padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700">{outcome_val.upper()}</span></div>', unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Contact",    call.get("contact_name","—") or "—")
                m2.metric("Interest",   f"{int_stars}  {interest_val}/5")
                m3.metric("Budget",     call.get("budget_range","—") or "—")
                m4.metric("Confidence", f"{call.get('confidence_level','—')}%")

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    prods = ", ".join(call.get("products_discussed", [])) or "—"
                    st.markdown(f'<div style="font-size:11px;color:{NAVY};padding:6px 0"><b>Objection:</b> {call.get("main_objection","—") or "—"}<br><b>Products:</b> {prods}</div>', unsafe_allow_html=True)
                with col_d2:
                    st.markdown(f'<div style="font-size:11px;color:{NAVY};padding:6px 0"><b>Next Steps:</b> {call.get("next_steps","—") or "—"}<br><b>Follow-up:</b> {call.get("follow_up_date","—")}</div>', unsafe_allow_html=True)

                if call.get("notes"):
                    st.markdown(f'<div style="font-size:11px;color:{NAVY};background:#F0F9FF;border-left:3px solid {TEAL};padding:9px 12px;border-radius:6px;margin:6px 0 8px;line-height:1.6">📝 {call["notes"]}</div>', unsafe_allow_html=True)

                if call_images:
                    st.markdown(f'<p style="font-size:10px;font-weight:700;color:{TEAL};margin:4px 0 6px;text-transform:uppercase;letter-spacing:0.08em">📸 Attached Images ({len(call_images)})</p>', unsafe_allow_html=True)
                    for ci, img_data in enumerate(call_images):
                        try:
                            img_bytes = base64.b64decode(img_data["data"])
                            fname     = img_data.get("filename", f"Image {ci+1}")
                            # Compact file-chip row — click expander to see full image
                            st.markdown(f"""
                            <div style="display:inline-flex;align-items:center;gap:8px;background:#F0F9FF;
                                        border:1px solid #BAE6FD;border-radius:8px;padding:6px 12px;
                                        margin-bottom:4px;cursor:default">
                              <span style="font-size:16px">🖼️</span>
                              <span style="font-size:11px;font-weight:600;color:{NAVY}">{fname}</span>
                            </div>""", unsafe_allow_html=True)
                            with st.expander(f"🔍 Click to view — {fname}"):
                                st.image(img_bytes, use_container_width=True)
                        except Exception:
                            pass

                del_col, _ = st.columns([1, 5])
                with del_col:
                    if st.button("🗑️ Delete", key=f"delete_call_{restaurant_id}_{actual_index}", use_container_width=True):
                        success = delete_call_note(restaurant_id, actual_index)
                        st.success("✅ Call deleted") if success else st.error("Could not delete call")
                        st.rerun()

                st.markdown(f'<hr style="border:none;border-top:1px solid {BORDER};margin:12px 0">', unsafe_allow_html=True)

# ============================================================
# SILENT WINNERS
# ============================================================
elif st.session_state.active_page == "silent_winners":
    st.markdown(f"""
    <div style="background:{WHITE};border-radius:12px;padding:16px 20px;margin-bottom:20px;border:1px solid {BORDER};box-shadow:0 1px 3px rgba(0,0,0,0.07)">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#94A3B8;margin-bottom:4px">🌟 SILENT WINNERS</div>
      <div style="font-size:16px;font-weight:700;color:{NAVY}">High-Potential Sales Targets</div>
      <div style="font-size:11px;color:{MUTED};margin-top:2px">Restaurants with strong ratings but low engagement — prime opportunity for response automation</div>
    </div>""", unsafe_allow_html=True)

    if _city and _city != "All Cities" and "district" in df_rest.columns:
        city_rest = df_rest[df_rest["district"] == _city]
    else:
        city_rest = df_rest

    silent_winners_city = identify_silent_winners(city_rest)
    if silent_winners_city:
        sw_data = []
        for sw in silent_winners_city[:15]:
            try:
                sw_row    = df_rest[df_rest["name"] == sw].iloc[0]
                sw_scores = compute_dimension_scores(sw, df_rest, df_rev)
                sw_rank   = int(df_ranks_all[df_ranks_all["name"] == sw]["rank"].values[0])
                sw_data.append({
                    "Restaurant": sw,
                    "Rating":     f"{float(sw_row.get('rating_n', 0)):.1f}⭐",
                    "Reviews":    f"{int(sw_row.get('rev_count_n', 0)):,}",
                    "Response %": f"{float(sw_row.get('res_rate', 0))*100:.0f}%",
                    "Sentiment":  f"{sw_scores['Intelligence']:.0f}%",
                    "Rank":       f"#{sw_rank}",
                })
            except Exception as e:
                logger.warning(f"Error processing silent winner {sw}: {e}")
                continue
        if sw_data:
            st.dataframe(pd.DataFrame(sw_data), use_container_width=True, hide_index=True)
            st.markdown(f'<p style="font-size:11px;color:{MUTED};margin-top:8px;">💡 These restaurants have high ratings but low engagement. Focus on <strong>response rate automation</strong> as the opening pitch.</p>', unsafe_allow_html=True)
        else:
            st.info("No silent winners data available.")
    else:
        st.info(f"No silent winners detected in {_city} (need rating >=4.5, reviews >=50, response rate <30%)")

# FOOTER
st.markdown(f"""
<div style="background:linear-gradient(135deg, {NAVY}12, {TEAL}08);border-top:2px solid {TEAL};border-radius:12px;padding:24px 20px;margin-top:32px;text-align:center">
  <div style="margin-bottom:12px">
    <span style="font-size:28px;margin-right:12px">🍽️</span>
    <span style="font-size:16px;font-weight:800;color:{NAVY};letter-spacing:0.5px">Intelligence Engine v2.0</span>
  </div>
  <p style="font-size:12px;color:{MUTED};margin:8px 0;line-height:1.6">
    <strong style="color:{NAVY}">{len(df_rest)} {t("establishments", st.session_state.language)}</strong> &nbsp;·&nbsp;
    <strong style="color:{NAVY}">{total} {t("ranked_count", st.session_state.language)}</strong> &nbsp;·&nbsp;
    <strong style="color:{NAVY}">{t("realtime_analytics", st.session_state.language)}</strong>
  </p>
  <div style="font-size:10px;color:#94A3B8;margin-top:10px;padding-top:12px;border-top:1px solid {BORDER}">
    <span style="display:inline-block;margin:0 8px"> {t("powered_by_footer", st.session_state.language)}</span>
  </div>
</div>
""", unsafe_allow_html=True)