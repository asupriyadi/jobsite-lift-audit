"""Generate the official-style Fujitec report PDFs (SIR, ECR, HOR)."""
import base64
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, Image, KeepTogether, PageBreak)

JUDGMENT_MARK = {"good": "✔", "replaced": "◎", "damage": "✖", "none": "▬", None: ""}
JUDGMENT_LABEL = {"good": "Good", "replaced": "Replaced/Adjusted",
                  "damage": "Damage", "none": "None"}

NAVY = colors.HexColor("#0A2540")
LIGHT = colors.HexColor("#EEF2F7")
GREY = colors.HexColor("#6B7280")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "fujitec_logo.png")


def _header_block(title_html):
    """Logo pinned to the left margin, title kept centered on the page."""
    try:
        logo = Image(LOGO_PATH, width=30 * mm, height=30 * mm * 686.0 / 2000.0)
    except Exception:
        logo = ""
    title = Paragraph(title_html, ParagraphStyle(
        name="rt", fontSize=12, leading=15, textColor=NAVY, alignment=1))
    tbl = Table([[logo, title, ""]], colWidths=[38 * mm, 114 * mm, 38 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
    ]))
    return tbl


def std_filename(prefix, date_str, job, site, unit):
    ymd = (date_str or "").replace("-", "").strip()
    site = (site or "").strip()
    unit = (unit or "").strip()
    parts = [prefix]
    if ymd:
        parts.append(ymd)
    if job:
        parts.append(str(job).strip())
    name = "-".join(parts)
    if site:
        name += f"-{site}"
    if unit and unit.lower() not in site.lower():
        name += f"#{unit}"
    return name + ".pdf"


def _style():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="cell", fontSize=7, leading=9))
    styles.add(ParagraphStyle(name="cellb", fontSize=7, leading=9, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="small", fontSize=6.5, leading=8))
    return styles


def _sig_image(data_url):
    if not data_url or "," not in data_url:
        return ""
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1])
        return Image(io.BytesIO(raw), width=40 * mm, height=18 * mm)
    except Exception:
        return ""


