import os
from pathlib import Path

from sys import platform
import configparser

from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import FirefoxProfile
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import sys
import time


def get_profile_path():
    if platform == 'linux' or platform == 'linux2':
        profile_path = Path(os.getenv('HOME')) / '.mozilla' / 'firefox'
    elif platform == 'darwin':
        profile_path = Path(os.getenv('HOME')) / \
                       'Library' / 'Application Support' / 'Firefox'
    elif platform == 'win32':
        profile_path = Path(os.getenv('APPDATA')) / 'Mozilla' / 'Firefox'
    if not profile_path.exists():
        raise FileNotFoundError("Mozilla profile doesn't exist and/or can't be located on this machine.")
    return profile_path


def get_default_profile(profile_path):
    mozilla_profile_ini = profile_path / 'profiles.ini'
    profile = configparser.ConfigParser()
    profile.read(mozilla_profile_ini)
    return profile.get('Profile0', 'Path')


def prepare_sniper_profile(default_profile_path):
    profile = FirefoxProfile(default_profile_path.resolve())
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    return profile


def create_driver(bot_config):
    geckodriver_path = bot_config["geckodriver_path"]
    if geckodriver_path is None:
        geckodriver_path = GeckoDriverManager.install()
        bot_config["geckodriver_path"] = geckodriver_path

    profile_path = get_profile_path()
    default_profile = get_default_profile(profile_path)
    print(f'Launching Firefox using default profile: {default_profile}')
    profile = prepare_sniper_profile(profile_path / default_profile)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=geckodriver_path)
    return driver


def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')
    try:
        driver.refresh()
    except WebDriverException:
        print('Error while refreshing - internet down?')
    sys.stdout.write('\r')
    sys.stdout.write('Page refreshed\n')
    sys.stdout.flush()