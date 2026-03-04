"""
report_generator.py
====================
Generates a rich 6-page Revenue Intelligence Brief PDF using reportlab + matplotlib.
Restaurant version — adapted from praxiotech-intelligence-engine.
"""
import io
from datetime import datetime

# Defer importing heavy plotting libraries (matplotlib, numpy) until they
# are actually needed in the plotting helper functions. This prevents
# import-time failures when these optional libraries are not installed.

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ── Brand palette ─────────────────────────────────────────────────────────────────
CN   = HexColor('#0F172A')
CB   = HexColor('#0EA5E9')
CT   = HexColor('#14B8A6')
CG   = HexColor('#22C55E')
CR   = HexColor('#EF4444')
CA   = HexColor('#F59E0B')
CSl  = HexColor('#64748B')
CLt  = HexColor('#F8FAFC')
CBd  = HexColor('#E2E8F0')
CPu  = HexColor('#A855F7')
CDB  = HexColor('#1E3A5F')
COFF = HexColor('#FFFBEB')
CBI  = HexColor('#EFF6FF')
W, H = A4


def S(name, **kw):
    defaults = dict(fontName='Helvetica', fontSize=10, textColor=CN, leading=14, spaceAfter=2*mm)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


STYLES = {
    'H1':    S('H1',  fontName='Helvetica-Bold', fontSize=20, textColor=CN, spaceAfter=3*mm),
    'H2':    S('H2',  fontName='Helvetica-Bold', fontSize=13, textColor=CN, spaceAfter=2*mm, spaceBefore=3*mm),
    'Body':  S('Body', fontSize=10, leading=15, spaceAfter=2*mm, alignment=TA_JUSTIFY),
    'Small': S('Small', fontSize=8.5, textColor=CSl, leading=12),
    'TH':    S('TH',  fontName='Helvetica-Bold', fontSize=8.5, textColor=white, alignment=TA_CENTER),
    'TC':    S('TC',  fontSize=9, textColor=CN, alignment=TA_CENTER),
    'TL':    S('TL',  fontSize=9, textColor=CN),
    'KPIL':  S('KPIL', fontName='Helvetica-Bold', fontSize=7.5, textColor=CSl, alignment=TA_CENTER),
    'KPIV':  S('KPIV', fontName='Helvetica-Bold', fontSize=20, textColor=CB, alignment=TA_CENTER),
    'Note':  S('Note', fontSize=8, textColor=CSl, leading=11, alignment=TA_JUSTIFY),
}


# ── Public entry ──────────────────────────────────────────────────────────────────
def generate_pdf_report(res_name, res_data, scores, gaps, momentum_data,
                        persona, benchmarks, df_rest, df_rev, rank, total, language="EN"):
    """
    Generate a PDF report with language support.

    Args:
        language: "EN" for English or "DE" for German (default: "EN")
    """
    # Import translations
    from translations import t

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=16*mm, leftMargin=16*mm,
        topMargin=14*mm,   bottomMargin=14*mm,
        title=f"Revenue Intelligence Brief – {res_name}",
        author="Praxiotech Restaurant Intelligence Engine v2.0"
    )
    story = []
    story += _cover(res_name, res_data, scores, rank, total, language)
    story.append(PageBreak())
    story += _exec_summary(res_name, res_data, scores, gaps, rank, total, persona, benchmarks, language)
    story.append(PageBreak())
    story += _dimension_page(res_name, scores, benchmarks, language)
    story.append(PageBreak())
    story += _gap_page(res_name, scores, gaps, benchmarks, rank, total, language)
    story.append(PageBreak())
    story += _momentum_page(res_name, res_data, scores, momentum_data, df_rest, df_rev, language)
    story.append(PageBreak())
    story += _action_page(res_name, scores, gaps, persona, language)

    doc.build(story, onFirstPage=_chrome, onLaterPages=_chrome)
    buf.seek(0)
    return buf.read()


def _chrome(canvas, doc):
    canvas.saveState()
    pg = canvas.getPageNumber()
    if pg == 1:
        canvas.setFillColor(CN)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.setFillColor(CB)
        canvas.rect(0, H-8, W, 8, fill=1, stroke=0)
        canvas.setFillColor(CDB)
        canvas.rect(0, 0, W, 55, fill=1, stroke=0)
    else:
        canvas.setFillColor(CN)
        canvas.rect(0, H-11, W, 11, fill=1, stroke=0)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(white)
        canvas.drawString(16*mm, H-7.5, "RESTAURANT REVENUE INTELLIGENCE  |  PRAXIOTECH")
        canvas.drawRightString(W-16*mm, H-7.5, f"CONFIDENTIAL  ·  PAGE {pg} OF 6")
        canvas.setFillColor(CBd)
        canvas.rect(0, 0, W, 12, fill=1, stroke=0)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CSl)
        canvas.drawString(16*mm, 4, f"Generated: {datetime.now().strftime('%d %b %Y')}  ·  Intelligence Engine v1.3  ·  Restaurant Audit")
        canvas.drawRightString(W-16*mm, 4, "For Internal Sales Use Only  ·  © Praxiotech GmbH")
    canvas.restoreState()