def build_sir_pdf(insp: dict, photos: dict = None) -> bytes:
    photos = photos or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=12 * mm, bottomMargin=12 * mm,
                            leftMargin=10 * mm, rightMargin=10 * mm)
    st = _style()
    elems = []

    title = _header_block("<b>PT. FUJITEC INDONESIA</b><br/>SERVICE INSPECTION REPORT &nbsp; (REXIA, ZEXIA)")
    elems.append(title)
    elems.append(Spacer(1, 4 * mm))

    header = [
        ["Job Number", insp.get("job_number", ""), "Date", insp.get("inspection_date", "")],
        ["Site Name", insp.get("site_name", ""), "Time", f"{insp.get('time_from','')} - {insp.get('time_to','')}"],
        ["Service By", insp.get("serviced_by", ""), "Total Unit", str(insp.get("total_units", ""))],
        ["Lift Number", insp.get("lift_number", ""), "Check List", insp.get("checklist_type", "")],
    ]
    ht = Table(header, colWidths=[28 * mm, 62 * mm, 28 * mm, 72 * mm])
    ht.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(ht)
    elems.append(Spacer(1, 4 * mm))

    data = [[Paragraph("<b>No</b>", st["cell"]), Paragraph("<b>Location</b>", st["cell"]),
             Paragraph("<b>Description</b>", st["cell"]), Paragraph("<b>Judg.</b>", st["cell"]),
             Paragraph("<b>Measurement</b>", st["cell"]), Paragraph("<b>Remarks</b>", st["cell"])]]
    for it in insp.get("items", []):
        meas = "; ".join([f"P{p.get('index',i+1)}: {p.get('measurement','')}"
                          for i, p in enumerate(it.get("points", [])) if p.get("measurement")])
        data.append([
            Paragraph(str(it.get("no", "")), st["cell"]),
            Paragraph(it.get("section", ""), st["small"]),
            Paragraph(it.get("description", ""), st["cell"]),
            Paragraph(JUDGMENT_MARK.get(it.get("judgment"), ""), st["cellb"]),
            Paragraph(meas, st["small"]),
            Paragraph(it.get("remark", ""), st["small"]),
        ])
    tbl = Table(data, colWidths=[8 * mm, 24 * mm, 74 * mm, 12 * mm, 36 * mm, 36 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), GREY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph("Legend: ✔ Good &nbsp; ◎ Replaced/Adjusted &nbsp; ✖ Damage &nbsp; ▬ None", st["small"]))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(f"<b>Global Remark:</b> {insp.get('global_remark','') or '-'}", st["cell"]))
    elems.append(Spacer(1, 3 * mm))

    sps = insp.get("spare_parts", [])
    if sps:
        sp_data = [[Paragraph("<b>Spare Part</b>", st["cell"]), Paragraph("<b>Qty</b>", st["cell"]),
                    Paragraph("<b>Sales</b>", st["cell"]), Paragraph("<b>Customer PO</b>", st["cell"]),
                    Paragraph("<b>Inventory</b>", st["cell"]), Paragraph("<b>Maintenance</b>", st["cell"])]]
        for sp in sps:
            sp_data.append([
                Paragraph(sp.get("name", ""), st["small"]), Paragraph(str(sp.get("quantity", "")), st["small"]),
                Paragraph(sp.get("sales_status", ""), st["small"]), Paragraph(sp.get("customer_po_status", ""), st["small"]),
                Paragraph(sp.get("inventory_status", ""), st["small"]), Paragraph(sp.get("maintenance_status", ""), st["small"]),
            ])
        spt = Table(sp_data, colWidths=[50 * mm, 15 * mm, 25 * mm, 30 * mm, 30 * mm, 30 * mm], repeatRows=1)
        spt.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elems.append(Paragraph("<b>Spare Part Requirements</b>", st["cellb"]))
        elems.append(Spacer(1, 1 * mm))
        elems.append(spt)
        elems.append(Spacer(1, 4 * mm))

    sig = insp.get("signatures", {}) or {}
    roles = [("issued_by", "Issued By (Technician)"), ("customer", "Customer"),
             ("checked_by", "Checked By (Supervisor)"), ("approved_by", "Approved By (Head Maint.)")]
    sig_row_img, sig_row_name = [], []
    for key, label in roles:
        s = sig.get(key, {}) or {}
        sig_row_img.append(_sig_image(s.get("image", "")))
        sig_row_name.append(Paragraph(f"<b>{label}</b><br/>{s.get('name','') or '________'}", st["small"]))
    sig_tbl = Table([sig_row_img, sig_row_name], colWidths=[47 * mm] * 4)
    sig_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(KeepTogether([Paragraph("<b>Signatures</b>", st["cellb"]), Spacer(1, 1 * mm), sig_tbl]))

    # ---- Photo attachment sheet ----
    photo_cells = []
    for it in insp.get("items", []):
        for p in it.get("points", []):
            fid = p.get("photo_file_id")
            if fid and fid in photos:
                try:
                    img = Image(io.BytesIO(photos[fid]), width=54 * mm, height=54 * mm, kind="proportional")
                    cap = Paragraph(
                        f"<b>No.{it.get('no')} · Titik {p.get('index')}</b><br/>{p.get('measurement','') or '-'}",
                        st["small"])
                    photo_cells.append([img, cap])
                except Exception:
                    pass

    if photo_cells:
        elems.append(PageBreak())
        elems.append(Paragraph("<b>PT. FUJITEC INDONESIA</b> — LAMPIRAN FOTO PEMERIKSAAN",
                               ParagraphStyle(name="pt", fontSize=11, leading=14, textColor=NAVY, alignment=1)))
        elems.append(Spacer(1, 4 * mm))
        cols = 3
        grid = []
        row_img, row_cap = [], []
        for i, (img, cap) in enumerate(photo_cells):
            row_img.append(img)
            row_cap.append(cap)
            if len(row_img) == cols:
                grid.append(row_img); grid.append(row_cap)
                row_img, row_cap = [], []
        if row_img:
            while len(row_img) < cols:
                row_img.append(""); row_cap.append("")
            grid.append(row_img); grid.append(row_cap)
        ptbl = Table(grid, colWidths=[62 * mm] * cols)
        ptbl.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elems.append(ptbl)

    doc.build(elems)
    return buf.getvalue()



def _kv_header(rows, col=None):
    col = col or [28 * mm, 62 * mm, 28 * mm, 72 * mm]
    t = Table(rows, colWidths=col)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _section_block(st, label, text):
    tbl = Table([[Paragraph(f"<b>{label}</b>", st["cell"]), Paragraph((text or "-").replace("\n", "<br/>"), st["cell"])]],
                colWidths=[38 * mm, 152 * mm])
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, 0), GREY),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _sig_grid(st, roles, sig):
    row_img, row_name = [], []
    for key, label in roles:
        s = (sig or {}).get(key, {}) or {}
        row_img.append(_sig_image(s.get("image", "")))
        row_name.append(Paragraph(f"<b>{label}</b><br/>{s.get('name','') or '________'}", st["small"]))
    w = 190.0 / len(roles) * mm
    tbl = Table([row_img, row_name], colWidths=[w] * len(roles))
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def build_ecr_pdf(rep: dict, photos: dict = None) -> bytes:
    photos = photos or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=12 * mm, bottomMargin=12 * mm,
                            leftMargin=10 * mm, rightMargin=10 * mm)
    st = _style()
    e = [_header_block("<b>PT. FUJITEC INDONESIA</b><br/>WORK REPORT (CALL BACK / ECR)"), Spacer(1, 4 * mm)]
    e.append(_kv_header([
        ["Technician", rep.get("technician", ""), "Date", rep.get("report_date", "")],
        ["Site Name", rep.get("site_name", ""), "Time", f"{rep.get('time_from','')} - {rep.get('time_to','')}"],
        ["Unit No", rep.get("unit_no", ""), "Job No", rep.get("job_number", "")],
        ["Billing", rep.get("billing", ""), "Status", rep.get("work_status", "")],
    ]))
    e.append(Spacer(1, 3 * mm))
    for label, key in [("WORKING DETAILS / DESCRIPTION", "working_details"), ("E/C", "ec"),
                       ("ACTION", "action"), ("CAUSE", "cause"), ("SOLUTION", "solution"),
                       ("STATUS", "work_status")]:
        e.append(_section_block(st, label, rep.get(key, "")))
        e.append(Spacer(1, 1.5 * mm))
    e.append(Spacer(1, 3 * mm))
    e.append(Paragraph("<b>Signatures</b>", st["cellb"]))
    e.append(Spacer(1, 1 * mm))
    e.append(_sig_grid(st, [("customer", "Customer"), ("issuer", "Issuer"),
                            ("checker", "Checker"), ("approver", "Approver")], rep.get("signatures")))
    _append_photo_sheet(e, st, _collect_flat_photos(rep, photos), "LAMPIRAN FOTO")
    doc.build(e)
    return buf.getvalue()


