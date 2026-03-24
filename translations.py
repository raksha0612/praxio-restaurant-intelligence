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
        "btn_notes": "📋 Visit Log",
        "btn_pipeline": "📈 Sales Pipeline",
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
        "powered_by": "✨ Powered by Claude AI + Real Octoparse Data",

        # Visit Log (Call Notes — updated to match Excel template)
        "call_notes_header": "📋 VISIT LOG",
        "calls_logged": "{} visit(s) logged",
        "active_account": "Active Account",
        "export_excel": "📊 Export Master Excel",
        "refresh_data": "🔄 Refresh Data",
        "log_new_visit": "➕ Log New Visit",

        # Visit form sections
        "section_visit_details": "📋 Visit Details",
        "section_sales_context": "💼 Sales Context",
        "section_followup": "📅 Follow-up",
        "section_reflection": "🧠 Self-Reflection",
        "section_products": "📦 Products Shown",
        "section_outcome": "🏁 Outcome",
        "section_images": "📸 Attach Images (optional)",

        # Visit form fields
        "visit_date": "Visit Date",
        "visit_time": "Visit Time (e.g. 14:30)",
        "city": "City",
        "district": "District (Stadtteil)",
        "price_class": "Price Class",
        "size": "Size",
        "contact_name": "Contact Person",
        "contact_placeholder": "e.g. Martin – Waiter, Male, ~40",
        "contact_gender_age": "Contact Role & Gender",
        "atmosphere": "Atmosphere on Site",
        "atmosphere_placeholder": "e.g. Few customers, 2 waiters present",
        "visit_duration": "Visit Duration",
        "duration_placeholder": "e.g. 15 min.",
        "pre_check_needs": "Pre-Check Needs",
        "pre_check_placeholder": "e.g. No online booking, slow website",
        "potential_score": "Potential Estimate (1–10)",
        "interest_level": "Interest Level (1–5)",
        "main_objection": "Main Objection",
        "objection_placeholder": "e.g. Price too high",
        "budget_range": "Budget Range",
        "budget_placeholder": "e.g. €100–200/mo",
        "confidence_level": "Confidence Level (Close %)",
        "next_steps": "Next Steps / Follow-up Plan",
        "next_steps_placeholder": "e.g. Call back Monday 09:00 to confirm demo",
        "followup_date": "Follow-up Date",
        "decision_timeline": "Decision Timeline",
        "timeline_placeholder": "e.g. 30 days, Q2 budget",
        "competitor_tools": "Competitor Tools Mentioned",
        "competitor_placeholder": "e.g. Google My Business only",
        "detailed_notes": "📝 Detailed Notes",
        "notes_placeholder": "Full visit narrative — what you saw, said, and agreed upon…",
        "self_reflection": "Self-Reflection (for coaching with Kevin)",
        "reflection_placeholder": "What went well? What do you need from Kevin? Key learning?",
        "save_visit": "💾 Save Visit",
        "visit_saved": "✅ Visit saved for {}",
        "previous_visits": "📋 Previous Visits ({} total)",
        "visit_number": "Visit #{} — {}",
        "delete_visit": "🗑️ Delete",
        "visit_deleted": "✅ Visit deleted",
        "delete_error": "Could not delete — index may be out of range",
        "images_hint": "Upload screenshots, business cards, or any relevant visuals.",

        # Outcome options
        "outcome_pending": "Pending",
        "outcome_interested": "Interested",
        "outcome_demo_scheduled": "Demo Scheduled",
        "outcome_proposal_sent": "Proposal Sent",
        "outcome_won": "Won",
        "outcome_lost": "Lost",

        # Products list
        "products_discussed": "Products Shown",

        # Sales Pipeline
        "pipeline_header": "📈 SALES PIPELINE",
        "pipeline_subtitle": "Opportunity Ranking",
        "pipeline_desc": "Ranked by opportunity score — biggest gaps + uncontacted leads surface first.",
        "pipeline_total": "Total Restaurants",
        "pipeline_uncontacted": "Uncontacted",
        "pipeline_fresh_leads": "↑ fresh leads",
        "pipeline_contacted": "Contacted",
        "pipeline_in_pipeline": "in pipeline",
        "pipeline_avg_gap": "Avg Score Gap",
        "pipeline_filter_district": "District",
        "pipeline_filter_status": "Status",
        "pipeline_show_top": "Show top",
        "pipeline_status_all": "All",
        "pipeline_status_uncontacted": "Uncontacted",
        "pipeline_status_contacted": "Contacted",
        "pipeline_opp_score": "opp",
        "pipeline_download": "⬇️ Download Master Excel (all restaurants + visit notes)",
        "pipeline_no_booking": "No booking",
        "pipeline_silent_owner": "Silent winner",
        "pipeline_on_target": "On target",
        "pipeline_growth": "Growth",
        "pipeline_gap": "Gap",
        "tag_above_avg": "✅ Above Average",
        "tag_below_avg": "⚠️ Below Average",

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
        "btn_notes": "📋 Besuchsprotokoll",
        "btn_pipeline": "📈 Vertriebspipeline",
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
        "powered_by": "✨ Powered by Claude AI + Real Octoparse Data",

        # Visit Log
        "call_notes_header": "📋 BESUCHSPROTOKOLL",
        "calls_logged": "{} Besuch(e) protokolliert",
        "active_account": "Aktiver Account",
        "export_excel": "📊 Master Excel exportieren",
        "refresh_data": "🔄 Daten aktualisieren",
        "log_new_visit": "➕ Neuen Besuch protokollieren",

        # Visit form sections
        "section_visit_details": "📋 Besuchsdetails",
        "section_sales_context": "💼 Verkaufskontext",
        "section_followup": "📅 Nachverfolgung",
        "section_reflection": "🧠 Selbstreflexion",
        "section_products": "📦 Gezeigte Produkte",
        "section_outcome": "🏁 Ergebnis",
        "section_images": "📸 Bilder anhängen (optional)",

        # Visit form fields
        "visit_date": "Besuchsdatum",
        "visit_time": "Uhrzeit (z.B. 14:30)",
        "city": "Stadt",
        "district": "Stadtteil",
        "price_class": "Preisklasse",
        "size": "Größe",
        "contact_name": "Gesprächspartner",
        "contact_placeholder": "z.B. Martin – Kellner, Männlich, ca. 40 Jahre alt",
        "contact_gender_age": "Rolle & Geschlecht",
        "atmosphere": "Stimmung vor Ort",
        "atmosphere_placeholder": "z.B. Wenige Kunden, 2 Kellner vor Ort",
        "visit_duration": "Dauer des Gesprächs",
        "duration_placeholder": "z.B. 15 Min.",
        "pre_check_needs": "Bedarf Pre-Check",
        "pre_check_placeholder": "z.B. Keine Online-Buchung, Website lädt langsam",
        "potential_score": "Einschätzung des Potenzials (1–10)",
        "interest_level": "Interessensstufe (1–5)",
        "main_objection": "Haupteinwand",
        "objection_placeholder": "z.B. Budget zu hoch",
        "budget_range": "Budgetbereich",
        "budget_placeholder": "z.B. €100–200/Monat",
        "confidence_level": "Sicherheitsstufe (Abschluss %)",
        "next_steps": "Nächste Schritte / Follow-up Plan",
        "next_steps_placeholder": "z.B. Montag 09:00 Telefonat zur Demo-Bestätigung",
        "followup_date": "Nachverfolgungsdatum",
        "decision_timeline": "Entscheidungsfrist",
        "timeline_placeholder": "z.B. 30 Tage, Q2-Budget",
        "competitor_tools": "Erwähnte Konkurrenztools",
        "competitor_placeholder": "z.B. Nur Google My Business",
        "detailed_notes": "📝 Ausführliche Notizen",
        "notes_placeholder": "Vollständiger Besuchsbericht – was Sie gesehen, gesagt und vereinbart haben…",
        "self_reflection": "Selbstreflexion (Basis für Dialog mit Kevin)",
        "reflection_placeholder": "Was lief gut? Was brauche ich von Kevin? Lerneffekt?",
        "save_visit": "💾 Besuch speichern",
        "visit_saved": "✅ Besuch gespeichert für {}",
        "previous_visits": "📋 Vorherige Besuche ({} gesamt)",
        "visit_number": "Besuch #{} — {}",
        "delete_visit": "🗑️ Löschen",
        "visit_deleted": "✅ Besuch gelöscht",
        "delete_error": "Löschen fehlgeschlagen — Index außerhalb des Bereichs",
        "images_hint": "Screenshots, Visitenkarten oder sonstige Bilder hochladen.",

        # Outcome options
        "outcome_pending": "Ausstehend",
        "outcome_interested": "Interessiert",
        "outcome_demo_scheduled": "Demo vereinbart",
        "outcome_proposal_sent": "Angebot gesendet",
        "outcome_won": "Gewonnen",
        "outcome_lost": "Verloren",

        # Products
        "products_discussed": "Gezeigte Produkte",

        # Sales Pipeline
        "pipeline_header": "📈 VERTRIEBSPIPELINE",
        "pipeline_subtitle": "Opportunity-Ranking",
        "pipeline_desc": "Sortiert nach Opportunity-Score — größte Lücken & unkontaktierte Leads zuerst.",
        "pipeline_total": "Restaurants gesamt",
        "pipeline_uncontacted": "Unkontaktiert",
        "pipeline_fresh_leads": "↑ neue Leads",
        "pipeline_contacted": "Kontaktiert",
        "pipeline_in_pipeline": "in Pipeline",
        "pipeline_avg_gap": "Ø Score-Lücke",
        "pipeline_filter_district": "Stadtteil",
        "pipeline_filter_status": "Status",
        "pipeline_show_top": "Top anzeigen",
        "pipeline_status_all": "Alle",
        "pipeline_status_uncontacted": "Unkontaktiert",
        "pipeline_status_contacted": "Kontaktiert",
        "pipeline_opp_score": "Opp",
        "pipeline_download": "⬇️ Master Excel herunterladen (alle Restaurants + Besuchsnotizen)",
        "pipeline_no_booking": "Kein Booking",
        "pipeline_silent_owner": "Stiller Gewinner",
        "pipeline_on_target": "Im Ziel",
        "pipeline_growth": "Wachstum",
        "pipeline_gap": "Lücke",
        "tag_above_avg": "✅ Überdurchschnittlich",
        "tag_below_avg": "⚠️ Unterdurchschnittlich",

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
    if lang not in TRANSLATIONS:
        lang = "EN"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["EN"].get(key, f"[{key}]"))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text