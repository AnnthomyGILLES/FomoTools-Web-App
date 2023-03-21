import os

import apprise
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class Notifier(object):
    def __init__(self, service, base_url):
        self.apobj = apprise.Apprise()
        self.apobj.add(base_url)
        self.service = service

    def notify(self, title, body):
        self.apobj.notify(
            body=body,
            title=title,
        )
        logger.info(f"Notification has been sent to {self.service}.")

    @classmethod
    def to_discord(cls, webhook_id, webhook_token):
        service = "Discord"
        base_url = f"discord://{webhook_id}/{webhook_token}"
        return cls(service, base_url)

    @classmethod
    def to_slack(cls, token_a, token_b, token_c, channel):
        service = "Slack"
        base_url = f"slack://{token_a}/{token_b}/{token_c}/#{channel}"
        return cls(service, base_url)

    @classmethod
    def to_telegram(
        cls,
        chat_id,
        bot_token=TELEGRAM_BOT_TOKEN,
    ):
        """Telegram bot Link: http://t.me/FomotoolsBot"""
        service = "Telegram"
        base_url = f"tgram://{bot_token}/{chat_id}"
        return cls(service, base_url)


if __name__ == "__main__":
    notifier = Notifier.to_telegram("679706949")
    notifier.notify(title="Gotama is a damn genius", body="Yes you are baby!")