def _cover(res_name, res_data, scores, rank, total, language="EN"):
    from translations import t
    story = [Spacer(1, 35*mm)]
    badge = Table([[f"  {t('pdf_intelligence_engine', language)}  "]])
    badge.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CB), ('TEXTCOLOR',(0,0),(-1,-1),white),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,-1),8),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(badge)
    story.append(Spacer(1, 7*mm))
    for txt_key, clr, sz in [(t("pdf_restaurant", language), white, 44), (t("pdf_revenue", language), CB, 44), (t("pdf_intelligence", language), white, 44)]:
        story.append(Paragraph(txt_key, S('CT', fontName='Helvetica-Bold', fontSize=sz, textColor=clr, leading=48, spaceAfter=0)))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=CDB, spaceAfter=4*mm))
    story.append(Paragraph(res_name, S('CRN', fontName='Helvetica-Bold', fontSize=22, textColor=HexColor('#94A3B8'), spaceAfter=2*mm)))
    story.append(Paragraph(
        t('pdf_ranked', language, rank=rank, total=total) + f"  ·  {datetime.now().strftime('%B %Y')}",
        S('CRM', fontSize=11, textColor=HexColor('#475569'), spaceAfter=10*mm)
    ))
    h = scores['Composite']
    kd = [
        [t("pdf_health_score", language), t("pdf_district_rank", language), t("pdf_star_rating", language), t("pdf_responsiveness", language)],
        [f"{h:.1f}/100", f"#{rank}/{total}", f"{float(res_data.get('rating_n',0)):.1f} ★", f"{scores['Responsiveness']:.0f}%"]
    ]
    kt = Table(kd, colWidths=[44*mm]*4)
    kt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),HexColor('#1E293B')), ('BACKGROUND',(0,1),(-1,1),HexColor('#0F172A')),
        ('TEXTCOLOR',(0,0),(-1,0),HexColor('#64748B')), ('TEXTCOLOR',(0,1),(-1,1),CB),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'), ('FONTNAME',(0,1),(-1,1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),7), ('FONTSIZE',(0,1),(-1,1),18),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),10), ('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LINEABOVE',(0,0),(-1,0),2,CB),
        ('LINEBEFORE',(1,0),(1,-1),0.5,HexColor('#1E3A5F')),
        ('LINEBEFORE',(2,0),(2,-1),0.5,HexColor('#1E3A5F')),
        ('LINEBEFORE',(3,0),(3,-1),0.5,HexColor('#1E3A5F')),
    ]))
    story.append(kt)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(t("pdf_confidential", language),
                            S('CF', fontSize=9, textColor=HexColor('#475569'))))
    return story


