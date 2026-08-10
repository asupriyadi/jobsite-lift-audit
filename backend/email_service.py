"""Emergent-managed Resend email notifications."""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Fujitec SIR")


async def send_email(recipient_email: str, subject: str, html_content: str, reply_to: str = None):
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
    try:
        async with httpx.AsyncClient(timeout=30) as client:
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


def spare_change_html(insp: dict, sp: dict, field_label: str, new_value_label: str, changed_by: str) -> str:
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;background:#f1f5f9;padding:24px">
      <tr><td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0">
          <tr><td style="background:#0A2540;padding:20px 28px">
            <span style="color:#fff;font-size:18px;font-weight:800">FUJITEC SIR</span>
            <span style="color:#93c5fd;font-size:12px;display:block">Update Status Spare Part</span>
          </td></tr>
          <tr><td style="padding:24px 28px;color:#0f172a">
            <p style="margin:0 0 14px;font-size:15px">Terjadi perubahan status spare part pada laporan inspeksi berikut:</p>
            <table width="100%" cellpadding="6" style="font-size:13px;border-collapse:collapse">
              <tr><td style="color:#64748b;width:150px">Spare Part</td><td style="font-weight:700">{sp.get('name','')}</td></tr>
              <tr><td style="color:#64748b">Qty</td><td>{sp.get('quantity','') or '-'}</td></tr>
              <tr><td style="color:#64748b">Site / Gedung</td><td>{insp.get('site_name','')}</td></tr>
              <tr><td style="color:#64748b">Job Number</td><td>{insp.get('job_number','')} &middot; Lift {insp.get('lift_number','')}</td></tr>
              <tr><td style="color:#64748b">Perubahan</td><td><b>{field_label}</b> &rarr; <span style="color:#2563eb;font-weight:700">{new_value_label}</span></td></tr>
              <tr><td style="color:#64748b">Oleh</td><td>{changed_by}</td></tr>
            </table>
            <p style="margin:18px 0 0;font-size:12px;color:#94a3b8">Email otomatis dari aplikasi Fujitec Service Inspection Report.</p>
          </td></tr>
        </table>
      </td></tr>
    </table>
    """
