""" Author:       hraleig@amazon.com
    Versions:     python v. 3.x

    Includes all logic for interacting with web pages, used by tests.py and test_objects.py
    Enables sign in to weg pages, gathering status codes and response times, and running curl commands.
"""

import subprocess
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


def chrome_driver():
    """Configure and create headless Google Chrome browser driver

        :return: headless chrome webdriver
    """

    options = Options()
    options.add_argument("--headless")
    options.add_argument("window-size=1400,1500")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(ChromeDriverManager().install(), options=options)


def http_status(prereq, link):
    """Retrieve http response from page directly

        :param prereq: command to perform before getting http status
        :param link: url for page being tested as String
        :return: http status code as String
    """
    cmd = prereq + "curl -s -o /dev/null -w \"%{http_code}\" " + link
    ret = curl_cmd(cmd)
    ret = ret.replace('b', '')
    ret = ret.replace('\'', '')

    return ret


def curl_http(command):
    """Retrieve http response from output of curl command

        :param command: curl command being run
        :return: http status code as String
    """
    ret = curl_cmd(command)
    return parse_http_sts(ret)


def curl_cmd(command):
    """Perform command in shell subprocess

        :param command: command being run
        :return: output from command
    """
    try:
        ret = subprocess.check_output(command, shell=True)
    except Exception as e:
        print(e)
        return str(e)
    return str(ret)


def parse_http_sts(ret):
    """Parse http status from text

        :param ret: text output from terminal command
        :return: http status code as String
    """
    token = "HTTP/1.1 "
    i = ret.find(token)
    start = i + len(token)

    return ret[int(start):int(start + 3)]


def response(driver):
    """Record page response time

        :param driver: webdriver for Chrome page
        :return: front, back end response times in milliseconds as Strings
    """

    nav_start = driver.execute_script("return window.performance.timing.navigationStart")
    resp_start = driver.execute_script("return window.performance.timing.responseStart")
    dom_complete = driver.execute_script("return window.performance.timing.domComplete")

    # compute front end and back end response times
    front = resp_start - nav_start
    back = dom_complete - resp_start

    return str(front), str(back)


def log_in(driver, user, passw, link, btn_path, title):
    """Enter username and password then submit to log in

        :param driver: webdriver for Chrome page
        :param user: username as String
        :param passw: password as String
        :param link: url for page being tested as String
        :param btn_path: xpath to submit button
        :param title: expected page title upon successful sign in
        :return: success String tuple if log in completed, failure description tuple String otherwise
    """
    try:
        # post username and password data
        driver.find_element_by_xpath("//input[@name='username']").send_keys(user)
        driver.find_element_by_xpath("//input[@name='password']").send_keys(passw)

        # click sign in button and wait for page update
        driver.find_element_by_xpath(btn_path).click()
    except NoSuchElementException:
        return 'FAILURE', 'Unable to access page elements'

    try:
        WebDriverWait(driver, 20).until(ec.url_changes(link))
        WebDriverWait(driver, 20).until(ec.title_is(title))
    except TimeoutException as e:
        print("Timeout occurred (" + e + ") while attempting to sign in to " + driver.current_url)
        if "Sign In" in driver.title or "invalid user" in driver.page_source.lower():
            return 'FAILURE', 'Incorrect username or password'
        else:
            return 'FAILURE', 'Sign in attempt timed out'

    return 'SUCCESS', 'Sign in complete'
