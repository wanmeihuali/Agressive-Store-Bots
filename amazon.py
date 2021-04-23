import time

import selenium.common.exceptions
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import random
import json
from utils import create_driver, time_sleep
from MessageSender import MessageSender


class AmazonBot:
    def __init__(self, global_config, amazon_config, message_sender, on_buy_success=None):

        self.global_config = global_config
        # Amazon credentials
        self.bot_name = amazon_config["name"]
        self.username = amazon_config["username"]
        self.password = amazon_config["password"]

        self.message_sender = message_sender
        # Twilio configuration
        self.message_sender.send_message("store_bot started", self.bot_name)

        self.amazonPage = amazon_config["amazonPage"]

        self.min_interval = amazon_config["min_interval"]
        self.max_interval = amazon_config["max_interval"]
        self.blacklisted = amazon_config["blacklisted"]

        self.min_price = amazon_config["min_price"]
        self.max_price = amazon_config["max_price"]

        self.item_must_include = amazon_config["item_must_include"]
        self.blacklisted_phrases = amazon_config["blacklisted_phrases"]

        self.driver = create_driver(global_config)
        self.auto_buy = global_config["auto_buy"]
        self.on_buy_success = on_buy_success
        self.stop = False

        # restart driver periodically to avoid flushing tmp folder
        self.restart_count = 5000

    def driver_wait(self, driver, find_type, selector):
        """Driver Wait Settings."""
        loop_id = 0
        while True:
            loop_id += 1
            if loop_id > 300:  # 60 sec
                print('wait failed!')
                break
            if find_type == 'css':
                try:
                    driver.find_element_by_css_selector(selector).click()
                    break
                except NoSuchElementException:
                    driver.implicitly_wait(0.2)
            elif find_type == 'name':
                try:
                    driver.find_element_by_name(selector).click()
                    break
                except NoSuchElementException:
                    driver.implicitly_wait(0.2)

    def login_attempt(self, driver):
        """Attempting to login Amazon Account."""
        driver.get('https://www.amazon.com/gp/sign-in.html')
        try:
            username_field = driver.find_element_by_css_selector('#ap_email')
            username_field.send_keys(self.username)
            self.driver_wait(driver, 'css', '#continue')
            password_field = driver.find_element_by_css_selector('#ap_password')
            password_field.send_keys(self.password)
            self.driver_wait(driver, 'css', '#signInSubmit')
            time.sleep(2)
        except NoSuchElementException:
            pass
        driver.get(self.amazonPage)

    def finding_cards(self, driver):
        """Scanning all cards."""
        global auto_buy

        count = 0
        while not self.stop:
            count += 1

            if count >= self.restart_count:
                self.message_sender.send_message("restart driver", self.bot_name)
                count = 0
                driver = self.restart()
                self.login_attempt(self.driver)

            time.sleep(1)
            try:
                find_all_cards = driver.find_elements_by_css_selector(
                    '.style__overlay__2qYgu.ProductGridItem__overlay__1ncmn')
                if len(find_all_cards) <= 0:
                    print("no card found")
                    self.go_home()
                    continue

                print(f"{self.bot_name}: Looking for card in {len(find_all_cards)} options")
                index = 0
                for card in find_all_cards:
                    status = ''
                    try:
                        status = card.parent.find_element_by_css_selector('.Availability__primaryMessage__1bDnl').text
                    except Exception:
                        print('Failed to find status text!')
                        index += 1
                        continue

                    if 'Currently unavailable' not in status and index not in self.blacklisted:
                        # Open listing
                        try:
                            card.click()
                        except selenium.common.exceptions.StaleElementReferenceException as e:
                            print('Failed to click')
                            print(e)
                            self.go_home()
                            index += 1
                            continue

                        self.driver_wait(driver, 'css', '#priceblock_ourprice')  # Ensures page loads & get price
                        price = -1
                        title = '?'
                        try:
                            price = driver.find_element_by_id('priceblock_ourprice')
                            price = float(price.text.replace('$', '').replace(',', ''))
                            title = driver.find_element_by_id('productTitle').text
                        except Exception as e:
                            print('Failed to get price:')
                            print(e)
                            self.go_home()
                            index += 1
                            continue

                        # Title check
                        if not self.check_name(title):
                            print(f'Title {title} did not pass requirements!')
                            self.blacklisted.append(index)
                            self.go_home()
                            index += 1
                            continue

                        if self.min_price <= price <= self.max_price:
                            print(f'Card available! (${str(price)}) "{title}" Attempting to buy..')
                            try:
                                driver.find_element_by_id('buy-now-button')  # Cannot buy for some reason
                            except NoSuchElementException:
                                print('Buy now button was not there, going back')
                                self.go_home()
                                index += 1
                                continue

                            self.driver_wait(driver, 'css', '#buy-now-button')  # Clicks buy now
                            try:
                                asking_to_login = driver.find_element_by_css_selector('#ap_password').is_displayed()
                                if asking_to_login:
                                    print('Attempting to log in..')
                                    driver.find_element_by_css_selector('#ap_password').send_keys(self.password)
                                    self.driver_wait(driver, 'css', '#signInSubmit')
                            except NoSuchElementException:
                                print('Failed to login when prompted..')
                                # go_home()  # Back to search
                                pass

                            # Final price check on buying screen... to be sure
                            price = 0
                            try:
                                price = driver.find_element_by_css_selector('.grand-total-price')
                                price = float(price.text.replace('$', '').replace(',', ''))
                            except Exception as e:
                                print('Failed to get grand total price:')
                                print(e)
                                self.go_home()
                                index += 1
                                continue

                            if self.min_price <= price <= self.max_price:
                                if auto_buy and not self.stop:
                                    self.driver_wait(driver, 'css', '.a-button-input')  # Final Checkout Button!

                                    if self.on_buy_success is not None:
                                        self.on_buy_success()

                                    print(f'Order Placed for {title} Price: ${str(price)}! Notifying and exiting..')

                                    self.message_sender.send_message(
                                        f'Order Placed for "{title}" Price: ${str(price)}!', self.bot_name)

                                    for i in range(3):
                                        print('\a')
                                        time.sleep(1)
                                    time.sleep(1800)
                                    driver.quit()
                                    auto_buy = False  # Safety
                                    return
                                else:
                                    print('Auto buy was not enabled, waiting on purchase screen.')
                                    return
                            else:
                                print(f'Final price did not pass! (${str(price)})')
                                exit()
                        else:
                            self.blacklisted.append(index)
                            print('Price did not pass ($' + str(price) + ')!')
                            self.go_home()

                    index += 1
            except (AttributeError, NoSuchElementException, TimeoutError) as e:
                print('Exception while scanning: ' + e)
                pass
            time_sleep(random.randint(self.min_interval, self.max_interval), driver)

    def go_home(self):
        try:
            self.driver.get(self.amazonPage)
        except WebDriverException:
            print('Failed to load page - internet down?')

    def check_name(self, title):
        passed = True
        for part in self.blacklisted_phrases:
            if part.lower() in title.lower():
                passed = False

        for part in self.item_must_include:
            if part.lower() not in title.lower():
                passed = False

        return passed

    def run(self):
        self.login_attempt(self.driver)
        self.finding_cards(self.driver)

    def restart(self):
        self.driver.quit()
        self.driver = create_driver(self.global_config)
        return self.driver

    def stop_running(self):
        self.driver.quit()
        self.stop = True


if __name__ == '__main__':
    with open("config.json", "r") as f:
        config = json.load(f)
    sender = MessageSender(config)
    bot = AmazonBot(config["global"], config["amazon"][0], sender)
    bot.run()