def _exec_summary(res_name, res_data, scores, gaps, rank, total, persona, benchmarks, language="EN"):
    from translations import t
    story = [Spacer(1, 5*mm)]
    story.append(Paragraph(t("pdf_exec_summary", language), STYLES['H1']))
    story.append(HRFlowable(width='100%', thickness=2, color=CB, spaceAfter=3*mm))

    rating    = float(res_data.get('rating_n', 0) or 0)
    rev_count = int(res_data.get('rev_count_n', 0) or 0)
    res_rate  = float(res_data.get('res_rate', 0) or 0)
    health    = scores['Composite']

    story.append(Paragraph(
        f"This Revenue Intelligence Brief presents a comprehensive digital audit of <b>{res_name}</b>, "
        f"currently ranked <b>#{rank} of {total}</b> in the Praxiotech Intelligence Index. "
        f"The restaurant holds a <b>Digital Health Score of {health:.1f}/100</b>, "
        f"built on a {rating:.1f}-star Google rating across {rev_count:,} customer reviews. "
        f"While the establishment demonstrates strong guest satisfaction metrics, "
        f"this audit identifies critical optimization gaps — most notably in owner responsiveness "
        f"(<b>{res_rate*100:.0f}%</b> current vs. 90% industry best practice) — "
        f"that represent immediate, high-ROI opportunities for the Praxiotech platform.",
        STYLES['Body']))

    top_gap = max(gaps, key=gaps.get) if gaps else 'Responsiveness'
    top_val = gaps.get(top_gap, 0)
    callout = Table([[Paragraph(
        f"<b>Primary Finding:</b> The largest gap is in <b>{top_gap}</b> ({top_val:+.1f} pts vs. benchmark). "
        f"Closing this single gap via Praxiotech would move {res_name} into the <b>Top 3</b>.",
        S('CB', fontSize=10, textColor=CN, leading=14))]], colWidths=[175*mm])
    callout.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CBI), ('LINEABOVE',(0,0),(-1,-1),3,CB),
        ('LINEBEFORE',(0,0),(-1,-1),3,CB),
        ('TOPPADDING',(0,0),(-1,-1),9), ('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),10), ('RIGHTPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(callout)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Performance Scorecard", STYLES['H2']))
    bench_map = {
        'Reputation':       benchmarks.get('rating', 4.4)*20,
        'Responsiveness':   90.0,
        'Digital Presence': 85.0,
        'Intelligence':     75.0,
        'Visibility':       70.0,
        'COMPOSITE':        75.0,
    }
    dims = ['Reputation','Responsiveness','Digital Presence','Intelligence','Visibility','COMPOSITE']
    wts  = ['30%','25%','20%','15%','10%','—']
    vals = [scores[d if d != 'COMPOSITE' else 'Composite'] for d in dims]

    hrow = [Paragraph(text, STYLES['TH']) for text in [t('pdf_dimension', language), 'Weight', t('pdf_score', language) + ' /100', t('pdf_benchmark', language), 'Delta', t('pdf_status', language)]]
    rows = [hrow]
    for i, dim in enumerate(dims):
        sc = vals[i]; bv = bench_map[dim]; dt = sc - bv
        ds = f"+{dt:.1f}" if dt >= 0 else f"{dt:.1f}"
        dc = CG if dt >= 0 else CR
        st = 'STRENGTH' if dt >= 0 else ('OPPORTUNITY' if dt > -15 else 'CRITICAL')
        bold = dim == 'COMPOSITE'
        fn   = 'Helvetica-Bold' if bold else 'Helvetica'
        rows.append([
            Paragraph(f"<b>{dim}</b>" if bold else dim, S('td',fontName=fn,fontSize=9,textColor=CN)),
            Paragraph(wts[i], S('tdC',fontName=fn,fontSize=9,textColor=CSl,alignment=TA_CENTER)),
            Paragraph(f"<b>{sc:.1f}</b>", S('tdSc',fontName='Helvetica-Bold',fontSize=11,textColor=CB,alignment=TA_CENTER)),
            Paragraph(f"{bv:.0f}", S('tdB',fontSize=9,textColor=CSl,alignment=TA_CENTER)),
            Paragraph(f"<b>{ds}</b>", S('tdD',fontName='Helvetica-Bold',fontSize=9,textColor=dc,alignment=TA_CENTER)),
            Paragraph(f"<b>{st}</b>",  S('tdSt',fontName='Helvetica-Bold',fontSize=8,textColor=white,alignment=TA_CENTER)),
        ])

    st_styles = []
    for i, dim in enumerate(dims):
        sc = vals[i]; bv = bench_map[dim]; dt = sc-bv
        bg = CG if dt >= 0 else (CA if dt > -15 else CR)
        st_styles.append(('BACKGROUND',(5,i+1),(5,i+1),bg))

    sc_table = Table(rows, colWidths=[52*mm,18*mm,24*mm,26*mm,20*mm,25*mm], repeatRows=1)
    sc_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),CN), ('FONTSIZE',(0,0),(-1,0),8.5),
        ('ALIGN',(0,0),(-1,-1),'LEFT'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[white,CLt]),
        ('BACKGROUND',(0,6),(-1,6),HexColor('#EFF6FF')),
        ('LINEABOVE',(0,6),(-1,6),1.5,CB),
        ('LINEBELOW',(0,0),(-1,-1),0.4,CBd),
        ('BOX',(0,0),(-1,-1),0.5,CBd),
    ] + st_styles))
    story.append(sc_table)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Customer Persona Intelligence", STYLES['H2']))
    p = persona
    pt = Table([
        [Paragraph(f"<b>Primary Persona:</b> {p['primary']}", STYLES['Body']),
         Paragraph(f"<b>Segment:</b> {p['segment']}", STYLES['Body'])],
        [Paragraph(f"<b>Core Motivation:</b> {p['motivation']}", STYLES['Body']), ""],
    ], colWidths=[87*mm, 88*mm])
    pt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CLt), ('LINEABOVE',(0,0),(-1,0),2,CT),
        ('SPAN',(0,1),(-1,1)),
        ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9),
        ('LINEBELOW',(0,-1),(-1,-1),0.5,CBd),
    ]))
    story.append(pt)
    return story


