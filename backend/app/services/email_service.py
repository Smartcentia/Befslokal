"""
Email service for sending verification codes and MFA links.
Supports both Resend (recommended) and SMTP.
"""
import asyncio
import hashlib
from typing import Optional
from app.core.config import settings
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

# Email retry configuration
MAX_EMAIL_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds


class EmailService:
    """
    Handles sending emails via Resend (preferred) or SMTP.
    Resend SDK v2+ uses resend.api_key + resend.Emails.send() (no Resend class).
    """
    
    def __init__(self):
        self.use_resend = bool(settings.RESEND_API_KEY)
        self.use_smtp = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
        
        if self.use_resend:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY
                self._resend = resend
                logger.info("✅ Email service initialized with Resend")
            except (ImportError, AttributeError) as e:
                logger.warning("⚠️ Resend package not available (%s), falling back to SMTP", e)
                self.use_resend = False
                self._resend = None
        elif self.use_smtp:
            logger.info("✅ Email service initialized with SMTP")
        else:
            logger.warning("⚠️ No email service configured. Emails will be logged only.")
    
    async def send_verification_code(self, email: str, code: str) -> bool:
        """
        Send email verification code (6-digit) to user.
        
        Args:
            email: Recipient email address
            code: 6-digit verification code
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Bekreft din e-postadresse - BEFS"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">Bekreft din e-postadresse</h2>
            <p>Hei,</p>
            <p>Du har registrert deg i BEFS. For å fullføre registreringen, vennligst bruk følgende bekreftelseskode:</p>
            <div style="background-color: #f3f4f6; border: 2px solid #2563eb; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="color: #2563eb; font-size: 32px; letter-spacing: 8px; margin: 0;">{code}</h1>
            </div>
            <p>Denne koden er gyldig i 15 minutter.</p>
            <p>Hvis du ikke har registrert deg, kan du ignorere denne e-posten.</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #6b7280; font-size: 12px;">BEFS - Bufetat Eiendomsforvaltningssystem</p>
        </body>
        </html>
        """
        
        text_body = f"""
Bekreft din e-postadresse - BEFS

Hei,

Du har registrert deg i BEFS. For å fullføre registreringen, vennligst bruk følgende bekreftelseskode:

{code}

Denne koden er gyldig i 15 minutter.

Hvis du ikke har registrert deg, kan du ignorere denne e-posten.

---
BEFS - Bufetat Eiendomsforvaltningssystem
        """
        
        return await self._send_email(email, subject, html_body, text_body)
    
    async def send_mfa_link(self, email: str, token: str, frontend_url: str) -> bool:
        """
        Send MFA verification link to user.
        
        Args:
            email: Recipient email address
            token: MFA verification token
            frontend_url: Frontend URL for the verification link
            
        Returns:
            True if sent successfully, False otherwise
        """
        verify_url = f"{frontend_url}/verify-mfa?token={token}"
        
        subject = "Bekreft innlogging - BEFS"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">Bekreft innlogging</h2>
            <p>Hei,</p>
            <p>Noen har forsøkt å logge inn på din BEFS-konto. For å bekrefte at det er deg, vennligst klikk på lenken under:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Bekreft innlogging</a>
            </div>
            <p>Eller kopier og lim inn følgende lenke i nettleseren:</p>
            <p style="color: #6b7280; font-size: 12px; word-break: break-all;">{verify_url}</p>
            <p>Denne lenken er gyldig i 10 minutter.</p>
            <p style="color: #dc2626;">Hvis du ikke har forsøkt å logge inn, kan du ignorere denne e-posten.</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #6b7280; font-size: 12px;">BEFS - Bufetat Eiendomsforvaltningssystem</p>
        </body>
        </html>
        """
        
        text_body = f"""
Bekreft innlogging - BEFS

Hei,

Noen har forsøkt å logge inn på din BEFS-konto. For å bekrefte at det er deg, vennligst åpne følgende lenke:

{verify_url}

Denne lenken er gyldig i 10 minutter.

Hvis du ikke har forsøkt å logge inn, kan du ignorere denne e-posten.

---
BEFS - Bufetat Eiendomsforvaltningssystem
        """
        
        return await self._send_email(email, subject, html_body, text_body)
    
    async def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Internal method to send email via Resend or SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not to_email:
            logger.warning("Email skipped: No recipient email provided")
            return False

        # Retry with exponential backoff
        for attempt in range(1, MAX_EMAIL_RETRIES + 1):
            try:
                if self.use_resend and self._resend:
                    result = await self._send_via_resend(to_email, subject, html_body, text_body)
                elif self.use_smtp:
                    result = await self._send_via_smtp(to_email, subject, html_body, text_body)
                else:
                    # Log-only mode (for development)
                    logger.info(f"📧 Email (log-only): To: {to_email} | Subject: {subject}")
                    logger.debug(f"Body preview: {text_body[:200]}...")
                    return True

                if result:
                    if attempt > 1:
                        logger.info(f"✅ Email sent successfully on attempt {attempt}/{MAX_EMAIL_RETRIES} to {to_email}")
                    return True
                else:
                    raise Exception("Email send returned False")

            except Exception as e:
                if attempt < MAX_EMAIL_RETRIES:
                    retry_delay = INITIAL_RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"⚠️ Email attempt {attempt}/{MAX_EMAIL_RETRIES} failed for {to_email}: {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        f"❌ All {MAX_EMAIL_RETRIES} email attempts failed for {to_email}: {e}"
                    )
                    return False

        return False
    
    async def _send_via_resend(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via Resend API (resend.Emails.send)."""
        try:
            params = {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
            # Resend SDK is sync; run in thread to avoid blocking
            email_response = await asyncio.to_thread(self._resend.Emails.send, params)
            email_id = email_response.get("id", "unknown") if isinstance(email_response, dict) else "unknown"
            logger.info("✅ Email sent via Resend to %s: %s", to_email, email_id)
            return True
        except Exception as e:
            logger.error("❌ Resend API error: %s", e)
            return False
    
    async def _send_via_smtp(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via SMTP."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart("alternative")
            message["From"] = settings.EMAIL_FROM
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add both plain text and HTML versions
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            message.attach(text_part)
            message.attach(html_part)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            
            logger.info(f"✅ Email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ SMTP error: {e}")
            return False


# Singleton instance
email_service = EmailService()
