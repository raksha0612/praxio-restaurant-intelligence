"""
excel_exporter.py — Excel Export for Call Notes & Analytics
=============================================================
Multi-sheet workbook generation:
  Sheet 1: Master Call Log (all restaurants + calls)
  Sheet 2: Pipeline Summary (metrics + forecasting)
  Sheet 3: Product Analytics (product frequency + correlation)
  Sheet 4: Action Items (overdue follow-ups + next steps)

Uses openpyxl for styling, pandas for data processing.
"""
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

TEAL = "0EA5E9"
TEAL2 = "14B8A6"
NAVY = "0F172A"
GRAY = "64748B"
SUCCESS = "22C55E"
WARNING = "F59E0B"
DANGER = "EF4444"


def export_call_notes_to_excel(call_notes_dir: Path) -> bytes:
    """
    Create multi-sheet Excel workbook with all call notes and analytics.

    Args:
        call_notes_dir: Path to scripts/data/call_notes directory

    Returns:
        Excel file as bytes (ready for download)
    """
    # Ensure directory exists
    call_notes_dir.mkdir(parents=True, exist_ok=True)

    # Load all call notes from JSON files
    all_calls = []
    restaurant_data = {}

    if call_notes_dir.exists():
        for json_file in call_notes_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                rest_id = json_file.stem
                calls = data.get("calls", [])

                for call in calls:
                    call["restaurant_id"] = rest_id
                    call["restaurant_name"] = rest_id.replace("_", " ").title()
                    all_calls.append(call)

                restaurant_data[rest_id] = {
                    "total_calls": len(calls),
                    "avg_interest": sum(c.get("interest_level", 0) for c in calls) / len(calls) if calls else 0,
                    "last_call": calls[-1].get("call_date", "N/A") if calls else "N/A",
                }
            except Exception as e:
                logger.warning(f"Error loading {json_file}: {e}")

    # Create workbook with styling
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Sheet 1: Master Call Log
    _create_call_log_sheet(wb, all_calls)

    # Sheet 2: Pipeline Summary
    _create_pipeline_sheet(wb, all_calls, restaurant_data)

    # Sheet 3: Product Analytics
    _create_product_sheet(wb, all_calls)

    # Sheet 4: Action Items
    _create_action_items_sheet(wb, all_calls)

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def _create_call_log_sheet(wb: Workbook, calls: list) -> None:
    """Create Sheet 1: Master Call Log (sorted by date, newest first)."""
    ws = wb.create_sheet("Call History", 0)

    # Headers
    headers = [
        "Restaurant", "Call Date", "Contact Name", "Interest Level", "Confidence %",
        "Main Objection", "Budget Range", "Decision Timeline", "Competitor Tools",
        "Products Discussed", "Outcome", "Next Steps", "Follow-up Date", "Notes"
    ]
    ws.append(headers)

    # Header styling
    header_fill = PatternFill(start_color=TEAL, end_color=TEAL, fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border

    # Sort calls by date (newest first)
    sorted_calls = sorted(
        calls,
        key=lambda x: datetime.strptime(x.get("call_date", "1900-01-01"), "%Y-%m-%d"),
        reverse=True
    )

    # Add data rows
    for call in sorted_calls:
        row = [
            call.get("restaurant_name", "—"),
            call.get("call_date", "—"),
            call.get("contact_name", "—"),
            call.get("interest_level", "—"),
            call.get("confidence_level", "—"),
            call.get("main_objection", "—"),
            call.get("budget_range", "—"),
            call.get("decision_timeline", "—"),
            call.get("competitor_tools", "—"),
            ", ".join(call.get("products_discussed", [])) or "—",
            call.get("outcome", "Pending"),
            call.get("next_steps", "—"),
            call.get("follow_up_date", "—"),
            call.get("notes", "—")[:100],  # Truncate notes
        ]
        ws.append(row)

        # Row styling
        row_num = ws.max_row
        for col_num, cell in enumerate(ws[row_num], 1):
            cell.border = border
            cell.alignment = Alignment(wrap_text=True, vertical="top")

            # Color-code interest level (column 4)
            if col_num == 4:
                interest = call.get("interest_level", 0)
                if interest >= 4:
                    cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
                    cell.font = Font(bold=True, color="166534")
                elif interest >= 2:
                    cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                    cell.font = Font(bold=True, color="92400E")
                else:
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    cell.font = Font(bold=True, color="991B1B")

            # Color-code outcome (column 11)
            if col_num == 11:
                outcome = call.get("outcome", "Pending").lower()
                if outcome == "won":
                    cell.fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
                    cell.font = Font(bold=True, color="166534")
                elif outcome == "lost":
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    cell.font = Font(bold=True, color="991B1B")

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-width columns
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 13
    ws.column_dimensions["E"].width = 13
    ws.column_dimensions["F"].width = 16
    ws.column_dimensions["G"].width = 15
    ws.column_dimensions["H"].width = 16
    ws.column_dimensions["I"].width = 18
    ws.column_dimensions["J"].width = 25
    ws.column_dimensions["K"].width = 12
    ws.column_dimensions["L"].width = 20
    ws.column_dimensions["M"].width = 14
    ws.column_dimensions["N"].width = 20


def _create_pipeline_sheet(wb: Workbook, calls: list, restaurant_data: dict) -> None:
    """Create Sheet 2: Pipeline Summary with KPIs."""
    ws = wb.create_sheet("Pipeline Summary", 1)

    # Title
    title_cell = ws["A1"]
    title_cell.value = "Sales Pipeline Summary"
    title_cell.font = Font(bold=True, size=14, color=NAVY)
    ws.merge_cells("A1:D1")

    # KPIs section
    kpis = [
        ("Total Restaurants with Calls", len(restaurant_data)),
        ("Total Calls Logged", len(calls)),
        ("Average Interest Level", round(sum(c.get("interest_level", 0) for c in calls) / max(len(calls), 1), 1)),
        ("High Interest Calls (4-5)", len([c for c in calls if c.get("interest_level", 0) >= 4])),
        ("Medium Interest Calls (2-3)", len([c for c in calls if 2 <= c.get("interest_level", 0) < 4])),
        ("Low Interest Calls (1)", len([c for c in calls if c.get("interest_level", 0) == 1])),
    ]

    row = 3
    for label, value in kpis:
        ws[f"A{row}"] = label
        ws[f"B{row}"] = value
        ws[f"A{row}"].font = Font(bold=True, size=11)
        ws[f"B{row}"].font = Font(size=11)
        ws[f"A{row}"].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        ws[f"B{row}"].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        row += 1

    # Product frequency section
    ws.merge_cells(f"A{row}:B{row}")
    ws[f"A{row}"] = "Product Frequency"
    ws[f"A{row}"].font = Font(bold=True, size=12, color=NAVY)
    row += 1

    # Count product mentions
    product_counts = {}
    for call in calls:
        for product in call.get("products_discussed", []):
            product_counts[product] = product_counts.get(product, 0) + 1

    ws[f"A{row}"] = "Product Name"
    ws[f"B{row}"] = "Times Discussed"
    for col in ["A", "B"]:
        ws[f"{col}{row}"].font = Font(bold=True, color="FFFFFF")
        ws[f"{col}{row}"].fill = PatternFill(start_color=TEAL2, end_color=TEAL2, fill_type="solid")
    row += 1

    for product, count in sorted(product_counts.items(), key=lambda x: x[1], reverse=True):
        ws[f"A{row}"] = product
        ws[f"B{row}"] = count
        row += 1

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 20


def _create_product_sheet(wb: Workbook, calls: list) -> None:
    """Create Sheet 3: Product Analytics."""
    ws = wb.create_sheet("Product Analytics", 2)

    # Title
    title_cell = ws["A1"]
    title_cell.value = "Product Analytics & Correlation"
    title_cell.font = Font(bold=True, size=14, color=NAVY)
    ws.merge_cells("A1:D1")

    # Product co-occurrence matrix
    products = set()
    for call in calls:
        products.update(call.get("products_discussed", []))

    products = sorted(list(products))

    # Headers
    ws["A3"] = "Product"
    ws["B3"] = "Times Discussed"
    ws["C3"] = "Avg Interest When Discussed"
    ws["D3"] = "Close Rate Estimate"

    for col in ["A", "B", "C", "D"]:
        ws[f"{col}3"].font = Font(bold=True, color="FFFFFF")
        ws[f"{col}3"].fill = PatternFill(start_color=TEAL, end_color=TEAL, fill_type="solid")

    # Calculate metrics per product
    row = 4
    for product in products:
        product_calls = [c for c in calls if product in c.get("products_discussed", [])]
        times = len(product_calls)
        avg_interest = sum(c.get("interest_level", 0) for c in product_calls) / max(times, 1)
        close_rate = len([c for c in product_calls if c.get("interest_level", 0) >= 4]) / max(times, 1) * 100

        ws[f"A{row}"] = product
        ws[f"B{row}"] = times
        ws[f"C{row}"] = round(avg_interest, 1)
        ws[f"D{row}"] = f"{close_rate:.0f}%"

        row += 1

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 18


def _create_action_items_sheet(wb: Workbook, calls: list) -> None:
    """Create Sheet 4: Action Items (upcoming follow-ups + overdue)."""
    ws = wb.create_sheet("Action Items", 3)

    # Title
    title_cell = ws["A1"]
    title_cell.value = "Upcoming & Overdue Follow-ups"
    title_cell.font = Font(bold=True, size=14, color=NAVY)
    ws.merge_cells("A1:E1")

    # Headers
    headers = ["Restaurant", "Last Call Date", "Contact", "Next Steps", "Days Until Due", "Status"]
    ws.append(headers)

    header_fill = PatternFill(start_color=TEAL, end_color=TEAL, fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Group calls by restaurant (latest first)
    rest_calls = {}
    for call in calls:
        rest = call.get("restaurant_name", "Unknown")
        if rest not in rest_calls:
            rest_calls[rest] = []
        rest_calls[rest].append(call)

    # Sort by date within each restaurant
    for rest in rest_calls:
        rest_calls[rest] = sorted(
            rest_calls[rest],
            key=lambda x: datetime.strptime(x.get("call_date", "1900-01-01"), "%Y-%m-%d"),
            reverse=True
        )

    # Add rows for recent calls with follow-up tracking
    today = datetime.now()
    row = 2
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for rest, call_list in sorted(rest_calls.items()):
        if not call_list:
            continue
        last_call = call_list[0]
        call_date = datetime.strptime(last_call.get("call_date", today.strftime("%Y-%m-%d")), "%Y-%m-%d")
        next_steps = last_call.get("next_steps", "No follow-up scheduled")
        days_since = (today - call_date).days

        # Assume 7-day follow-up window
        due_date = call_date + timedelta(days=7)
        days_until_due = (due_date - today).days

        # Determine status
        if days_until_due < 0:
            status = "OVERDUE"
            status_color = DANGER
        elif days_until_due <= 2:
            status = "URGENT"
            status_color = WARNING
        else:
            status = "PENDING"
            status_color = SUCCESS

        ws[f"A{row}"] = rest
        ws[f"B{row}"] = last_call.get("call_date", "—")
        ws[f"C{row}"] = last_call.get("contact_name", "—")
        ws[f"D{row}"] = next_steps[:50]  # Truncate
        ws[f"E{row}"] = max(0, days_until_due)
        ws[f"F{row}"] = status

        # Color-code status
        for col in ["A", "B", "C", "D", "E", "F"]:
            ws[f"{col}{row}"].border = border
            if col == "F":
                ws[f"{col}{row}"].fill = PatternFill(start_color=status_color, end_color=status_color, fill_type="solid")
                ws[f"{col}{row}"].font = Font(bold=True, color="FFFFFF")
            else:
                ws[f"{col}{row}"].alignment = Alignment(wrap_text=True, vertical="top")

        row += 1

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 12

    ws.freeze_panes = "A2"