def _dimension_page(res_name, scores, benchmarks, language="EN"):
    from translations import t
    story = [Spacer(1, 5*mm)]
    story.append(Paragraph(t("pdf_dimension_analysis", language), STYLES['H1']))
    story.append(HRFlowable(width='100%', thickness=2, color=CT, spaceAfter=3*mm))
    story.append(Paragraph(
        "Each of the five performance dimensions is independently scored (0–100), weighted by business impact, "
        "and benchmarked against the top 25th percentile of all establishments in the dataset. "
        "<b>Green bars</b> = above benchmark. <b>Red bars</b> = gap opportunity for Praxiotech.",
        STYLES['Body']))

    dims     = ['Reputation','Responsiveness','Digital\nPresence','Intelligence','Visibility']
    sc_vals  = [scores['Reputation'], scores['Responsiveness'], scores['Digital Presence'], scores['Intelligence'], scores['Visibility']]
    bm_vals  = [benchmarks.get('rating',4.4)*20, 90, 85, 75, 70]
    bar_clrs = ['#22C55E' if sc_vals[i] >= bm_vals[i] else '#EF4444' for i in range(5)]

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(7.2, 2.9))
        x = np.arange(5); w = 0.36
        b1 = ax.bar(x - w/2, sc_vals, w, color=bar_clrs, zorder=3, label='Score')
        ax.bar(x + w/2, bm_vals, w, color='#CBD5E1', zorder=3, label='Benchmark')
        ax.set_xticks(x); ax.set_xticklabels(dims, fontsize=9)
        ax.set_ylim(0, 115); ax.set_ylabel('Score', fontsize=9)
        ax.set_facecolor('#F8FAFC'); fig.patch.set_facecolor('#FFFFFF')
        ax.yaxis.grid(True, color='#E2E8F0', linewidth=0.6, zorder=0); ax.set_axisbelow(True)
        for spine in ax.spines.values(): spine.set_color('#E2E8F0')
        for bar, v in zip(b1, sc_vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5, f"{v:.0f}",
                    ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#0F172A')
        ax.legend(loc='upper right', fontsize=8, framealpha=0.8)
        plt.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format='PNG', dpi=140, bbox_inches='tight'); plt.close(fig); buf.seek(0)
        story.append(RLImage(buf, width=168*mm, height=68*mm))
    except Exception:
        story.append(Paragraph(
            "Plots unavailable — `matplotlib`/`numpy` not installed. To enable plots, install: pip install matplotlib numpy",
            STYLES['Note']))
    story.append(Spacer(1, 4*mm))

    dim_details = [
        ('Reputation (30%)',       scores['Reputation'],       benchmarks.get('rating',4.4)*20,
         'Combines star rating quality (70%) and review volume social proof (30%). High-volume restaurants dominate local search.',
         'Maintain 4.5+ star avg. Target 500+ reviews. Use post-visit follow-up automation.'),
        ('Responsiveness (25%)',   scores['Responsiveness'],   90,
         '% of customer reviews receiving an owner reply. 89% of diners read owner responses before booking.',
         'Target 90%+ response rate. Deploy Praxiotech AI Review Manager for 2-hour guaranteed replies.'),
        ('Digital Presence (20%)', scores['Digital Presence'], 85,
         'Website, phone contact, and booking infrastructure. Complete profiles convert 3x more Google Maps viewers.',
         'Verify Google Business Profile. Add booking link. Refresh photos quarterly.'),
        ('Intelligence (15%)',     scores['Intelligence'],     75,
         'Sentiment derived from review rating patterns, identifying emotional triggers that drive repeat visits.',
         'Monitor sentiment weekly. Address recurring negative themes within 30 days.'),
        ('Visibility (10%)',       scores['Visibility'],       70,
         'Recency-weighted review velocity. Fresh reviews within 90 days heavily influence Google Maps ranking.',
         'Launch SMS post-visit campaign. Target 3-5 new reviews per week.'),
    ]

    for name, sc, bv, what, action in dim_details:
        dt = sc - bv
        bg = HexColor('#DCFCE7') if dt >= 0 else (HexColor('#FEF3C7') if dt > -15 else HexColor('#FEE2E2'))
        tc = CG if dt >= 0 else (CA if dt > -15 else CR)
        st = 'STRENGTH' if dt >= 0 else ('OPPORTUNITY' if dt > -15 else 'CRITICAL GAP')
        card = Table([
            [Paragraph(f"<b>{name}</b>", S('dh',fontName='Helvetica-Bold',fontSize=10,textColor=CN)),
             Paragraph(f"<b>{sc:.1f} / 100</b>", S('dsv',fontName='Helvetica-Bold',fontSize=12,textColor=CB,alignment=TA_RIGHT)),
             Paragraph(f"<b>{st}</b>", S('dst',fontName='Helvetica-Bold',fontSize=8,textColor=tc,alignment=TA_CENTER))],
            [Paragraph(f"<b>What it measures:</b> {what}", STYLES['Small']), '', ''],
            [Paragraph(f"<b>Recommended action:</b> {action}", S('act',fontSize=8.5,textColor=HexColor('#0369A1'),leading=12)), '', ''],
        ], colWidths=[88*mm, 42*mm, 45*mm])
        card.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),HexColor('#F8FAFC')), ('BACKGROUND',(2,0),(2,0),bg),
            ('BACKGROUND',(0,2),(-1,2),HexColor('#F0F9FF')),
            ('SPAN',(0,1),(-1,1)), ('SPAN',(0,2),(-1,2)),
            ('LINEABOVE',(0,0),(-1,0),2,tc), ('BOX',(0,0),(-1,-1),0.5,CBd),
            ('LINEBELOW',(0,0),(-1,-1),0.4,CBd), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),7), ('RIGHTPADDING',(0,0),(-1,-1),7),
        ]))
        story.append(card); story.append(Spacer(1, 2*mm))
    return story


