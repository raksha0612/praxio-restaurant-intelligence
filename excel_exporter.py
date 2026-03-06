import base64
import io
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

TEAL       = "0EA5E9"
TEAL2      = "14B8A6"
NAVY       = "0F172A"
GRAY       = "64748B"
LIGHT      = "F0F9FF"
BORDER_CLR = "E2E8F0"

def export_call_notes_to_excel(call_notes_dir: Path) -> bytes:
    call_notes_dir.mkdir(parents=True, exist_ok=True)
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

    wb = Workbook()
    wb.remove(wb.active)
    image_anchors = _create_images_sheet(wb, all_calls)
    _create_call_log_sheet(wb, all_calls, image_anchors)
    _create_pipeline_sheet(wb, all_calls, restaurant_data)
    _create_product_sheet(wb, all_calls)
    _create_action_items_sheet(wb, all_calls)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

def _b(clr=BORDER_CLR):
    s = Side(style="thin", color=clr)
    return Border(left=s, right=s, top=s, bottom=s)

def _f(clr):
    return PatternFill(start_color=clr, end_color=clr, fill_type="solid")

def _std_border():
    return _b()

def _header_style(cell, bg=TEAL):
    cell.fill = _f(bg)
    cell.font = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = _b()

def _section_title(ws, cell_addr, text, merge_to=None, bg=NAVY):
    ws[cell_addr] = text
    ws[cell_addr].font = Font(bold=True, size=13, color="FFFFFF", name="Calibri")
    ws[cell_addr].fill = _f(bg)
    ws[cell_addr].alignment = Alignment(horizontal="left", vertical="center")
    if merge_to:
        ws.merge_cells(f"{cell_addr}:{merge_to}")

