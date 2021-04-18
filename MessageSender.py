import telegram
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import threading

class MessageSender:
    def __init__(self, config):
        self.lock = threading.Lock()
        self.telegram_bot = None
        if config["telegram"] is not None:
            self.telegram_chat_id = config["telegram"]["chat_id"]
            self.telegram_bot = telegram.Bot(token=config["telegram"]["token"])

        self.twilio_client = None
        if config["twilio"] is not None:
            self.toNumber = config["twilio"]["toNumber"]
            self.fromNumber = config["twilio"]["fromNumber"]
            self.accountSid = config["twilio"]["accountSid"]
            self.authToken = config["twilio"]["authToken"]
            self.twilio_client = Client(self.accountSid, self.authToken)

    def send_message(self, content, sender=None):
        with self.lock:
            if sender is not None:
                content = "Sender: " + sender + ": " + content
            if self.telegram_bot is not None:
                self.telegram_bot.send_message(chat_id=self.telegram_chat_id, text=content)
            if self.twilio_client is not None:
                try:
                    self.twilio_client.messages.create(to=self.toNumber, from_=self.fromNumber,
                                           body=content)
                except (NameError, TwilioRestException):
                    pass