def _gap_page(res_name, scores, gaps, benchmarks, rank, total, language="EN"):
    from translations import t
    story = [Spacer(1, 5*mm)]
    story.append(Paragraph(t("pdf_gap_analysis", language), STYLES['H1']))
    story.append(HRFlowable(width='100%', thickness=2, color=CA, spaceAfter=3*mm))
    story.append(Paragraph(
        f"Gap analysis compares {res_name}'s performance against the market benchmark "
        f"(top 25th percentile of {total} establishments). "
        "Positive delta = underperforming (Praxiotech opportunity). Negative = market advantage to defend.",
        STYLES['Body']))

    dims = ['Reputation','Responsiveness','Digital Presence','Intelligence','Visibility']
    sc_list = [scores[d] for d in dims]
    bm_list = [benchmarks.get('rating',4.4)*20, 90, 85, 75, 70]

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(7.2, 2.8))
        y = np.arange(len(dims))
        clrs = ['#22C55E' if sc_list[i] >= bm_list[i] else '#EF4444' for i in range(len(dims))]
        bars = ax.barh(y, sc_list, color=clrs, height=0.45, zorder=3)
        ax.barh(y, bm_list, color='#CBD5E1', height=0.45, alpha=0.35, zorder=2, label='Benchmark')
        ax.set_yticks(y); ax.set_yticklabels(['Reputation','Responsiveness','Digital Pres.','Intelligence','Visibility'], fontsize=9)
        ax.set_xlim(0, 110); ax.set_xlabel('Score', fontsize=9)
        ax.set_facecolor('#F8FAFC'); fig.patch.set_facecolor('#FFFFFF')
        ax.xaxis.grid(True, color='#E2E8F0', linewidth=0.6, zorder=0); ax.set_axisbelow(True)
        for spine in ax.spines.values(): spine.set_color('#E2E8F0')
        for bar, sc in zip(bars, sc_list):
            ax.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2, f"{sc:.0f}", va='center', fontsize=8.5, fontweight='bold', color='#0F172A')
        for i, bv in enumerate(bm_list):
            ax.vlines(bv, i-0.3, i+0.3, colors='#0F172A', linewidth=1.8, zorder=4)
        ax.legend(fontsize=8, framealpha=0.8)
        plt.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format='PNG', dpi=140, bbox_inches='tight'); plt.close(fig); buf.seek(0)
        story.append(RLImage(buf, width=168*mm, height=65*mm))
    except Exception:
        story.append(Paragraph(
            "Plots unavailable — `matplotlib`/`numpy` not installed. To enable plots, install: pip install matplotlib numpy",
            STYLES['Note']))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Gap Analysis Summary & Praxiotech Solutions", STYLES['H2']))
    prx_map = {
        'Reputation':       ('Review Velocity Campaign', '80 EUR/mo',  '45 days', '+12-18 pts'),
        'Responsiveness':   ('AI Review Manager',        '120 EUR/mo', '14 days', '+25-40 pts'),
        'Digital Presence': ('Profile Optimization',     '60 EUR/mo',  '7 days',  '+15-25 pts'),
        'Intelligence':     ('Sentiment Monitoring',     '80 EUR/mo',  '30 days', '+10-20 pts'),
        'Visibility':       ('Engagement Booster',       '60 EUR/mo',  '30 days', '+10-15 pts'),
    }
    tgts = {'Reputation':90,'Responsiveness':90,'Digital Presence':90,'Intelligence':80,'Visibility':85}

    hrow = [Paragraph(col, STYLES['TH']) for col in [t('pdf_dimension', language), t('pdf_current', language), t('pdf_target', language), t('pdf_gap', language), t('pdf_solution', language), t('pdf_investment', language), t('pdf_timeline', language), t('pdf_est_lift', language)]]
    rows = [hrow]
    for dim in dims:
        sc = scores[dim]; tgt = tgts[dim]; gv = tgt - sc
        sol, inv, tm, lift = prx_map[dim]
        gc = CR if gv > 15 else (CA if gv > 0 else CG)
        gs = f"+{gv:.0f}" if gv > 0 else f"{gv:.0f}"
        rows.append([
            Paragraph(dim, S('gtl',fontSize=9,textColor=CN)),
            Paragraph(f"{sc:.0f}%", S('gtc',fontName='Helvetica-Bold',fontSize=9,textColor=CB,alignment=TA_CENTER)),
            Paragraph(f"{tgt}%",  S('gtc2',fontSize=9,textColor=CSl,alignment=TA_CENTER)),
            Paragraph(f"<b>{gs}</b>", S('gtg',fontName='Helvetica-Bold',fontSize=9,textColor=gc,alignment=TA_CENTER)),
            Paragraph(sol, S('gts',fontSize=8.5,textColor=CN)),
            Paragraph(f"<b>{inv}</b>", S('gti',fontName='Helvetica-Bold',fontSize=9,textColor=CT,alignment=TA_CENTER)),
            Paragraph(tm, S('gtt',fontSize=8.5,textColor=CSl,alignment=TA_CENTER)),
            Paragraph(f"<b>{lift}</b>", S('gtlf',fontName='Helvetica-Bold',fontSize=9,textColor=CG,alignment=TA_CENTER)),
        ])

    gt = Table(rows, colWidths=[28*mm,16*mm,14*mm,12*mm,40*mm,22*mm,17*mm,22*mm], repeatRows=1)
    gt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),CN), ('FONTSIZE',(0,0),(-1,0),8),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('ALIGN',(0,1),(0,-1),'LEFT'), ('ALIGN',(4,1),(4,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,CLt]),
        ('LINEBELOW',(0,0),(-1,-1),0.4,CBd), ('BOX',(0,0),(-1,-1),0.5,CBd),
    ]))
    story.append(gt)
    story.append(Spacer(1, 4*mm))

    big = max(gaps, key=gaps.get) if gaps else 'Responsiveness'
    bv  = gaps.get(big, 0)
    ob  = Table([[Paragraph(
        f"<b>Top Sales Lever:</b> Closing the <b>{big}</b> gap of <b>{bv:.0f} pts</b> via Praxiotech's AI platform "
        f"delivers an average <b>+18 pt Health Score improvement</b> in 60 days — pushing {res_name} into the "
        f"<b>Top 3</b> and directly increasing organic booking volume.",
        S('obody', fontSize=10, textColor=CN, leading=14))]], colWidths=[175*mm])
    ob.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),COFF), ('LINEABOVE',(0,0),(-1,-1),3,CA),
        ('LINEBEFORE',(0,0),(-1,-1),3,CA),
        ('TOPPADDING',(0,0),(-1,-1),9), ('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),10), ('RIGHTPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(ob)
    return story


def _momentum_page(res_name, res_data, scores, momentum_data, df_rest, df_rev, language="EN"):
    from translations import t
    import pandas as pd
    story = [Spacer(1, 5*mm)]
    story.append(Paragraph(t("pdf_momentum", language), STYLES['H1']))
    story.append(HRFlowable(width='100%', thickness=2, color=CG, spaceAfter=3*mm))
    story.append(Paragraph(
        "Momentum analysis tracks review velocity — the rate at which new customer reviews are generated. "
        "A declining velocity signals reduced Google Maps ranking authority. "
        "Surges indicate significant events requiring an active owner response strategy.",
        STYLES['Body']))

    if momentum_data is not None and len(momentum_data) > 0:
        months = [str(m)[:7] for m in momentum_data['month']]
        counts = [float(c) for c in momentum_data['count']]
    else:
        months = [f"M-{i}" for i in range(13)]
        # numpy may be unavailable; fall back to a simple deterministic default
        try:
            import numpy as np
            counts = np.random.poisson(3.5, 13).tolist()
        except Exception:
            counts = [3 for _ in range(13)]

    avg_vel = sum(counts)/len(counts) if counts else 0
    recent3 = sum(counts[-3:])/3 if len(counts) >= 3 else avg_vel
    trend_str = "ACCELERATING" if recent3 > avg_vel*1.1 else ("DECLINING" if recent3 < avg_vel*0.8 else "STABLE")
    trend_clr = '#22C55E' if trend_str == "ACCELERATING" else ('#EF4444' if trend_str == 'DECLINING' else '#F59E0B')

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={'width_ratios':[3,1.2]})
        x = range(len(counts))
        ax1.fill_between(x, counts, alpha=0.12, color='#0EA5E9')
        ax1.plot(x, counts, color='#0EA5E9', linewidth=2.2, zorder=3)
        ax1.scatter(x, counts, color='#0EA5E9', s=28, zorder=4, edgecolors='white', linewidths=1)
        ax1.set_facecolor('#F8FAFC'); fig.patch.set_facecolor('#FFFFFF')
        ax1.yaxis.grid(True, color='#E2E8F0', linewidth=0.6, zorder=0); ax1.set_axisbelow(True)
        for spine in ax1.spines.values(): spine.set_color('#E2E8F0')
        step = max(1, len(months)//6)
        ax1.set_xticks(list(range(0, len(months), step)))
        ax1.set_xticklabels([months[i][-5:] for i in range(0, len(months), step)], fontsize=7.5)
        ax1.set_ylabel('Reviews/Month', fontsize=8); ax1.set_title('Review Velocity (13-Month)', fontsize=9, pad=4)
        ax1.axhline(avg_vel, color='#64748B', linewidth=1, linestyle='--', alpha=0.7)

        rc = None
        if '_slug' in df_rest.columns and '_slug' in df_rev.columns:
            try:
                rest_slug = df_rest[df_rest['name'] == res_name].iloc[0]['_slug']
                sub = df_rev[df_rev['_slug'] == rest_slug]
                if len(sub) > 0 and 'review_rating' in df_rev.columns:
                    rc = sub['review_rating'].value_counts().sort_index(ascending=False)
            except (IndexError, KeyError):
                pass
        if rc is None or len(rc) == 0:
            rc = pd.Series([40,30,15,10,5], index=[5,4,3,2,1])

        donut_clrs = ['#22C55E','#86EFAC','#FCD34D','#FCA5A5','#EF4444']
        ax2.pie(rc.values, colors=donut_clrs[:len(rc)], startangle=90, wedgeprops={'width':0.5})
        ax2.set_title('Rating Split', fontsize=9, pad=4)
        ax2.legend([f"{i}★ ({v})" for i,v in zip(rc.index, rc.values)],
                   loc='lower center', bbox_to_anchor=(0.5,-0.22), fontsize=6.5, ncol=2, framealpha=0.8)
        plt.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format='PNG', dpi=140, bbox_inches='tight'); plt.close(fig); buf.seek(0)
        story.append(RLImage(buf, width=168*mm, height=65*mm))
    except Exception:
        story.append(Paragraph(
            "Plots unavailable — `matplotlib` not installed. To enable plots, install: pip install matplotlib numpy",
            STYLES['Note']))
    story.append(Spacer(1, 3*mm))

    tc_clr = HexColor(trend_clr)
    srow = [
        [Paragraph("AVG VELOCITY", STYLES['KPIL']), Paragraph("3-MONTH TREND", STYLES['KPIL']),
         Paragraph("TREND STATUS", STYLES['KPIL']),  Paragraph("MONTHS ANALYZED", STYLES['KPIL'])],
        [Paragraph(f"<b>{avg_vel:.1f}/mo</b>", STYLES['KPIV']), Paragraph(f"<b>{recent3:.1f}/mo</b>", STYLES['KPIV']),
         Paragraph(f"<b>{trend_str}</b>", S('ts',fontName='Helvetica-Bold',fontSize=13,textColor=tc_clr,alignment=TA_CENTER)),
         Paragraph(f"<b>{len(counts)}</b>", STYLES['KPIV'])],
    ]
    st_tbl = Table(srow, colWidths=[43.75*mm]*4)
    st_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),CLt), ('LINEABOVE',(0,0),(-1,0),2,CG),
        ('LINEBELOW',(0,-1),(-1,-1),0.5,CBd),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LINEBEFORE',(1,0),(1,-1),0.5,CBd), ('LINEBEFORE',(2,0),(2,-1),0.5,CBd), ('LINEBEFORE',(3,0),(3,-1),0.5,CBd),
    ]))
    story.append(st_tbl)
    return story


