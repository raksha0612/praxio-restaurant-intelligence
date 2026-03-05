"""
excel_exporter.py — Excel Export for Call Notes & Analytics
=============================================================
Multi-sheet workbook generation:
  Sheet 1: Master Call Log (all restaurants + calls + embedded images)
  Sheet 2: Pipeline Summary (metrics + forecasting)
  Sheet 3: Product Analytics (product frequency + correlation)
  Sheet 4: Action Items (overdue follow-ups + next steps)

Uses openpyxl for styling, pandas for data processing.
"""
import base64
import io
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

logger = logging.getLogger(__name__)

TEAL       = "0EA5E9"
TEAL2      = "14B8A6"
NAVY       = "0F172A"
GRAY       = "64748B"
SUCCESS    = "22C55E"
WARNING    = "F59E0B"
DANGER     = "EF4444"
LIGHT      = "F0F9FF"
BORDER_CLR = "E2E8F0"


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def export_call_notes_to_excel(call_notes_dir: Path) -> bytes:
    """
    Create multi-sheet Excel workbook with all call notes and analytics.

    Args:
        call_notes_dir: Path to scripts/data/call_notes directory

    Returns:
        Excel file as bytes (ready for download)
    """
    call_notes_dir.mkdir(parents=True, exist_ok=True)

    all_calls       = []
    restaurant_data = {}

    if call_notes_dir.exists():
        for json_file in call_notes_dir.glob("*.json"):
            try:
                data    = json.loads(json_file.read_text(encoding="utf-8"))
                rest_id = json_file.stem
                calls   = data.get("calls", [])

                for call in calls:
                    call["restaurant_id"]   = rest_id
                    call["restaurant_name"] = rest_id.replace("_", " ").title()
                    all_calls.append(call)

                restaurant_data[rest_id] = {
                    "total_calls":  len(calls),
                    "avg_interest": (
                        sum(c.get("interest_level", 0) for c in calls) / len(calls)
                        if calls else 0
                    ),
                    "last_call": calls[-1].get("call_date", "N/A") if calls else "N/A",
                }
            except Exception as e:
                logger.warning(f"Error loading {json_file}: {e}")

    wb = Workbook()
    wb.remove(wb.active)  # Remove default blank sheet

    _create_call_log_sheet(wb, all_calls)
    _create_pipeline_sheet(wb, all_calls, restaurant_data)
    _create_product_sheet(wb, all_calls)
    _create_action_items_sheet(wb, all_calls)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _std_border():
    side = Side(style="thin", color=BORDER_CLR)
    return Border(left=side, right=side, top=side, bottom=side)


def _header_style(cell, bg=TEAL):
    cell.fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font      = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = _std_border()


def _section_title(ws, cell_addr, text, merge_to=None, bg=NAVY):
    ws[cell_addr] = text
    ws[cell_addr].font      = Font(bold=True, size=13, color="FFFFFF", name="Calibri")
    ws[cell_addr].fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    ws[cell_addr].alignment = Alignment(horizontal="left", vertical="center")
    if merge_to:
        ws.merge_cells(f"{cell_addr}:{merge_to}")


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 1 — MASTER CALL LOG  (with embedded images)
# ─────────────────────────────────────────────────────────────────────────────

