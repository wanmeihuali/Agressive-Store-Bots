import bs4
import time
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, \
    ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils import create_driver, time_sleep
from MessageSender import MessageSender
import json
import random


# ---------------------------------------------Please Read--------------------------------------------------------------

# Updated: 4/12/2021

# Hello everyone! Welcome to my Best Buy script.
# Let's go over the checklist for the script to run properly.
#   1. Product URL
#   2. Firefox Profile
#   3. Credit Card CVV Number
#   4. Twilio Account

# This Script only accepts Product URL's that look like this. I hope you see the difference between page examples.

# Example 1 - Nvidia RTX 3080:
# url = 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'
# Example 2 - PS5:
# https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149
# Example 3 - Ryzen 5600x:
# https://www.bestbuy.com/site/amd-ryzen-5-5600x-4th-gen-6-core-12-threads-unlocked-desktop-processor-with-wraith-stealth-cooler/6438943.p?skuId=6438943

# This Script does not accept Product URL's that look like this.
# https://www.bestbuy.com/site/searchpage.jsp?st=rtx+3080&_dyncharset=UTF-8&_dynSessConf=&id=pcat17071&type=page&sc=Global&cp=1&nrp=&sp=&qp=&list=n&af=true&iht=y&usc=All+Categories&ks=960&keys=keys

# Highly Recommend To set up Twilio Account to receive text messages. So if bot doesn't work you'll at least get a phone
# text message with the url link. You can click the link and try manually purchasing on your phone.

# Twilio is free. Get it Here.
# www.twilio.com/referral/BgLBXx

# -----------------------------------------------Steps To Complete------------------------------------------------------

# Test Link 1 - Ryzen 5800x seems to be available quite often. It is the best URL to try out preorder script.
# To actually avoid buying CPU, you can comment out Line 220. Uncomment the line when you are done testing.
# https://www.bestbuy.com/site/amd-ryzen-7-5800x-4th-gen-8-core-16-threads-unlocked-desktop-processor-without-cooler/6439000.p?skuId=6439000

# Test Link 2 (cheap HDMI cable) - https://www.bestbuy.com/site/dynex-6-hdmi-cable-black/6405508.p?skuId=6405508
# *Warning* - Script will try to checkout the HDMI cable twice since this is how the Bestbuy preorder script works
# Best buy makes us click the add to cart button twice to enter Queue System. 
# Don't worry about script buying two graphics cards though. The script will only buy one.
# As well, Best buy won't let you check out more than 1 item.
# To actually avoid buying HDMI cable, you can comment out Line 220. Uncomment the line when you are done testing.

# 1. Product URL
#url = 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440'
#url = 'https://www.bestbuy.com/site/amd-ryzen-5-5600x-4th-gen-6-core-12-threads-unlocked-desktop-processor-with-wraith-stealth-cooler/6438943.p?skuId=6438943'
# url = 'https://www.bestbuy.com/site/amd-ryzen-7-5800x-4th-gen-8-core-16-threads-unlocked-desktop-processor-without-cooler/6439000.p?skuId=6439000'

# ----------------------------------------------------------------------------------------------------------------------