def _action_page(res_name, scores, gaps, persona, language="EN"):
    from translations import t
    story = [Spacer(1, 5*mm)]
    story.append(Paragraph(t("pdf_action_plan", language), STYLES['H1']))
    story.append(HRFlowable(width='100%', thickness=2, color=CPu, spaceAfter=3*mm))
    story.append(Paragraph(
        f"The following 90-day plan translates audit findings into a structured engagement for {res_name}. "
        "Each initiative maps to a Praxiotech service, investment level, and projected outcome.",
        STYLES['Body']))

    rdmap = [
        ["Phase","Timeframe","Initiative","Praxiotech Service","Investment","KPI"],
        ["QUICK WIN","Days 1-14","Google Profile Optimization","Profile Audit + Setup","60 EUR/mo","Profile 100%"],
        ["QUICK WIN","Days 1-14","AI Review Responses Live","AI Review Manager","120 EUR/mo","Rate > 80%"],
        ["GROWTH","Days 15-45","Review Velocity Campaign","SMS Follow-up System","80 EUR/mo","+15 reviews"],
        ["GROWTH","Days 15-45","Sentiment Monitoring","Sentiment Dashboard","80 EUR/mo","Alert <2hr"],
        ["AUTHORITY","Days 46-90","Monthly Intelligence Brief","Reporting Suite","Incl.","Top 3 rank"],
        ["AUTHORITY","Days 46-90","ROI Attribution Report","Revenue Dashboard","Incl.","3x bookings"],
    ]
    phase_bg = {'QUICK WIN': HexColor('#DCFCE7'), 'GROWTH': HexColor('#DBEAFE'), 'AUTHORITY': HexColor('#EDE9FE')}
    phase_tc = {'QUICK WIN': CG, 'GROWTH': CB, 'AUTHORITY': CPu}

    rh = [Paragraph(t, STYLES['TH']) for t in rdmap[0]]
    rrows = [rh]
    for row in rdmap[1:]:
        rrows.append([Paragraph(str(c), S('rt',fontSize=8.5,textColor=CN,
                       alignment=TA_CENTER if i != 2 and i != 3 else TA_LEFT)) for i,c in enumerate(row)])
    pstyles = []
    for ri, row in enumerate(rdmap[1:], start=1):
        ph = row[0]
        pstyles += [('BACKGROUND',(0,ri),(0,ri),phase_bg.get(ph,white)),
                    ('TEXTCOLOR',(0,ri),(0,ri),phase_tc.get(ph,CN)),
                    ('FONTNAME',(0,ri),(0,ri),'Helvetica-Bold')]
    rt = Table(rrows, colWidths=[20*mm,20*mm,42*mm,40*mm,20*mm,25*mm], repeatRows=1)
    rt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),CN), ('FONTSIZE',(0,0),(-1,0),8),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('ALIGN',(2,1),(3,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,CLt]),
        ('LINEBELOW',(0,0),(-1,-1),0.4,CBd), ('BOX',(0,0),(-1,-1),0.5,CBd),
    ] + pstyles))
    story.append(rt)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Investment Summary", STYLES['H2']))
    inv = [
        ["Service Tier","Monthly","Annual","Expected Impact"],
        ["Starter  (AI Reviews + Profile)","180 EUR","2,160 EUR","+8-15% booking conversion"],
        ["Growth   (+ Velocity + Sentiment)","340 EUR","4,080 EUR","+20-30% digital authority"],
        ["Authority (Full Suite)","480 EUR","5,760 EUR","+35-50% organic traffic"],
        ["RECOMMENDED FOR THIS RESTAURANT","340 EUR","4,080 EUR","Est. ROI: 4.2x in 12 months"],
    ]
    it = Table([[Paragraph(c, STYLES['TH']) for c in inv[0]]] +
               [[Paragraph(str(c), S('itc',fontSize=9,textColor=CN,alignment=TA_CENTER if i>0 else TA_LEFT))
                 for i,c in enumerate(row)] for row in inv[1:]],
               colWidths=[62*mm,28*mm,28*mm,57*mm], repeatRows=1)
    it.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),CN),
        ('BACKGROUND',(0,-1),(-1,-1),HexColor('#0F172A')), ('TEXTCOLOR',(0,-1),(-1,-1),CT),
        ('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('ALIGN',(0,1),(0,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[white,CLt]),
        ('LINEBELOW',(0,0),(-1,-1),0.4,CBd), ('BOX',(0,0),(-1,-1),0.5,CBd),
    ]))
    story.append(it)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Sales Pitch Scripts", STYLES['H2']))
    p = persona
    for lang, label, color, body in [
        ('EN', 'ENGLISH Opening Hook', CB, p['pitch_en']),
        ('DE', 'DEUTSCH Verkaufsargument', CT, p['pitch_de']),
    ]:
        pt = Table([
            [Paragraph(f"<b>{label}</b>", S(f'pl{lang}',fontName='Helvetica-Bold',fontSize=9,textColor=color))],
            [Paragraph(body, S(f'pb{lang}',fontSize=9.5,textColor=CN,leading=14,alignment=TA_JUSTIFY))],
        ], colWidths=[175*mm])
        pt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),HexColor('#EFF6FF') if lang=='EN' else HexColor('#F0FDFA')),
            ('BACKGROUND',(0,1),(-1,1),white), ('LINEABOVE',(0,0),(-1,0),3,color),
            ('BOX',(0,0),(-1,-1),0.5,CBd),
            ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LEFTPADDING',(0,0),(-1,-1),9), ('RIGHTPADDING',(0,0),(-1,-1),9),
        ]))
        story.append(pt); story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width='100%', thickness=0.5, color=CBd, spaceAfter=2*mm))
    story.append(Paragraph(
        f"Disclaimer: This brief is for internal Praxiotech sales use only. Benchmarks derived from public "
        f"Google Maps data. Projected ROI figures are estimates based on comparable client results and are not guaranteed. "
        f"Prepared {datetime.now().strftime('%B %Y')}.",
        STYLES['Note']))
    return story
