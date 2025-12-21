# core/notifications.py
"""
Notification system for price drops and alerts
Supports Email (SMTP) and Telegram
"""
import os
import asyncio
from typing import List, Optional
from core.logging import get_logger
from core.config import config

logger = get_logger("notifications")


class EmailNotifier:
    """Email notifications via SMTP"""

    def __init__(self):
        self.enabled = config.get("notifications.email.enabled", False)
        self.smtp_host = os.getenv("SMTP_HOST") or config.get("notifications.email.smtp_host")
        self.smtp_port = int(os.getenv("SMTP_PORT", config.get("notifications.email.smtp_port", 587)))
        self.smtp_user = os.getenv("SMTP_USER") or config.get("notifications.email.smtp_user")
        self.smtp_password = os.getenv("SMTP_PASSWORD") or config.get("notifications.email.smtp_password")
        self.from_email = os.getenv("SMTP_FROM") or config.get("notifications.email.from_email")

        if self.enabled:
            logger.info(f"📧 Email notifications enabled: {self.smtp_host}:{self.smtp_port}")

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification"""
        if not self.enabled:
            logger.debug("Email notifications disabled")
            return False

        try:
            import aiosmtplib
            from email.message import EmailMessage

            message = EmailMessage()
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True
            )

            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    async def send_price_drop_email(self, to_email: str, model: str, old_price: float,
                                   new_price: float, drop_percent: float) -> bool:
        """Send price drop notification email"""
        subject = f"💰 Price Drop Alert: {model}"
        body = f"""
GPU Price Drop Alert!

Model: {model}
Old Price: {old_price:.2f} лв
New Price: {new_price:.2f} лв
Drop: {drop_percent:.1f}%

This is a significant price drop! Check it out before it's gone.

---
GPU Market Service
Unsubscribe: http://localhost:8000/unsubscribe
        """.strip()

        return await self.send_email(to_email, subject, body)


class TelegramNotifier:
    """Telegram bot notifications"""

    def __init__(self):
        self.enabled = config.get("notifications.telegram.enabled", False)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or config.get("notifications.telegram.bot_token")
        self.chat_ids = config.get("notifications.telegram.chat_ids", [])

        if self.enabled and self.bot_token:
            logger.info(f"📱 Telegram notifications enabled for {len(self.chat_ids)} chats")
        elif self.enabled:
            logger.warning("⚠️ Telegram enabled but no bot token configured")

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send Telegram message"""
        if not self.enabled or not self.bot_token:
            logger.debug("Telegram notifications disabled")
            return False

        try:
            from telegram import Bot

            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )

            logger.info(f"✅ Telegram message sent to {chat_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")
            return False

    async def send_price_drop_alert(self, model: str, old_price: float,
                                   new_price: float, drop_percent: float) -> bool:
        """Send price drop alert to all configured chats"""
        if not self.chat_ids:
            logger.warning("No Telegram chat IDs configured")
            return False

        message = f"""
💰 <b>Price Drop Alert!</b>

<b>Model:</b> {model}
<b>Old Price:</b> {old_price:.2f} лв
<b>New Price:</b> {new_price:.2f} лв
<b>Drop:</b> {drop_percent:.1f}% 📉

Act fast before it's gone! 🏃‍♂️
        """.strip()

        results = []
        for chat_id in self.chat_ids:
            result = await self.send_message(chat_id, message)
            results.append(result)

        return any(results)


class NotificationManager:
    """Unified notification manager"""

    def __init__(self):
        self.email = EmailNotifier()
        self.telegram = TelegramNotifier()
        logger.info("📬 Notification manager initialized")

    async def notify_price_drop(self, model: str, old_price: float,
                               new_price: float, email_to: Optional[List[str]] = None):
        """
        Send price drop notification via all enabled channels

        Args:
            model: GPU model name
            old_price: Previous price
            new_price: Current price
            email_to: Optional list of email addresses
        """
        drop_percent = ((old_price - new_price) / old_price) * 100

        logger.info(
            f"📢 Sending price drop notification: {model} "
            f"{old_price:.2f}лв → {new_price:.2f}лв (-{drop_percent:.1f}%)"
        )

        # Send Telegram notification
        if self.telegram.enabled:
            await self.telegram.send_price_drop_alert(model, old_price, new_price, drop_percent)

        # Send email notifications
        if self.email.enabled and email_to:
            for email in email_to:
                await self.email.send_price_drop_email(
                    email, model, old_price, new_price, drop_percent
                )

    async def notify_scrape_completed(self, total_listings: int, unique_models: int):
        """Notify that scraping completed"""
        message = f"""
🔄 <b>Data Collection Completed</b>

<b>Total Listings:</b> {total_listings}
<b>Unique Models:</b> {unique_models}

Data has been updated successfully!
        """.strip()

        if self.telegram.enabled and self.telegram.chat_ids:
            for chat_id in self.telegram.chat_ids:
                await self.telegram.send_message(chat_id, message)


# Global notification manager
notifier = NotificationManager()