class BestbuyBot:
    def __init__(self, global_config, bestbuy_config, message_sender, on_buy_success=None):
        self.url = bestbuy_config["url"]

        # 3. credit card CVV Number
        self.CVV = global_config["CVV"]
        self.auto_buy = global_config["auto_buy"]

        self.message_sender = message_sender
        self.on_buy_success = on_buy_success
        self.min_interval = bestbuy_config["min_interval"]
        self.max_interval = bestbuy_config["max_interval"]
        self.stop = False
        self.driver = create_driver(global_config)

    def extract_page(self, ):
        html = self.driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        return soup


    def driver_click(self, driver, find_type, selector):
        """Driver Wait and Click Settings."""
        while True:
            if find_type == 'css':
                try:
                    driver.find_element_by_css_selector(selector).click()
                    break
                except NoSuchElementException:
                    driver.implicitly_wait(1)
            elif find_type == 'name':
                try:
                    driver.find_element_by_name(selector).click()
                    break
                except NoSuchElementException:
                    driver.implicitly_wait(1)
            elif find_type == 'xpath':
                try:
                    driver.find_element_by_xpath(f"//*[@class='{selector}']").click()
                    break
                except NoSuchElementException:
                    driver.implicitly_wait(1)


    def searching_for_card(self, driver):
        """Scanning for card."""
        driver.get(self.url)
        while not self.stop:
            soup = self.extract_page()
            wait = WebDriverWait(driver, 15)
            wait2 = WebDriverWait(driver, 5)

            try:
                add_to_cart_button = soup.find('button', {
                    'class': 'btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button'})

                if add_to_cart_button:
                    print(f'Add To Cart Button Found!')

                    # Queue System Logic.
                    try:
                        # Entering Queue: Clicking "add to cart" 2nd time to enter queue.
                        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart-button")))
                        self.driver_click(driver, 'css', '.add-to-cart-button')
                        print("Clicked Add to Cart Button. Now sending message to your phone.")
                        print("You are now added to Best Buy's Queue System. Page will be refreshing. Please be patient.")

                        # Sleep timer is here to give Please Wait Button to appear. Please don't edit this.
                        time.sleep(5)
                        driver.refresh()
                        time.sleep(5)
                    except (NoSuchElementException, TimeoutException) as error:
                        print(f'Queue System Error: ${error}')

                    # Sending Text Message To let you know you are in the queue system.
                    self.message_sender.send_message(f'Your In Queue System on Bestbuy! {self.url}')

                    # In queue, just waiting for "add to cart" button to turn clickable again.
                    # page refresh every 15 seconds until Add to Cart button reappears.
                    while True:
                        try:
                            add_to_cart = driver.find_element_by_css_selector(".add-to-cart-button")
                            please_wait_enabled = add_to_cart.get_attribute('aria-describedby')

                            if please_wait_enabled:
                                driver.refresh()
                                time.sleep(15)
                            else:  # When Add to Cart appears. This will click button.
                                print("Add To Cart Button Clicked A Second Time.")
                                wait2.until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-button")))
                                time.sleep(2)
                                self.driver_click(driver, 'css', '.add-to-cart-button')
                                time.sleep(2)
                                break
                        except(NoSuchElementException, TimeoutException) as error:
                            print(f'Queue System Refresh Error: ${error}')

                    # Going To Cart Process.
                    driver.get('https://www.bestbuy.com/cart')

                    # Checking if item is still in cart.
                    try:
                        wait.until(
                            EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary']")))
                        time.sleep(1)
                        self.driver_click(driver, 'xpath', 'btn btn-lg btn-block btn-primary')
                        print("Item Is Still In Cart.")
                    except (NoSuchElementException, TimeoutException):
                        print("Item is not in cart anymore. Retrying..")
                        time_sleep(3, driver)
                        self.searching_for_card(driver)

                    # Logging Into Account.
                    print("Attempting to Login. Firefox should remember your login info to auto login.")

                    # Click Shipping Option. (if available)
                    try:
                        wait2.until(EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']")))
                        time.sleep(2)
                        shipping_class = driver.find_element_by_xpath("//*[@class='ispu-card__switch']")
                        shipping_class.click()
                        print("Clicking Shipping Option.")
                    except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as error:
                        print(f'shipping error: {error}')

                    # Trying CVV
                    try:
                        print("\nTrying CVV Number.\n")
                        wait2.until(EC.presence_of_element_located((By.ID, "credit-card-cvv")))
                        time.sleep(1)
                        security_code = driver.find_element_by_id("credit-card-cvv")
                        time.sleep(1)
                        security_code.send_keys(self.CVV)
                    except (NoSuchElementException, TimeoutException):
                        pass

                    if self.auto_buy and not self.stop:
                        # Final Checkout.
                        try:
                            wait2.until(EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']")))
                            print("clicked checkout")
                            # comment the line down below to avoid buying when testing bot. vv
                            self.driver_click(driver, 'xpath', 'btn btn-lg btn-block btn-primary button__fast-track')
                        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
                            print("Could Not Complete Checkout.")

                        # Completed Checkout.
                        print('Order Placed!')

                        self.stop = True
                        if self.on_buy_success is not None:
                            self.on_buy_success()

                        # Sending Text Message To let you know you are in the queue system.
                        self.message_sender.send_message(f'Order Placed')

                    time.sleep(1800)
                    driver.quit()

            except (NoSuchElementException, TimeoutException) as error:
                print(f'error is: {error}')

            time_sleep(random.randint(self.min_interval, self.max_interval), driver)

    def run(self):
        self.searching_for_card(self.driver)

    def stop_running(self):
        self.stop = True


if __name__ == '__main__':
    with open("config.json", "r") as f:
        config = json.load(f)
    sender = MessageSender(config)
    bot = BestbuyBot(config["global"], config["bestbuy"][0], sender)
    bot.run()
