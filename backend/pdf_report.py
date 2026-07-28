"""Generate the official-style Fujitec Service Inspection Report PDF."""
import base64
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, Image, KeepTogether)

JUDGMENT_MARK = {"good": "✔", "replaced": "◎", "damage": "✖", "none": "▬", None: ""}
JUDGMENT_LABEL = {"good": "Good", "replaced": "Replaced/Adjusted",
                  "damage": "Damage", "none": "None"}

NAVY = colors.HexColor("#0A2540")
LIGHT = colors.HexColor("#EEF2F7")


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


def build_sir_pdf(insp: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=12 * mm, bottomMargin=12 * mm,
                            leftMargin=10 * mm, rightMargin=10 * mm)
    st = _style()
    elems = []

    title = Paragraph("<b>PT. FUJITEC INDONESIA</b><br/>SERVICE INSPECTION REPORT &nbsp; (REXIA, ZEXIA)",
                      ParagraphStyle(name="t", fontSize=12, leading=15, textColor=NAVY, alignment=1))
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
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
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

    doc.build(elems)
    return buf.getvalue()
