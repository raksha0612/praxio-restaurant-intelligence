# 🌐 Multi-Language Support - Restaurant Intelligence Engine

## Overview
Your app now supports **English (EN)** and **German (DE)** languages! Users can switch languages at the top of the sidebar, and the interface will adapt accordingly.

---

## What's Implemented

### ✅ Language Selector
- **Location**: Top of sidebar, with 🇬🇧 EN and 🇩🇪 DE buttons
- **How it works**: Click either button to switch language instantly
- **Current language**: Displayed below the buttons
- **Persistent**: Sets language in session state

### ✅ Translated UI Elements

#### Sidebar
- "Intelligence Engine v2.0" → "Intelligence Engine v2.0" (same in both languages)
- "Restaurant Audit Platform" → "Restaurant Audit Plattform"

#### Navigation Buttons
- "📊 Intelligence Dashboard" → "📊 Intelligenz-Dashboard"
- "🤖 AI Sales Assistant" → "🤖 KI-Verkaufsassistent"
- "📋 Call Notes" → "📋 Anrufnotizen"
- "🌟 Silent Winners" → "🌟 Stille Gewinner"

#### PDF Export
- "📄 Export PDF Report" → "📄 PDF-Bericht exportieren"
- Language parameter passed to PDF generator
- PDF filename includes language suffix in future versions

### ✅ Translation Infrastructure
- **File**: `translations.py`
- **Function**: `t(key, language, **kwargs)` - translates any key
- **Coverage**: 80+ translation keys prepared
- **Format**: Nested dictionary `TRANSLATIONS["EN"]` and `TRANSLATIONS["DE"]`

### ✅ PDF Report Support
All PDF generation functions now accept a `language` parameter:
```python
generate_pdf_report(..., language=st.session_state.language)
```

---

## How to Extend Translations

### Adding a New Translated String

1. **Add to translations.py**:
   ```python
   TRANSLATIONS = {
       "EN": {
           "my_new_key": "English text here",
           ...
       },
       "DE": {
           "my_new_key": "Deutscher Text hier",
           ...
       }
   }
   ```

2. **Use in app.py**:
   ```python
   text = t("my_new_key", st.session_state.language)
   st.write(text)
   ```

### Translating PDF Content

The PDF report functions accept `language` parameter. To translate PDF report text:

1. **Update translations.py** with PDF text keys
2. **Import translations** in report_generator.py:
   ```python
   from translations import t
   ```
3. **Replace hardcoded text** in PDF functions:
   ```python
   # Before:
   story.append(Paragraph("Executive Summary", STYLES['H1']))

   # After:
   story.append(Paragraph(t("exec_summary_title", language), STYLES['H1']))
   ```

---

## Current Translation Coverage

### Ready to Use (80+ keys)
- Page titles and headers
- Sidebar sections
- Navigation buttons
- KPI labels and metrics
- Form labels and placeholders
- Chart titles
- Button labels
- Call note sections
- Silent winners sections
- Footer text

### Ready to Extend (Currently English Only)
- PDF report content (all pages)
- Detailed chart descriptions
- Persona information (AI-generated)
- Review excerpts

---

## Example: Complete Translation Flow

### Scenario: User switches to German

1. **Clicks 🇩🇪 DE button**
   ```
   st.session_state.language = "DE"
   st.rerun()
   ```

2. **Page reloads with German**
   - "📊 Intelligence Dashboard" → "📊 Intelligenz-Dashboard"
   - All buttons update
   - Sidebar text translates
   - PDF export now generates German reports (infrastructure ready)

3. **PDF Export**
   - User clicks "📄 PDF-Bericht exportieren"
   - PDF is generated with `language="DE"`
   - PDF functions ready to use German text (extend as needed)

---

## Translation Dictionary Structure

Each key maps to both EN and DE versions:

```python
TRANSLATIONS = {
    "EN": {
        "category_subcategory": "English text",
        ...
    },
    "DE": {
        "category_subcategory": "Deutscher Text",
        ...
    }
}
```

### Naming Convention
- `btn_*` - Button labels
- `kpi_*` - KPI metrics
- `label_*` - Form labels
- `placeholder_*` - Input placeholders
- `sidebar_*` - Sidebar elements
- `section_*` - Section headers

---

## Quick Reference: Key Files

| File | Purpose |
|------|---------|
| `translations.py` | Translation dictionaries + `t()` function |
| `app/app.py` | Main app using `t()` for UI strings |
| `report_generator.py` | PDF generation with language support |
| `restaurant_chat.py` | AI chat (can extend with language prompts) |

---

## Advanced: Language-Specific Behavior

The `language` parameter can be used for more than text:

```python
if st.session_state.language == "DE":
    # German-specific formatting, date formats, etc.
    date_format = "%d.%m.%Y"
else:
    # English
    date_format = "%m/%d/%Y"
```

---

## Testing the Feature

1. **Start the app**: `.\do.ps1 app`
2. **Click language buttons** in sidebar
3. **Verify navigation buttons change**
4. **Test PDF export** to confirm language parameter passes through
5. **Check sidebar** title and subtitle translate

---

## Limitations (To Address If Needed)

Currently English-only in:
- PDF report main content (easy to extend)
- AI chat system prompt (can add language-aware instructions)
- Form placeholder text (most are already translated)
- Error messages (can extend)

All of these can be translated by following the pattern above.

---

## Next Steps

To fully translate the app:

1. **Priority 1** - Add remaining form/button labels to translations.py (quick)
2. **Priority 2** - Translate PDF report sections (requires finding/replacing hardcoded text)
3. **Priority 3** - Add language-aware AI prompts in restaurant_chat.py
4. **Priority 4** - Test with real German users and refine terminology

---

##Notes

- Translation function `t()` is intelligent - if a key is missing in a language, it falls back to English
- Format strings work: `t("msg", lang, count=5)` → "You have 5 items"
- Language persists in session - users can switch anytime
- No page reload needed - instant with `st.rerun()`

---

## Support for New Languages

To add a third language (e.g., French):

1. **Add to TRANSLATIONS dict**:
   ```python
   "FR": {
       "sidebar_title": "Moteur d'Intelligence",
       ...
   }
   ```

2. **Add button in sidebar**:
   ```python
   if st.button("🇫🇷 FR", ...):
       st.session_state.language = "FR"
   ```

That's it! The system is extensible.

---

Enjoy your multi-language app! 🌍
