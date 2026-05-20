
from app.core.config import settings
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

class NotificationService:
    """
    Håndterer utsending av varsler via E-post (SMTP/SendGrid).
    Foreløpig implementert som en 'stub' for å vise intensjon og flyt.
    """

    async def send_email(self, to_email: str, subject: str, body: str):
        """
        Sender e-post varsel.
        
        TODO: Integrer med e-post leverandør (f.eks. SendGrid).
        """
        if not to_email:
            logger.warning("Notification skipped: No email provided.")
            return

        logger.info(f"📧 Notification sent: To: {to_email} | Subject: {subject}")
        logger.info(f"Body: {body[:100]}...")
        
        # Plassholder for faktisk implementasjon:
        # await email_provider.send(to=to_email, subject=subject, content=body)
        
        return True

    async def notify_deviation(self, deviation_id: str, title: str, severity: str):
        """
        Varsler om nytt avvik hvis brukeren har aktivert e-postvarsling.
        """
        # Hent brukerens preferanser (dette ville normalt sjekket DB)
        user_wants_email = True 
        
        if user_wants_email:
            subject = f"⚠️ Nytt Avvik: {title} ({severity})"
            body = f"Ett nytt avvik er registrert (ID: {deviation_id}). Vennligst logg inn i BEFS for å behandle dette."
            await self.send_email("frank.vevle@bufetat.no", subject, body)

notification_service = NotificationService()
