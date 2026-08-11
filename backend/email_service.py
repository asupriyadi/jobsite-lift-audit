"""Emergent-managed Resend email notifications."""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Fujitec SIR")


async def send_email(recipient_email, subject, html_content, reply_to=None, attachments=None):
    """attachments: list of {"filename": str, "content": base64-str}."""
    if not EMAIL_KEY:
        logger.warning("EMERGENT_EMAIL_KEY not set; skipping email")
        return None
    payload = {
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
        "from_name": EMAIL_FROM_NAME,
    }
    if reply_to:
        payload["contact_email"] = reply_to
    if attachments:
        payload["attachments"] = attachments
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{EMAIL_BASE_URL}/api/v1/email/send",
                headers={"X-Email-Key": EMAIL_KEY},
                json=payload,
            )
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error(f"Email send error to {recipient_email}: {e}")
        return None


def _shell(header_sub, body_html):
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;background:#f1f5f9;padding:24px">
      <tr><td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0">
          <tr><td style="background:#0A2540;padding:20px 28px">
            <span style="color:#fff;font-size:18px;font-weight:800">FUJITEC SIR</span>
            <span style="color:#93c5fd;font-size:12px;display:block">{header_sub}</span>
          </td></tr>
          <tr><td style="padding:24px 28px;color:#0f172a">{body_html}
            <p style="margin:18px 0 0;font-size:12px;color:#94a3b8">Email otomatis dari aplikasi Fujitec Service Inspection Report.</p>
          </td></tr>
        </table>
      </td></tr>
    </table>"""


def spare_change_html(insp, sp, field_label, new_value_label, changed_by):
    body = f"""
      <p style="margin:0 0 14px;font-size:15px">Terjadi perubahan status spare part pada laporan inspeksi berikut:</p>
      <table width="100%" cellpadding="6" style="font-size:13px;border-collapse:collapse">
        <tr><td style="color:#64748b;width:150px">Spare Part</td><td style="font-weight:700">{sp.get('name','')}</td></tr>
        <tr><td style="color:#64748b">Qty</td><td>{sp.get('quantity','') or '-'}</td></tr>
        <tr><td style="color:#64748b">Site / Gedung</td><td>{insp.get('site_name','')}</td></tr>
        <tr><td style="color:#64748b">Job Number</td><td>{insp.get('job_number','')} &middot; Lift {insp.get('lift_number','')}</td></tr>
        <tr><td style="color:#64748b">Perubahan</td><td><b>{field_label}</b> &rarr; <span style="color:#2563eb;font-weight:700">{new_value_label}</span></td></tr>
        <tr><td style="color:#64748b">Oleh</td><td>{changed_by}</td></tr>
      </table>"""
    return _shell("Update Status Spare Part", body)


def daily_summary_html(rows):
    if not rows:
        inner = "<p style='font-size:14px'>Tidak ada spare part yang masih pending. 🎉</p>"
    else:
        trs = "".join([
            f"<tr><td style='padding:6px;border-top:1px solid #e2e8f0'>{r.get('name','')}</td>"
            f"<td style='padding:6px;border-top:1px solid #e2e8f0'>{r.get('quantity','') or '-'}</td>"
            f"<td style='padding:6px;border-top:1px solid #e2e8f0'>{r.get('site_name','')}</td>"
            f"<td style='padding:6px;border-top:1px solid #e2e8f0'>{r.get('job_number','')}/{r.get('lift_number','')}</td>"
            f"<td style='padding:6px;border-top:1px solid #e2e8f0'>{r.get('inventory_status','')}</td></tr>"
            for r in rows])
        inner = f"""
          <p style="margin:0 0 12px;font-size:15px"><b>{len(rows)}</b> spare part masih menunggu penggantian:</p>
          <table width="100%" style="font-size:12px;border-collapse:collapse">
            <tr style="background:#f8fafc;text-align:left"><th style="padding:6px">Spare Part</th><th style="padding:6px">Qty</th><th style="padding:6px">Gedung</th><th style="padding:6px">Job/Unit</th><th style="padding:6px">Inventory</th></tr>
            {trs}
          </table>"""
    return _shell("Ringkasan Harian — Spare Part Pending", inner)


def approval_html(doc, report_kind):
    body = f"""
      <p style="margin:0 0 14px;font-size:15px">Laporan <b>{report_kind}</b> telah <b>disetujui</b>. PDF terlampir pada email ini.</p>
      <table width="100%" cellpadding="6" style="font-size:13px">
        <tr><td style="color:#64748b;width:150px">Site / Gedung</td><td style="font-weight:700">{doc.get('site_name','')}</td></tr>
        <tr><td style="color:#64748b">Job Number</td><td>{doc.get('job_number','')}</td></tr>
        <tr><td style="color:#64748b">Unit</td><td>{doc.get('unit_no') or doc.get('lift_number','')}</td></tr>
        <tr><td style="color:#64748b">Tanggal</td><td>{doc.get('inspection_date') or doc.get('report_date','')}</td></tr>
      </table>"""
    return _shell(f"{report_kind} Disetujui", body)
