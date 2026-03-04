"""
Multi-language support for Restaurant Intelligence Engine
Supports: English (EN) and German (DE)
"""

TRANSLATIONS = {
    "EN": {
        # Page titles
        "page_title": "Restaurant Intelligence Engine v2.0",

        # Sidebar
        "sidebar_title": "Intelligence Engine v2.0",
        "sidebar_subtitle": "Restaurant Audit Platform",
        "city_filter": "🌍 City Filter",
        "all_cities": "All Cities",
        "restaurant_select": "🏪 Select Restaurant",
        "advanced_filters": "⚙️ Advanced Filters",
        "min_rating": "Min Rating",
        "min_reviews": "Min Reviews",
        "min_response": "Min Response %",
        "silent_winners_detected": "🔴 {} Silent Winners Detected",
        "total_restaurants": "Total: <b>{}</b> restaurants in {}",
        "language": "🌐 Language",

        # Loading state
        "loading": "Loading Restaurant Data...",

        # No data
        "no_restaurants": "⚠️ No restaurants available. Please check your data.",

        # Page Header
        "ranked": "Ranked",
        "of": "of",
        "score": "Score",
        "rating": "Rating",
        "reviews": "Reviews",
        "silent_winner_badge": "🔴 SILENT WINNER",

        # Navigation buttons
        "btn_dashboard": "📊 Intelligence Dashboard",
        "btn_assistant": "🤖 AI Sales Assistant",
        "btn_notes": "📋 Call Notes",
        "btn_silent_winners": "🌟 Silent Winners",

        # Dashboard - KPIs
        "kpi_score": "Overall Score",
        "kpi_rank": "Rank",
        "kpi_response": "Response Rate",
        "kpi_sentiment": "Sentiment",
        "kpi_freshness": "Freshness",
        "out_of_100": "out of 100",
        "total": "{} total",
        "owner_replies": "Owner replies",
        "review_sentiment": "Review sentiment",
        "review_velocity": "Review velocity",
        "active": "Active",
        "good": "Good",
        "low": "Low",
        "strong": "Strong",
        "needs_work": "Needs work",
        "good_status": "↗ Good",
        "low_status": "↘ Low",
        "strong_status": "↗ Strong",
        "needs_work_status": "↘ Needs work",
        "active_status": "↗ Active",
        "slow_status": "↘ Slow",

        # Dashboard - Charts
        "dimension_radar": "⚙️ Dimension Radar",
        "gap_analysis": "📊 Gap Analysis vs Benchmark",
        "responsiveness": "Responsiveness",
        "market_sentiment": "Market Sentiment",
        "review_freshness": "Review Freshness",
        "brand_visibility": "Brand Visibility",
        "reputation": "Reputation",
        "digital_presence": "Digital Presence",
        "intelligence": "Intelligence",
        "visibility": "Visibility",

        # Dashboard - Persona and Actions
        "customer_insights": "👤 AI Customer Insights",
        "primary_persona": "PRIMARY PERSONA",
        "segment": "SEGMENT:",
        "motivation": "Motivation:",
        "export_pdf": "📄 Export PDF Report",
        "pdf_error": "PDF error: {}",
        "actionable_solutions": "💡 Actionable Solutions",
        "priority_high": "HIGH",
        "priority_medium": "MEDIUM",
        "priority_low": "LOW",

        # Dashboard - Momentum
        "momentum": "📈 Momentum & Ratings",
        "rating_split": "Rating Split",
        "health": "Health",

        # Dashboard - Leaderboard
        "top_restaurants": "🏆 Top 10 Restaurants",

        # AI Assistant
        "ai_assistant_header": "🤖 AI SALES ASSISTANT",
        "ai_assistant_subtitle": "Ask Claude about",
        "ai_assistant_description": "💡 Ask anything about performance, strategies, growth opportunities or next steps",
        "ask_placeholder": "Ask about {}…",
        "suggested_questions": "💡 Suggested questions:",
        "followup_questions": "💬 Follow-up Questions:",
        "similar_questions": "🔍 Similar Questions:",
        "clear_chat": "🗑️ Clear Chat",
        "claude_thinking": "Claude is thinking…",
        "generating_questions": "Generating related questions…",
        "configure_api": "Configure Anthropic API Key (optional)",
        "api_instructions": "Paste your Anthropic API key here to enable the AI assistant. Keys are saved to the project's .env file.",
        "api_key_placeholder": "sk-...",
        "save_api_key": "Save API Key",
        "api_key_saved": "API key saved to .env — please restart the app.",
        "api_key_error": "Could not save API key: {}",
        "powered_by": "✨ Powered by Claude AI + Real Octoparse Data",

        # Call Notes
        "call_notes": "📞 SALES CALL NOTES",
        "calls_logged": "{} call(s) logged",
        "export_excel": "📊 Export Master Excel",
        "refresh_data": "🔄 Refresh Data",
        "log_new_call": "➕ Log New Call",
        "call_details": "Call Details",
        "call_date": "Call Date",
        "contact_name": "Contact Name",
        "contact_placeholder": "e.g. Marco Rossi",
        "interest_level": "Interest Level",
        "sales_context": "Sales Context",
        "main_objection": "Main Objection",
        "objection_placeholder": "e.g. Budget",
        "budget_range": "Budget Range",
        "budget_placeholder": "e.g. €100-200/mo",
        "confidence_level": "Confidence Level (Close %)",
        "follow_up_section": "Follow-up",
        "next_steps": "Next Steps",
        "next_steps_placeholder": "e.g. Send proposal",
        "followup_date": "Follow-up Date",
        "preparation": "Preparation",
        "decision_timeline": "Decision Timeline",
        "timeline_placeholder": "e.g. 30 days, Q2 budget",
        "competitor_tools": "Competitor Tools Mentioned",
        "competitor_placeholder": "e.g. Google My Business only",
        "products_discussed": "📦 Products Discussed",
        "outcome": "Outcome",
        "outcome_pending": "Pending",
        "outcome_won": "Won",
        "outcome_lost": "Lost",
        "detailed_notes": "Detailed Notes",
        "notes_placeholder": "Key discussion points, objections raised, etc.",
        "save_call": "💾 Save Call",
        "call_saved": "✅ Call saved for {}",
        "previous_calls": "📞 Previous Calls ({} total)",
        "call_number": "Call #{} — {}",
        "interest": "Interest:",
        "delete_call": "🗑️ Delete",
        "call_deleted": "✅ Call deleted",
        "delete_error": "Could not delete call — index may be out of range",

        # Silent Winners
        "silent_winners_title": "🌟 SILENT WINNERS",
        "silent_winners_subtitle": "High-Potential Sales Targets",
        "silent_winners_desc": "Restaurants with strong ratings but low engagement — prime opportunity for response automation",
        "silent_winners_criteria": "No silent winners detected in {} (need rating ≥4.5, reviews ≥50, response rate <30%)",
        "opportunity": "€{}/mo",

        # Silent Winners Table
        "table_restaurant": "Restaurant",
        "table_rating": "Rating",
        "table_reviews": "Reviews",
        "table_response": "Response %",
        "table_sentiment": "Sentiment",
        "table_rank": "Rank",
        "table_opportunity": "Opportunity",

        # PDF Report
        "pdf_intelligence_engine": "INTELLIGENCE ENGINE ACTIVE v1.3",
        "pdf_restaurant": "RESTAURANT",
        "pdf_revenue": "REVENUE",
        "pdf_intelligence": "INTELLIGENCE",
        "pdf_ranked": "Ranked #{rank} of {total} Establishments",
        "pdf_health_score": "HEALTH SCORE",
        "pdf_district_rank": "DISTRICT RANK",
        "pdf_star_rating": "STAR RATING",
        "pdf_responsiveness": "RESPONSIVENESS",
        "pdf_confidential": "Prepared exclusively for Praxiotech GmbH sales team  ·  CONFIDENTIAL",
        "pdf_exec_summary": "01 / Executive Summary",
        "pdf_dimension_analysis": "02 / Dimension Deep-Dive Analysis",
        "pdf_gap_analysis": "03 / Gap Analysis & Opportunities",
        "pdf_momentum": "04 / Momentum & Review Analytics",
        "pdf_action_plan": "05 / Action Plan & Product Fit",
        "pdf_opportunity": "Opportunity Value",
        "pdf_dimension": "Dimension",
        "pdf_score": "Score",
        "pdf_benchmark": "Benchmark",
        "pdf_gap": "Gap",
        "pdf_status": "Status",
        "pdf_weight": "Weight",
        "pdf_current": "Current",
        "pdf_target": "Target",
        "pdf_solution": "Praxiotech Solution",
        "pdf_investment": "Investment",
        "pdf_timeline": "Timeline",
        "pdf_est_lift": "Est. Lift",

        # Footer
        "establishments": "Establishments",
        "ranked_count": "Ranked",
        "realtime_analytics": "Real-time Analytics",
        "powered_by_footer": "✨ Powered by Praxiotech GmbH",
    },

    "DE": {
        # Page titles
        "page_title": "Restaurant Intelligence Engine v2.0",

        # Sidebar
        "sidebar_title": "Intelligence Engine v2.0",
        "sidebar_subtitle": "Restaurant Audit Plattform",
        "city_filter": "🌍 Stadt Filter",
        "all_cities": "Alle Städte",
        "restaurant_select": "🏪 Restaurant auswählen",
        "advanced_filters": "⚙️ Erweiterte Filter",
        "min_rating": "Mindestbewertung",
        "min_reviews": "Mindest-Bewertungen",
        "min_response": "Min. Antwort %",
        "silent_winners_detected": "🔴 {} Stille Gewinner erkannt",
        "total_restaurants": "Gesamt: <b>{}</b> Restaurants in {}",
        "language": "🌐 Sprache",

        # Loading state
        "loading": "Restaurant-Daten werden geladen...",

        # No data
        "no_restaurants": "⚠️ Keine Restaurants verfügbar. Bitte überprüfen Sie Ihre Daten.",

        # Page Header
        "ranked": "Bewertet",
        "of": "von",
        "score": "Punktzahl",
        "rating": "Bewertung",
        "reviews": "Bewertungen",
        "silent_winner_badge": "🔴 STILLER GEWINNER",

        # Navigation buttons
        "btn_dashboard": "📊 Intelligenz-Dashboard",
        "btn_assistant": "🤖 KI-Verkaufsassistent",
        "btn_notes": "📋 Anrufnotizen",
        "btn_silent_winners": "🌟 Stille Gewinner",

        # Dashboard - KPIs
        "kpi_score": "Gesamtpunktzahl",
        "kpi_rank": "Rang",
        "kpi_response": "Antwortquote",
        "kpi_sentiment": "Stimmung",
        "kpi_freshness": "Aktualität",
        "out_of_100": "von 100",
        "total": "{} gesamt",
        "owner_replies": "Besitzer antwortet",
        "review_sentiment": "Bewertungsstimmung",
        "review_velocity": "Bewertungsgeschwindigkeit",
        "active": "Aktiv",
        "good": "Gut",
        "low": "Niedrig",
        "strong": "Stark",
        "needs_work": "Verbesserungsbedürftig",
        "good_status": "↗ Gut",
        "low_status": "↘ Niedrig",
        "strong_status": "↗ Stark",
        "needs_work_status": "↘ Verbesserungsbedürftig",
        "active_status": "↗ Aktiv",
        "slow_status": "↘ Langsam",

        # Dashboard - Charts
        "dimension_radar": "⚙️ Dimensions-Radar",
        "gap_analysis": "📊 Lückenanalyse vs. Benchmark",
        "responsiveness": "Reaktionsfähigkeit",
        "market_sentiment": "Marktstimmung",
        "review_freshness": "Bewertungsaktualität",
        "brand_visibility": "Markensichtbarkeit",
        "reputation": "Ruf",
        "digital_presence": "Digitale Präsenz",
        "intelligence": "Intelligenz",
        "visibility": "Sichtbarkeit",

        # Dashboard - Persona and Actions
        "customer_insights": "👤 KI-Kundeneinblicke",
        "primary_persona": "PRIMÄRE PERSONA",
        "segment": "SEGMENT:",
        "motivation": "Motivation:",
        "export_pdf": "📄 PDF-Bericht exportieren",
        "pdf_error": "PDF-Fehler: {}",
        "actionable_solutions": "💡 Umsetzbare Lösungen",
        "priority_high": "HOCH",
        "priority_medium": "MITTEL",
        "priority_low": "NIEDRIG",

        # Dashboard - Momentum
        "momentum": "📈 Impulse & Bewertungen",
        "rating_split": "Bewertungsaufteilung",
        "health": "Gesundheit",

        # Dashboard - Leaderboard
        "top_restaurants": "🏆 Top 10 Restaurants",

        # AI Assistant
        "ai_assistant_header": "🤖 KI-VERKAUFSASSISTENT",
        "ai_assistant_subtitle": "Claude fragen über",
        "ai_assistant_description": "💡 Fragen Sie etwas über Leistung, Strategien, Wachstumschancen oder nächste Schritte",
        "ask_placeholder": "Frage zu {} …",
        "suggested_questions": "💡 Vorgeschlagene Fragen:",
        "followup_questions": "💬 Anschlussfragen:",
        "similar_questions": "🔍 Ähnliche Fragen:",
        "clear_chat": "🗑️ Chat löschen",
        "claude_thinking": "Claude denkt nach…",
        "generating_questions": "Verwandte Fragen werden generiert…",
        "configure_api": "Anthropic API-Schlüssel konfigurieren (optional)",
        "api_instructions": "Geben Sie hier Ihren Anthropic API-Schlüssel ein, um den KI-Assistenten zu aktivieren. Schlüssel werden in der .env-Datei des Projekts gespeichert.",
        "api_key_placeholder": "sk-...",
        "save_api_key": "API-Schlüssel speichern",
        "api_key_saved": "API-Schlüssel in .env gespeichert — bitte starten Sie die App neu.",
        "api_key_error": "API-Schlüssel konnte nicht gespeichert werden: {}",
        "powered_by": "✨ Powered by Claude AI + Real Octoparse Data",

        # Call Notes
        "call_notes": "📞 VERKAUFSGESPRÄCHSNOTIZEN",
        "calls_logged": "{} Anrufe protokolliert",
        "export_excel": "📊 Master Excel exportieren",
        "refresh_data": "🔄 Daten aktualisieren",
        "log_new_call": "➕ Neuen Anruf protokollieren",
        "call_details": "Anruf-Details",
        "call_date": "Anrufdatum",
        "contact_name": "Kontaktname",
        "contact_placeholder": "z.B. Marco Rossi",
        "interest_level": "Interessensstufe",
        "sales_context": "Verkaufskontext",
        "main_objection": "Haupteinwand",
        "objection_placeholder": "z.B. Budget",
        "budget_range": "Budgetbereich",
        "budget_placeholder": "z.B. €100-200/Monat",
        "confidence_level": "Sicherheitsstufe (Abschluss %)",
        "follow_up_section": "Nachverfolgung",
        "next_steps": "Nächste Schritte",
        "next_steps_placeholder": "z.B. Angebot senden",
        "followup_date": "Nachverfolgungsdatum",
        "preparation": "Vorbereitung",
        "decision_timeline": "Entscheidungsfrist",
        "timeline_placeholder": "z.B. 30 Tage, Q2-Budget",
        "competitor_tools": "Erwähnte Konkurrenztools",
        "competitor_placeholder": "z.B. Nur Google My Business",
        "products_discussed": "📦 Besprochene Produkte",
        "outcome": "Ergebnis",
        "outcome_pending": "Ausstehend",
        "outcome_won": "Gewonnen",
        "outcome_lost": "Verloren",
        "detailed_notes": "Detaillierte Notizen",
        "notes_placeholder": "Wichtige Diskussionspunkte, aufgedeckte Einwände usw.",
        "save_call": "💾 Anruf speichern",
        "call_saved": "✅ Anruf für {} gespeichert",
        "previous_calls": "📞 Vorherige Anrufe ({} gesamt)",
        "call_number": "Anruf #{} — {}",
        "interest": "Interesse:",
        "delete_call": "🗑️ Löschen",
        "call_deleted": "✅ Anruf gelöscht",
        "delete_error": "Anruf konnte nicht gelöscht werden — Index ist möglicherweise außerhalb des Bereichs",

        # Silent Winners
        "silent_winners_title": "🌟 STILLE GEWINNER",
        "silent_winners_subtitle": "Potenzielle Verkaufsziele mit hohem Potenzial",
        "silent_winners_desc": "Restaurants mit starken Bewertungen, aber niedriger Engagement — ausgezeichnete Gelegenheit für Antwortautomatisierung",
        "silent_winners_criteria": "Keine stillen Gewinner in {} erkannt (benötigt Bewertung ≥4,5, Bewertungen ≥50, Antwortquote <30%)",
        "opportunity": "€{}/Monat",

        # Silent Winners Table
        "table_restaurant": "Restaurant",
        "table_rating": "Bewertung",
        "table_reviews": "Bewertungen",
        "table_response": "Antwort %",
        "table_sentiment": "Stimmung",
        "table_rank": "Rang",
        "table_opportunity": "Gelegenheit",

        # PDF Report
        "pdf_intelligence_engine": "INTELLIGENZ-ENGINE AKTIV v1.3",
        "pdf_restaurant": "RESTAURANT",
        "pdf_revenue": "UMSATZ",
        "pdf_intelligence": "INTELLIGENZ",
        "pdf_ranked": "Bewertet #{rank} von {total} Restaurants",
        "pdf_health_score": "GESUNDHEITSSCORE",
        "pdf_district_rank": "BEZIRKSRANG",
        "pdf_star_rating": "STERNBEWERTUNG",
        "pdf_responsiveness": "REAKTIONSFÄHIGKEIT",
        "pdf_confidential": "Ausschließlich für das Praxiotech GmbH Vertriebsteam erstellt  ·  VERTRAULICH",
        "pdf_exec_summary": "01 / Zusammenfassung",
        "pdf_dimension_analysis": "02 / Dimension Tiefenanalyse",
        "pdf_gap_analysis": "03 / Lückenanalyse & Möglichkeiten",
        "pdf_momentum": "04 / Impulse & Bewertungsanalytik",
        "pdf_action_plan": "05 / Aktionsplan & Produktpassung",
        "pdf_opportunity": "Opportunitätswert",
        "pdf_dimension": "Dimension",
        "pdf_score": "Punktzahl",
        "pdf_benchmark": "Benchmark",
        "pdf_gap": "Lücke",
        "pdf_status": "Status",
        "pdf_weight": "Gewichtung",
        "pdf_current": "Aktuell",
        "pdf_target": "Ziel",
        "pdf_solution": "Praxiotech Lösung",
        "pdf_investment": "Investition",
        "pdf_timeline": "Zeitrahmen",
        "pdf_est_lift": "Geschätzte Steigerung",

        # Footer
        "establishments": "Restaurants",
        "ranked_count": "Bewertet",
        "realtime_analytics": "Echtzeit-Analytik",
        "powered_by_footer": "✨ Powered by Praxiotech GmbH",
    }
}

def t(key: str, lang: str = "EN", **kwargs) -> str:
    """
    Translate a key to the specified language.

    Args:
        key: Translation key (e.g., "page_title")
        lang: Language code ("EN" or "DE")
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string
    """
    if lang not in TRANSLATIONS:
        lang = "EN"

    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["EN"].get(key, f"[{key}]"))

    # Handle format strings with kwargs
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

    return text