def _create_call_log_sheet(wb: Workbook, calls: list) -> None:
    """Sheet 1: Master Call Log sorted by date (newest first), with images."""
    try:
        from openpyxl.drawing.image import Image as XLImage
        _can_embed = True
    except ImportError:
        _can_embed = False

    ws = wb.create_sheet("📋 Call History", 0)
    ws.sheet_view.showGridLines = False

    # ── Title banner ─────────────────────────────────────────────────────────
    ws.merge_cells("A1:N1")
    ws["A1"] = "🍽️  Praxiotech Intelligence Engine v2.0 — Master Call Log"
    ws["A1"].font      = Font(bold=True, size=14, color="FFFFFF", name="Calibri")
    ws["A1"].fill      = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:N2")
    ws["A2"] = (
        f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}"
        "   ·   Confidential — Internal Sales Use Only"
    )
    ws["A2"].font      = Font(size=8, color="94A3B8", name="Calibri")
    ws["A2"].fill      = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 14

    # ── Column headers (row 4) ───────────────────────────────────────────────
    headers = [
        "Restaurant", "Call Date", "Contact Name", "Interest\n(1-5)", "Confidence\n(%)",
        "Main Objection", "Budget Range", "Decision\nTimeline", "Competitor\nTools",
        "Products Discussed", "Outcome", "Next Steps", "Follow-up\nDate", "Notes",
    ]
    col_widths = [22, 12, 18, 11, 11, 20, 15, 16, 18, 30, 12, 22, 14, 30]

    for ci, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=4, column=ci, value=h)
        _header_style(cell, bg=TEAL)
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.row_dimensions[4].height = 28

    # ── Sort calls newest first ──────────────────────────────────────────────
    sorted_calls = sorted(
        calls,
        key=lambda x: datetime.strptime(x.get("call_date", "1900-01-01"), "%Y-%m-%d"),
        reverse=True,
    )

    current_row  = 5
    outcome_bg   = {"won": "DCFCE7", "lost": "FEE2E2", "pending": "FEF3C7"}
    outcome_fg   = {"won": "166534", "lost": "991B1B", "pending": "92400E"}

    for call in sorted_calls:
        interest = call.get("interest_level", 0)
        outcome  = call.get("outcome", "Pending").lower()
        bg_alt   = "F8FAFC" if current_row % 2 == 0 else "FFFFFF"

        row_vals = [
            call.get("restaurant_name", "—"),
            call.get("call_date", "—"),
            call.get("contact_name", "—"),
            interest,
            call.get("confidence_level", "—"),
            call.get("main_objection", "—"),
            call.get("budget_range", "—"),
            call.get("decision_timeline", "—"),
            call.get("competitor_tools", "—"),
            ", ".join(call.get("products_discussed", [])) or "—",
            call.get("outcome", "Pending"),
            call.get("next_steps", "—"),
            call.get("follow_up_date", "—"),
            (call.get("notes", "") or "")[:120],
        ]

        for ci, val in enumerate(row_vals, 1):
            cell = ws.cell(row=current_row, column=ci, value=val)
            cell.border    = _std_border()
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.font      = Font(size=9, name="Calibri")
            cell.fill      = PatternFill(start_color=bg_alt, end_color=bg_alt, fill_type="solid")

            # Interest level colour (column 4)
            if ci == 4:
                if interest >= 4:
                    cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
                    cell.font = Font(bold=True, color="166534", size=9, name="Calibri")
                elif interest >= 2:
                    cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                    cell.font = Font(bold=True, color="92400E", size=9, name="Calibri")
                else:
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    cell.font = Font(bold=True, color="991B1B", size=9, name="Calibri")

            # Outcome colour (column 11)
            if ci == 11 and outcome in outcome_bg:
                cell.fill = PatternFill(
                    start_color=outcome_bg[outcome],
                    end_color=outcome_bg[outcome],
                    fill_type="solid"
                )
                cell.font = Font(bold=True, color=outcome_fg[outcome], size=9, name="Calibri")

        ws.row_dimensions[current_row].height = 18
        current_row += 1

        # ── Embedded images block ────────────────────────────────────────────
        call_images = call.get("images", [])
        if call_images and _can_embed:
            from openpyxl.drawing.image import Image as XLImage

            # Sub-header for images
            ws.merge_cells(f"A{current_row}:N{current_row}")
            img_hdr = ws.cell(
                row=current_row, column=1,
                value=(
                    f"  📸  Attached Images — {call.get('restaurant_name', '')} "
                    f"({call.get('call_date', '')})  ·  {len(call_images)} file(s)"
                ),
            )
            img_hdr.font      = Font(bold=True, size=9, color=TEAL, name="Calibri")
            img_hdr.fill      = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
            img_hdr.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[current_row].height = 14
            current_row += 1

            # Fixed thumbnail dimensions (pixels)
            THUMB_W   = 100
            THUMB_H   = 80
            IMGS_PER_ROW = 6
            # Excel: 1 point ≈ 0.75 px; row height is in points
            ROW_H_PTS = int(THUMB_H * 0.75) + 4   # ≈ 64 pts for 80px image
            COL_W_CHR = 14                          # column width in char units

            # Ensure columns B–G are wide enough for thumbnails
            for col_offset in range(IMGS_PER_ROW):
                col_letter = get_column_letter(2 + col_offset)
                ws.column_dimensions[col_letter].width = max(
                    ws.column_dimensions[col_letter].width, COL_W_CHR
                )

            # Filename label row
            label_row = current_row
            ws.row_dimensions[label_row].height = 10
            for ci_img, img_data in enumerate(call_images):
                col_letter = get_column_letter(2 + ci_img % IMGS_PER_ROW)
                if ci_img > 0 and ci_img % IMGS_PER_ROW == 0:
                    label_row += ROW_H_PTS // 10 + 2  # advance for next image row
                lbl = ws.cell(row=label_row, column=2 + ci_img % IMGS_PER_ROW,
                              value=img_data.get("filename", f"img_{ci_img+1}"))
                lbl.font      = Font(size=7, color=GRAY, name="Calibri")
                lbl.alignment = Alignment(horizontal="center")

            img_row = label_row + 1

            for ci_img, img_data in enumerate(call_images):
                row_block = ci_img // IMGS_PER_ROW
                col_num   = 2 + (ci_img % IMGS_PER_ROW)
                place_row = img_row + row_block * (ROW_H_PTS // 10 + 3)
                col_ltr   = get_column_letter(col_num)

                try:
                    raw        = base64.b64decode(img_data.get("data", ""))
                    stream     = io.BytesIO(raw)
                    xl_img     = XLImage(stream)

                    # Scale to thumbnail maintaining aspect ratio
                    ratio      = min(THUMB_W / max(xl_img.width, 1),
                                     THUMB_H / max(xl_img.height, 1))
                    xl_img.width  = int(xl_img.width  * ratio)
                    xl_img.height = int(xl_img.height * ratio)

                    ws.add_image(xl_img, f"{col_ltr}{place_row}")
                    ws.row_dimensions[place_row].height = ROW_H_PTS

                except Exception as img_err:
                    logger.warning(f"Could not embed image {ci_img}: {img_err}")

            # Advance past all image rows
            rows_of_blocks  = (len(call_images) - 1) // IMGS_PER_ROW + 1
            current_row     = img_row + rows_of_blocks * (ROW_H_PTS // 10 + 3) + 1

        # Thin separator between calls
        ws.row_dimensions[current_row].height = 4
        for ci in range(1, len(headers) + 1):
            sep = ws.cell(row=current_row, column=ci, value="")
            sep.fill = PatternFill(start_color=BORDER_CLR, end_color=BORDER_CLR, fill_type="solid")
        current_row += 1

    ws.freeze_panes = "A5"


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 2 — PIPELINE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def _create_pipeline_sheet(wb: Workbook, calls: list, restaurant_data: dict) -> None:
    """Sheet 2: Pipeline summary KPIs + outcome distribution + product frequency."""
    ws = wb.create_sheet("📊 Pipeline Summary", 1)
    ws.sheet_view.showGridLines = False

    _section_title(ws, "A1", "  📊  Sales Pipeline Summary", merge_to="D1")
    ws.merge_cells("A2:D2")
    ws["A2"] = f"Exported {datetime.now().strftime('%d %b %Y')}"
    ws["A2"].font      = Font(size=8, color="94A3B8", name="Calibri")
    ws["A2"].fill      = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws["A2"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 14

    # ── KPI section ──────────────────────────────────────────────────────────
    ws["A4"] = "Key Performance Indicators"
    ws["A4"].font = Font(bold=True, size=11, color=NAVY, name="Calibri")

    kpis = [
        ("Total Restaurants with Calls",  len(restaurant_data)),
        ("Total Calls Logged",            len(calls)),
        ("Average Interest Level",        round(
            sum(c.get("interest_level", 0) for c in calls) / max(len(calls), 1), 1
        )),
        ("High Interest Calls (4-5)",     len([c for c in calls if c.get("interest_level", 0) >= 4])),
        ("Medium Interest Calls (2-3)",   len([c for c in calls if 2 <= c.get("interest_level", 0) < 4])),
        ("Low Interest Calls (1)",        len([c for c in calls if c.get("interest_level", 0) == 1])),
        ("Deals Won",                     len([c for c in calls if c.get("outcome", "").lower() == "won"])),
        ("Deals Lost",                    len([c for c in calls if c.get("outcome", "").lower() == "lost"])),
        ("Deals Pending",                 len([c for c in calls if c.get("outcome", "Pending").lower() == "pending"])),
        ("Calls with Images Attached",    len([c for c in calls if c.get("images")])),
    ]

    kpi_colors = {
        "High Interest Calls (4-5)":  ("DCFCE7", "166534"),
        "Deals Won":                  ("DCFCE7", "166534"),
        "Deals Lost":                 ("FEE2E2", "991B1B"),
        "Low Interest Calls (1)":     ("FEE2E2", "991B1B"),
        "Calls with Images Attached": (LIGHT,    TEAL),
    }

    row = 5
    for label, value in kpis:
        bg, fg = kpi_colors.get(label, ("F1F5F9", NAVY))
        for ci, (col, val) in enumerate(zip(["A", "B"], [label, value]), 1):
            cell = ws[f"{col}{row}"]
            cell.value     = val
            cell.font      = Font(bold=(ci == 1), size=10, color=fg, name="Calibri")
            cell.fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            cell.alignment = Alignment(
                horizontal="center" if ci == 2 else "left", vertical="center"
            )
            cell.border = _std_border()
        ws.row_dimensions[row].height = 18
        row += 1

    row += 1  # spacer

    # ── Outcome distribution ─────────────────────────────────────────────────
    ws.merge_cells(f"A{row}:D{row}")
    ws[f"A{row}"] = "  Outcome Distribution"
    ws[f"A{row}"].font      = Font(bold=True, size=11, color="FFFFFF", name="Calibri")
    ws[f"A{row}"].fill      = PatternFill(start_color=TEAL2, end_color=TEAL2, fill_type="solid")
    ws[f"A{row}"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 20
    row += 1

    for outcome_label, bg, fg in [
        ("Won",     "DCFCE7", "166534"),
        ("Lost",    "FEE2E2", "991B1B"),
        ("Pending", "FEF3C7", "92400E"),
    ]:
        cnt  = len([c for c in calls if c.get("outcome", "Pending") == outcome_label])
        rate = f"{cnt / max(len(calls), 1) * 100:.1f}%"
        for ci, val in enumerate([outcome_label, cnt, rate], 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            cell.font      = Font(bold=(ci == 1), color=fg, size=10, name="Calibri")
            cell.alignment = Alignment(
                horizontal="left" if ci == 1 else "center", vertical="center"
            )
            cell.border = _std_border()
        ws.row_dimensions[row].height = 18
        row += 1

    row += 1

    # ── Product frequency ────────────────────────────────────────────────────
    ws.merge_cells(f"A{row}:D{row}")
    ws[f"A{row}"] = "  Product Frequency"
    ws[f"A{row}"].font      = Font(bold=True, size=11, color="FFFFFF", name="Calibri")
    ws[f"A{row}"].fill      = PatternFill(start_color=TEAL, end_color=TEAL, fill_type="solid")
    ws[f"A{row}"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 20
    row += 1

    for col_ltr, hdr in zip(["A", "B"], ["Product Name", "Times Discussed"]):
        cell = ws[f"{col_ltr}{row}"]
        cell.value     = hdr
        cell.font      = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
        cell.fill      = PatternFill(start_color="475569", end_color="475569", fill_type="solid")
        cell.alignment = Alignment(
            horizontal="center" if col_ltr == "B" else "left", vertical="center"
        )
        cell.border = _std_border()
    ws.row_dimensions[row].height = 18
    row += 1

    product_counts: dict = {}
    for call in calls:
        for product in call.get("products_discussed", []):
            product_counts[product] = product_counts.get(product, 0) + 1

    for product, count in sorted(product_counts.items(), key=lambda x: x[1], reverse=True):
        bg = "F0F9FF"
        ws[f"A{row}"].value     = product
        ws[f"A{row}"].font      = Font(size=9, name="Calibri")
        ws[f"A{row}"].fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
        ws[f"A{row}"].border    = _std_border()
        ws[f"B{row}"].value     = count
        ws[f"B{row}"].font      = Font(bold=True, size=9, color=TEAL, name="Calibri")
        ws[f"B{row}"].fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
        ws[f"B{row}"].alignment = Alignment(horizontal="center")
        ws[f"B{row}"].border    = _std_border()
        ws.row_dimensions[row].height = 16
        row += 1

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 16


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 3 — PRODUCT ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

def _create_product_sheet(wb: Workbook, calls: list) -> None:
    """Sheet 3: Product analytics — frequency, avg interest, close rate estimate."""
    ws = wb.create_sheet("🛒 Product Analytics", 2)
    ws.sheet_view.showGridLines = False

    _section_title(ws, "A1", "  🛒  Product Analytics & Correlation", merge_to="D1")
    ws.row_dimensions[1].height = 26

    headers = ["Product", "Times Discussed", "Avg Interest When Discussed", "Close Rate Estimate"]
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=ci, value=h)
        _header_style(cell, bg=TEAL)
    ws.row_dimensions[3].height = 22

    products: set = set()
    for call in calls:
        products.update(call.get("products_discussed", []))

    row = 4
    for product in sorted(products):
        product_calls = [c for c in calls if product in c.get("products_discussed", [])]
        times         = len(product_calls)
        avg_interest  = sum(c.get("interest_level", 0) for c in product_calls) / max(times, 1)
        close_rate    = (
            len([c for c in product_calls if c.get("interest_level", 0) >= 4])
            / max(times, 1) * 100
        )

        bg   = "F0F9FF" if row % 2 == 0 else "FFFFFF"
        vals = [product, times, round(avg_interest, 1), f"{close_rate:.0f}%"]
        for ci, val in enumerate(vals, 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.font      = Font(size=9, name="Calibri")
            cell.fill      = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            cell.alignment = Alignment(
                horizontal="left" if ci == 1 else "center", vertical="center"
            )
            cell.border = _std_border()

            # Colour-code close rate column
            if ci == 4:
                if close_rate >= 60:
                    cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
                    cell.font = Font(bold=True, color="166534", size=9, name="Calibri")
                elif close_rate >= 30:
                    cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                    cell.font = Font(bold=True, color="92400E", size=9, name="Calibri")
                else:
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    cell.font = Font(bold=True, color="991B1B", size=9, name="Calibri")

        ws.row_dimensions[row].height = 18
        row += 1

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 26
    ws.column_dimensions["D"].width = 20


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 4 — ACTION ITEMS
# ─────────────────────────────────────────────────────────────────────────────

def _create_action_items_sheet(wb: Workbook, calls: list) -> None:
    """Sheet 4: Upcoming & overdue follow-ups."""
    ws = wb.create_sheet("⚡ Action Items", 3)
    ws.sheet_view.showGridLines = False

    _section_title(ws, "A1", "  ⚡  Upcoming & Overdue Follow-ups", merge_to="F1")
    ws.row_dimensions[1].height = 26

    headers    = ["Restaurant", "Last Call Date", "Contact", "Next Steps", "Days Until Due", "Status"]
    col_widths = [26, 14, 20, 32, 16, 14]
    for ci, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=3, column=ci, value=h)
        _header_style(cell, bg=TEAL)
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.row_dimensions[3].height = 22

    # Group by restaurant — keep latest call only
    rest_calls: dict = {}
    for call in calls:
        rest = call.get("restaurant_name", "Unknown")
        if rest not in rest_calls:
            rest_calls[rest] = []
        rest_calls[rest].append(call)

    for rest in rest_calls:
        rest_calls[rest] = sorted(
            rest_calls[rest],
            key=lambda x: datetime.strptime(x.get("call_date", "1900-01-01"), "%Y-%m-%d"),
            reverse=True,
        )

    today = datetime.now()
    row   = 4

    for rest, call_list in sorted(rest_calls.items()):
        if not call_list:
            continue
        last_call  = call_list[0]
        call_date  = datetime.strptime(
            last_call.get("call_date", today.strftime("%Y-%m-%d")), "%Y-%m-%d"
        )
        next_steps = last_call.get("next_steps", "No follow-up scheduled")
        due_date   = call_date + timedelta(days=7)
        days_until = (due_date - today).days

        if days_until < 0:
            status    = "OVERDUE"
            status_bg = "FEE2E2"
            status_fg = "991B1B"
        elif days_until <= 2:
            status    = "URGENT"
            status_bg = "FEF3C7"
            status_fg = "92400E"
        else:
            status    = "PENDING"
            status_bg = "DCFCE7"
            status_fg = "166534"

        row_bg   = "F8FAFC" if row % 2 == 0 else "FFFFFF"
        row_vals = [
            rest,
            last_call.get("call_date", "—"),
            last_call.get("contact_name", "—"),
            (next_steps or "")[:60],
            max(0, days_until),
            status,
        ]

        for ci, val in enumerate(row_vals, 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.border    = _std_border()
            cell.alignment = Alignment(
                wrap_text=True, vertical="center",
                horizontal="left" if ci in (1, 3, 4) else "center",
            )
            if ci == 6:
                cell.fill = PatternFill(
                    start_color=status_bg, end_color=status_bg, fill_type="solid"
                )
                cell.font = Font(bold=True, color=status_fg, size=9, name="Calibri")
            else:
                cell.fill = PatternFill(
                    start_color=row_bg, end_color=row_bg, fill_type="solid"
                )
                cell.font = Font(size=9, name="Calibri")

        ws.row_dimensions[row].height = 18
        row += 1

    ws.freeze_panes = "A4"