def build_hor_pdf(rep: dict, photos: dict = None) -> bytes:
    photos = photos or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=12 * mm, bottomMargin=12 * mm,
                            leftMargin=10 * mm, rightMargin=10 * mm)
    st = _style()
    e = [_header_block("<b>PT. FUJITEC INDONESIA</b><br/>HAND OVER REPORT"), Spacer(1, 4 * mm)]
    e.append(_kv_header([
        ["Date", rep.get("report_date", ""), "Job No", rep.get("job_number", "")],
        ["Building", rep.get("site_name", ""), "Lift No", rep.get("lift_number", "")],
    ]))
    e.append(Spacer(1, 3 * mm))

    def parts_table(title, parts):
        e.append(Paragraph(f"<b>{title}</b>", st["cellb"]))
        rows = [[Paragraph("<b>No</b>", st["cell"]), Paragraph("<b>Spare Part</b>", st["cell"]), Paragraph("<b>Qty</b>", st["cell"])]]
        for i, p in enumerate(parts or []):
            rows.append([Paragraph(str(i + 1), st["cell"]), Paragraph(p.get("name", ""), st["cell"]), Paragraph(str(p.get("qty", "")), st["cell"])])
        if len(rows) == 1:
            rows.append([Paragraph("-", st["cell"]), Paragraph("-", st["cell"]), Paragraph("-", st["cell"])])
        t = Table(rows, colWidths=[10 * mm, 150 * mm, 30 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                               ("BACKGROUND", (0, 0), (-1, 0), GREY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        e.append(t)
        e.append(Spacer(1, 3 * mm))

    parts_table("Spare Parts Replaced (New)", rep.get("parts_replaced"))
    parts_table("Used (Second-hand) Parts Handed Over to Building", rep.get("parts_handover"))
    parts_table("Parts Returned to Fujitec", rep.get("parts_returned"))
    if rep.get("note"):
        e.append(Paragraph(f"<b>Note:</b> {rep.get('note')}", st["cell"]))
        e.append(Spacer(1, 3 * mm))
    e.append(Paragraph("<b>Signatures</b>", st["cellb"]))
    e.append(Spacer(1, 1 * mm))
    e.append(_sig_grid(st, [("fujitec_rep", "PT. Fujitec Indonesia"), ("customer", "Customer / Building")], rep.get("signatures")))

    # Before/After photo sheet for replaced parts
    ba = []
    for i, p in enumerate(rep.get("parts_replaced", []) or []):
        for kind, k in [("Sebelum", "before_photo_file_id"), ("Sesudah", "after_photo_file_id")]:
            fid = p.get(k)
            if fid and fid in photos:
                ba.append((photos[fid], f"{p.get('name','')} — {kind}"))
    _append_photo_sheet(e, st, ba, "LAMPIRAN FOTO (SEBELUM & SESUDAH)")
    doc.build(e)
    return buf.getvalue()


def _collect_flat_photos(rep, photos):
    out = []
    for fid in rep.get("photo_file_ids", []) or []:
        if fid in photos:
            out.append((photos[fid], ""))
    return out


def _append_photo_sheet(elems, st, cells, heading):
    if not cells:
        return
    elems.append(PageBreak())
    elems.append(Paragraph(f"<b>PT. FUJITEC INDONESIA</b> — {heading}",
                           ParagraphStyle(name="ph", fontSize=11, leading=14, textColor=NAVY, alignment=1)))
    elems.append(Spacer(1, 4 * mm))
    cols = 3
    grid, row_img, row_cap = [], [], []
    for data, cap in cells:
        try:
            img = Image(io.BytesIO(data), width=54 * mm, height=54 * mm, kind="proportional")
        except Exception:
            continue
        row_img.append(img)
        row_cap.append(Paragraph(cap, st["small"]))
        if len(row_img) == cols:
            grid.append(row_img); grid.append(row_cap); row_img, row_cap = [], []
    if row_img:
        while len(row_img) < cols:
            row_img.append(""); row_cap.append("")
        grid.append(row_img); grid.append(row_cap)
    ptbl = Table(grid, colWidths=[62 * mm] * cols)
    ptbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elems.append(ptbl)