def _create_images_sheet(wb, calls):
    try:
        from openpyxl.drawing.image import Image as XLImage
        can_embed = True
    except ImportError:
        can_embed = False

    ws = wb.create_sheet("📸 Images", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 2
    ws.column_dimensions["B"].width = 72
    ws.column_dimensions["C"].width = 2

    ws.merge_cells("A1:C1")
    ws["A1"] = "  📸  Image Gallery — Full Size Attachments"
    ws["A1"].font = Font(bold=True, size=13, color="FFFFFF", name="Calibri")
    ws["A1"].fill = _f(NAVY)
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 34

    ws.merge_cells("A2:C2")
    ws["A2"] = "  Full resolution images. Click thumbnails in Call History to jump here."
    ws["A2"].font = Font(size=8, color="94A3B8", italic=True, name="Calibri")
    ws["A2"].fill = _f("1E293B")
    ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 14

    sorted_calls = sorted(calls, key=lambda x: datetime.strptime(x.get("call_date","1900-01-01"),"%Y-%m-%d"), reverse=True)
    anchors = {}
    g_row = 4

    for call in sorted_calls:
        rest_id = call.get("restaurant_id","")
        call_date = call.get("call_date","")
        rest_name = call.get("restaurant_name","—")
        for img_idx, img_data in enumerate(call.get("images",[])):
            filename = img_data.get("filename", f"image_{img_idx+1}")
            ws.merge_cells(f"A{g_row}:C{g_row}")
            hdr = ws.cell(row=g_row, column=1, value=f"  📞  {rest_name}  ·  {call_date}  ·  {filename}")
            hdr.font = Font(bold=True, size=10, color="FFFFFF", name="Calibri")
            hdr.fill = _f(TEAL)
            hdr.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[g_row].height = 22
            anchors[(rest_id, call_date, img_idx)] = g_row
            g_row += 1
            if can_embed:
                try:
                    raw = base64.b64decode(img_data.get("data",""))
                    xl = XLImage(io.BytesIO(raw))
                    ratio = min(580/max(xl.width,1), 440/max(xl.height,1))
                    xl.width = int(xl.width * ratio)
                    xl.height = int(xl.height * ratio)
                    ws.row_dimensions[g_row].height = int(xl.height * 0.75) + 8
                    ic = ws.cell(row=g_row, column=2, value="")
                    ic.fill = _f("F0F9FF")
                    s = Side(style="medium", color=TEAL)
                    ic.border = Border(left=s, right=s, top=s, bottom=s)
                    ws.add_image(xl, f"B{g_row}")
                except Exception as e:
                    logger.warning(f"Gallery image error: {e}")
            g_row += 2

    if g_row == 4:
        ws.merge_cells("A4:C4")
        ws["A4"] = "No images attached yet."
        ws["A4"].font = Font(italic=True, size=10, color=GRAY, name="Calibri")
        ws["A4"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[4].height = 30
    return anchors

def _create_call_log_sheet(wb, calls, image_anchors=None):
    if image_anchors is None:
        image_anchors = {}
    try:
        from openpyxl.drawing.image import Image as XLImage
        can_embed = True
    except ImportError:
        can_embed = False

    ws = wb.create_sheet("📋 Call History", 1)
    ws.sheet_view.showGridLines = False

    # A=spacer B=lbl C=val D=lbl E=val F=lbl G=val H=lbl I=val J=spacer
    for i, w in enumerate([1.2, 16, 26, 16, 26, 16, 26, 16, 26, 1.2], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    def sc(row, col, val="", bg="FFFFFF", fg=NAVY, bold=False, sz=9, h="left", v="center", wrap=False, bdr=True):
        c = ws.cell(row=row, column=col, value=val)
        c.font = Font(bold=bold, size=sz, color=fg, name="Calibri")
        c.fill = _f(bg)
        c.alignment = Alignment(horizontal=h, vertical=v, wrap_text=wrap)
        if bdr: c.border = _b()
        return c

    def mc(row, c1, c2, val="", bg="FFFFFF", fg=NAVY, bold=False, sz=9, h="left", v="center", wrap=False):
        ws.merge_cells(f"{get_column_letter(c1)}{row}:{get_column_letter(c2)}{row}")
        return sc(row, c1, val, bg, fg, bold, sz, h, v, wrap)

    def lbl(row, col, txt):
        sc(row, col, txt, bg="F1F5F9", fg="64748B", bold=True, sz=8, h="right")

    # Title
    mc(1,1,10,"   🍽️  Intelligence Engine v2.0  —  Call History", bg=NAVY, fg="FFFFFF", bold=True, sz=14)
    ws.row_dimensions[1].height = 36
    mc(2,1,10, f"   Generated {datetime.now().strftime('%d %b %Y  %H:%M')}   ·   {len(calls)} call(s)   ·   Confidential", bg="1E293B", fg="94A3B8", sz=8)
    ws.row_dimensions[2].height = 14
    mc(3,1,10,"   💡  Tip: Click '📸 View Full Size' next to any image to open the Image Gallery sheet.", bg="EFF6FF", fg="0369A1", sz=9)
    ws.row_dimensions[3].height = 16

    sorted_calls = sorted(calls, key=lambda x: datetime.strptime(x.get("call_date","1900-01-01"),"%Y-%m-%d"), reverse=True)
    o_cfg = {"won":("DCFCE7","166534"),"lost":("FEE2E2","991B1B"),"pending":("FEF9C3","854D0E")}
    i_cfg = {"hi":("D1FAE5","065F46"),"mid":("FEF3C7","92400E"),"lo":("FEE2E2","991B1B")}
    R = 5

    for call in sorted_calls:
        interest = call.get("interest_level", 0)
        outcome = call.get("outcome","Pending").lower()
        rest_id = call.get("restaurant_id","")
        call_date = call.get("call_date","—")
        rest_name = call.get("restaurant_name","—")
        o_bg,o_fg = o_cfg.get(outcome,("FEF9C3","854D0E"))
        ik = "hi" if interest>=4 else ("mid" if interest>=2 else "lo")
        i_bg,i_fg = i_cfg[ik]
        stars = "★"*int(interest)+"☆"*(5-int(interest))

        # Card header — teal bar
        mc(R,1,10, f"   📞  {rest_name}   ·   {call_date}", bg=TEAL, fg="FFFFFF", bold=True, sz=11)
        ws.row_dimensions[R].height = 26; R+=1

        # Row 1: Contact | Outcome | Interest | Confidence
        lbl(R,2,"Contact");    sc(R,3, call.get("contact_name","—") or "—")
        lbl(R,4,"Outcome");    sc(R,5, call.get("outcome","Pending"), bg=o_bg, fg=o_fg, bold=True, h="center")
        lbl(R,6,"Interest");   sc(R,7, f"{stars}  {interest}/5", bg=i_bg, fg=i_fg, bold=True)
        lbl(R,8,"Confidence"); sc(R,9, f"{call.get('confidence_level','—')}%", h="center")
        ws.row_dimensions[R].height = 20; R+=1

        # Row 2: Budget | Timeline | Competitor | Follow-up
        lbl(R,2,"Budget");     sc(R,3, call.get("budget_range","—") or "—")
        lbl(R,4,"Timeline");   sc(R,5, call.get("decision_timeline","—") or "—")
        lbl(R,6,"Competitor"); sc(R,7, call.get("competitor_tools","—") or "—")
        lbl(R,8,"Follow-up");  sc(R,9, call.get("follow_up_date","—") or "—")
        ws.row_dimensions[R].height = 20; R+=1

        # Row 3: Products (full width)
        lbl(R,2,"Products")
        mc(R,3,9, ", ".join(call.get("products_discussed",[])) or "—", wrap=True)
        ws.row_dimensions[R].height = 20; R+=1

        # Row 4: Objection | Next Steps
        lbl(R,2,"Objection"); mc(R,3,5, call.get("main_objection","—") or "—", wrap=True)
        lbl(R,6,"Next Steps"); mc(R,7,9, call.get("next_steps","—") or "—", wrap=True)
        ws.row_dimensions[R].height = 20; R+=1

        # Row 5: Notes — full width, tall, warm bg
        lbl(R,2,"Notes")
        nc = mc(R,3,9, call.get("notes","") or "—", bg="FFFBEB", fg="44403C", sz=9, wrap=True, v="top")
        nc.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
        ws.row_dimensions[R].height = 60; R+=1

        # Images
        call_images = call.get("images",[])
        if call_images:
            mc(R,2,9, f"  📸  Attached Images  ({len(call_images)} file{'s' if len(call_images)!=1 else ''})", bg="CFFAFE", fg=TEAL, bold=True, sz=9)
            ws.row_dimensions[R].height = 16; R+=1

            THUMB_W,THUMB_H = 90,68
            ROW_PTS = int(THUMB_H*0.75)+6

            for img_idx, img_data in enumerate(call_images):
                col_th = 2+(img_idx%4)*2
                lbl_c = ws.cell(row=R, column=col_th, value=f"🖼  {img_data.get('filename','img')}")
                lbl_c.font = Font(bold=True, size=8, color="334155", name="Calibri")
                lbl_c.fill = _f("F1F5F9"); lbl_c.alignment = Alignment(horizontal="left", vertical="center"); lbl_c.border = _b()
                gallery_row = image_anchors.get((rest_id, call_date, img_idx), 4)
                lnk = ws.cell(row=R, column=col_th+1, value="📸 View Full Size ↗")
                lnk.font = Font(bold=True, size=8, color="0369A1", underline="single", name="Calibri")
                lnk.fill = _f("DBEAFE"); lnk.alignment = Alignment(horizontal="center", vertical="center"); lnk.border = _b()
                lnk.hyperlink = f"#'📸 Images'!A{gallery_row}"
            ws.row_dimensions[R].height = 14; R+=1

            ws.row_dimensions[R].height = ROW_PTS
            for img_idx, img_data in enumerate(call_images):
                col_th = 2+(img_idx%4)*2
                tc = ws.cell(row=R, column=col_th, value="")
                tc.fill = _f("F0F9FF")
                s = Side(style="thin", color=TEAL); tc.border = Border(left=s,right=s,top=s,bottom=s)
                if can_embed:
                    try:
                        xl = XLImage(io.BytesIO(base64.b64decode(img_data.get("data",""))))
                        rat = min(THUMB_W/max(xl.width,1), THUMB_H/max(xl.height,1))
                        xl.width=int(xl.width*rat); xl.height=int(xl.height*rat)
                        ws.add_image(xl, f"{get_column_letter(col_th)}{R}")
                    except Exception as e:
                        logger.warning(f"Thumb error: {e}")
            R+=1

        # Separator
        for ci in range(1,11):
            ws.cell(row=R, column=ci).fill = _f(TEAL)
        ws.row_dimensions[R].height = 4; R+=2

    ws.freeze_panes = "A5"

def _create_pipeline_sheet(wb, calls, restaurant_data):
    ws = wb.create_sheet("📊 Pipeline Summary", 2)
    ws.sheet_view.showGridLines = False
    _section_title(ws,"A1","  📊  Sales Pipeline Summary", merge_to="D1")
    ws.merge_cells("A2:D2"); ws["A2"] = f"Exported {datetime.now().strftime('%d %b %Y')}"
    ws["A2"].font = Font(size=8,color="94A3B8",name="Calibri"); ws["A2"].fill = _f("1E293B")
    ws["A2"].alignment = Alignment(horizontal="center"); ws.row_dimensions[1].height=26; ws.row_dimensions[2].height=14
    ws["A4"] = "Key Performance Indicators"; ws["A4"].font = Font(bold=True,size=11,color=NAVY,name="Calibri")
    kpis = [
        ("Total Restaurants with Calls", len(restaurant_data)),
        ("Total Calls Logged", len(calls)),
        ("Average Interest Level", round(sum(c.get("interest_level",0) for c in calls)/max(len(calls),1),1)),
        ("High Interest Calls (4-5)", len([c for c in calls if c.get("interest_level",0)>=4])),
        ("Medium Interest Calls (2-3)", len([c for c in calls if 2<=c.get("interest_level",0)<4])),
        ("Low Interest Calls (1)", len([c for c in calls if c.get("interest_level",0)==1])),
        ("Deals Won", len([c for c in calls if c.get("outcome","").lower()=="won"])),
        ("Deals Lost", len([c for c in calls if c.get("outcome","").lower()=="lost"])),
        ("Deals Pending", len([c for c in calls if c.get("outcome","Pending").lower()=="pending"])),
        ("Calls with Images Attached", len([c for c in calls if c.get("images")])),
    ]
    kpi_colors = {"High Interest Calls (4-5)":("DCFCE7","166534"),"Deals Won":("DCFCE7","166534"),"Deals Lost":("FEE2E2","991B1B"),"Low Interest Calls (1)":("FEE2E2","991B1B"),"Calls with Images Attached":(LIGHT,TEAL)}
    row=5
    for label,value in kpis:
        bg,fg = kpi_colors.get(label,("F1F5F9",NAVY))
        for ci,(col,val) in enumerate(zip(["A","B"],[label,value]),1):
            cell=ws[f"{col}{row}"]; cell.value=val
            cell.font=Font(bold=(ci==1),size=10,color=fg,name="Calibri"); cell.fill=_f(bg)
            cell.alignment=Alignment(horizontal="center" if ci==2 else "left",vertical="center"); cell.border=_b()
        ws.row_dimensions[row].height=18; row+=1
    row+=1
    ws.merge_cells(f"A{row}:D{row}"); ws[f"A{row}"]="  Outcome Distribution"
    ws[f"A{row}"].font=Font(bold=True,size=11,color="FFFFFF",name="Calibri"); ws[f"A{row}"].fill=_f(TEAL2)
    ws[f"A{row}"].alignment=Alignment(horizontal="left",vertical="center"); ws.row_dimensions[row].height=20; row+=1
    for ol,bg,fg in [("Won","DCFCE7","166534"),("Lost","FEE2E2","991B1B"),("Pending","FEF3C7","92400E")]:
        cnt=len([c for c in calls if c.get("outcome","Pending")==ol]); rate=f"{cnt/max(len(calls),1)*100:.1f}%"
        for ci,val in enumerate([ol,cnt,rate],1):
            cell=ws.cell(row=row,column=ci,value=val); cell.fill=_f(bg)
            cell.font=Font(bold=(ci==1),color=fg,size=10,name="Calibri")
            cell.alignment=Alignment(horizontal="left" if ci==1 else "center",vertical="center"); cell.border=_b()
        ws.row_dimensions[row].height=18; row+=1
    row+=1
    ws.merge_cells(f"A{row}:D{row}"); ws[f"A{row}"]="  Product Frequency"
    ws[f"A{row}"].font=Font(bold=True,size=11,color="FFFFFF",name="Calibri"); ws[f"A{row}"].fill=_f(TEAL)
    ws[f"A{row}"].alignment=Alignment(horizontal="left",vertical="center"); ws.row_dimensions[row].height=20; row+=1
    for col_ltr,hdr in zip(["A","B"],["Product Name","Times Discussed"]):
        cell=ws[f"{col_ltr}{row}"]; cell.value=hdr
        cell.font=Font(bold=True,color="FFFFFF",size=10,name="Calibri"); cell.fill=_f("475569")
        cell.alignment=Alignment(horizontal="center" if col_ltr=="B" else "left",vertical="center"); cell.border=_b()
    ws.row_dimensions[row].height=18; row+=1
    pc={}
    for call in calls:
        for p in call.get("products_discussed",[]): pc[p]=pc.get(p,0)+1
    for p,cnt in sorted(pc.items(),key=lambda x:x[1],reverse=True):
        ws[f"A{row}"].value=p; ws[f"A{row}"].font=Font(size=9,name="Calibri"); ws[f"A{row}"].fill=_f("F0F9FF"); ws[f"A{row}"].border=_b()
        ws[f"B{row}"].value=cnt; ws[f"B{row}"].font=Font(bold=True,size=9,color=TEAL,name="Calibri"); ws[f"B{row}"].fill=_f("F0F9FF"); ws[f"B{row}"].alignment=Alignment(horizontal="center"); ws[f"B{row}"].border=_b()
        ws.row_dimensions[row].height=16; row+=1
    ws.column_dimensions["A"].width=38; ws.column_dimensions["B"].width=20; ws.column_dimensions["C"].width=16; ws.column_dimensions["D"].width=16

def _create_product_sheet(wb, calls):
    ws = wb.create_sheet("🛒 Product Analytics", 3)
    ws.sheet_view.showGridLines = False
    _section_title(ws,"A1","  🛒  Product Analytics & Correlation",merge_to="D1"); ws.row_dimensions[1].height=26
    for ci,h in enumerate(["Product","Times Discussed","Avg Interest","Close Rate Estimate"],1):
        cell=ws.cell(row=3,column=ci,value=h); _header_style(cell,bg=TEAL)
    ws.row_dimensions[3].height=22
    products=set()
    for call in calls: products.update(call.get("products_discussed",[]))
    row=4
    for product in sorted(products):
        pc=[c for c in calls if product in c.get("products_discussed",[])]
        times=len(pc); avg=sum(c.get("interest_level",0) for c in pc)/max(times,1)
        cr=len([c for c in pc if c.get("interest_level",0)>=4])/max(times,1)*100
        bg="F0F9FF" if row%2==0 else "FFFFFF"
        for ci,val in enumerate([product,times,round(avg,1),f"{cr:.0f}%"],1):
            cell=ws.cell(row=row,column=ci,value=val); cell.font=Font(size=9,name="Calibri")
            cell.fill=_f(bg); cell.alignment=Alignment(horizontal="left" if ci==1 else "center",vertical="center"); cell.border=_b()
            if ci==4:
                cb="DCFCE7" if cr>=60 else ("FEF3C7" if cr>=30 else "FEE2E2")
                cf="166534" if cr>=60 else ("92400E" if cr>=30 else "991B1B")
                cell.fill=_f(cb); cell.font=Font(bold=True,color=cf,size=9,name="Calibri")
        ws.row_dimensions[row].height=18; row+=1
    ws.column_dimensions["A"].width=38; ws.column_dimensions["B"].width=18; ws.column_dimensions["C"].width=26; ws.column_dimensions["D"].width=20

def _create_action_items_sheet(wb, calls):
    ws = wb.create_sheet("⚡ Action Items", 4)
    ws.sheet_view.showGridLines = False
    _section_title(ws,"A1","  ⚡  Upcoming & Overdue Follow-ups",merge_to="F1"); ws.row_dimensions[1].height=26
    for ci,(h,w) in enumerate(zip(["Restaurant","Last Call Date","Contact","Next Steps","Days Until Due","Status"],[26,14,20,32,16,14]),1):
        cell=ws.cell(row=3,column=ci,value=h); _header_style(cell,bg=TEAL); ws.column_dimensions[get_column_letter(ci)].width=w
    ws.row_dimensions[3].height=22
    rc={}
    for call in calls: rc.setdefault(call.get("restaurant_name","Unknown"),[]).append(call)
    for rest in rc: rc[rest]=sorted(rc[rest],key=lambda x:datetime.strptime(x.get("call_date","1900-01-01"),"%Y-%m-%d"),reverse=True)
    today=datetime.now(); row=4
    for rest,call_list in sorted(rc.items()):
        if not call_list: continue
        lc=call_list[0]; cd=datetime.strptime(lc.get("call_date",today.strftime("%Y-%m-%d")),"%Y-%m-%d")
        due=(cd+timedelta(days=7)-today).days
        status="OVERDUE" if due<0 else ("URGENT" if due<=2 else "PENDING")
        sbg="FEE2E2" if status=="OVERDUE" else ("FEF3C7" if status=="URGENT" else "DCFCE7")
        sfg="991B1B" if status=="OVERDUE" else ("92400E" if status=="URGENT" else "166534")
        rb="F8FAFC" if row%2==0 else "FFFFFF"
        for ci,val in enumerate([rest,lc.get("call_date","—"),lc.get("contact_name","—"),(lc.get("next_steps","") or "")[:60],max(0,due),status],1):
            cell=ws.cell(row=row,column=ci,value=val); cell.border=_b()
            cell.alignment=Alignment(wrap_text=True,vertical="center",horizontal="left" if ci in(1,3,4) else "center")
            if ci==6: cell.fill=_f(sbg); cell.font=Font(bold=True,color=sfg,size=9,name="Calibri")
            else: cell.fill=_f(rb); cell.font=Font(size=9,name="Calibri")
        ws.row_dimensions[row].height=18; row+=1
    ws.freeze_panes="A4"