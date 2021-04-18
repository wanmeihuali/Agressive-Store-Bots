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
            self.toNumber = '+13125369588'
            self.fromNumber = '+12032957363'
            self.accountSid = 'ACc220ddb24b4e4f3c6177072ce77cf566'
            self.authToken = '5149f8c2b6c0da17e45beadb30dadca7'
            self.twilio_client = Client(self.accountSid, self.authToken)

    def send_message(self, content):
        with self.lock:
            if self.telegram_bot is not None:
                self.telegram_bot.send_message(chat_id=self.telegram_chat_id, text=content)
            if self.twilio_client is not None:
                try:
                    self.twilio_client.messages.create(to=self.toNumber, from_=self.fromNumber,
                                           body=content)
                except (NameError, TwilioRestException):
                    pass

