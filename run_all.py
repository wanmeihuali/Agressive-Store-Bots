import json
from MessageSender import MessageSender
from amazon import AmazonBot
from bestbuy import BestbuyBot
import threading
import signal


class BotRunner:
    def __init__(self):
        self.bots = []

    def stop_all(self):
        for bot in self.bots:
            bot.stop_running()

    def run_all(self):
        with open("config.json", "r") as f:
            config = json.load(f)

        sender = MessageSender(config)
        self.bots = []
        for amazon_config in config["amazon"]:
            self.bots.append(AmazonBot(config["global"], amazon_config, sender, self.stop_all))

        for bestbuy_config in config["bestbuy"]:
            self.bots.append(BestbuyBot(config["global"], bestbuy_config, sender, self.stop_all))

        threads = []
        for bot in self.bots:
            thread = threading.Thread(target=bot.run)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()




if __name__ == "__main__":

    bot_runner = BotRunner()

    #signal.signal(signal.SIGINT, lambda signum, frame: bot_runner.stop_all)
    #signal.signal(signal.SIGTERM, lambda signum, frame: bot_runner.stop_all)

    bot_runner.run_all()
