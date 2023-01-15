import atexit
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By


def get_browser(headless: bool):
    chrome_options = webdriver.chrome.options.Options()  # type: ignore
    if headless:
        chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(options=chrome_options)

    def kill_browser():
        print("quitting browser...")
        browser.quit()
        print("done quitting browser")

    atexit.register(kill_browser)
    return browser


def parse_vital_busyness(browser) -> int:
    elt = browser.find_element(By.CSS_SELECTOR, "#currocc")
    txt = elt.text
    return int(txt)


def get_vital_busyness(browser):
    browser.get("https://www.vitalclimbinggym.com/brooklyn")
    # TODO: something better?
    time.sleep(1)
    return parse_vital_busyness(browser)


def vital_busyness_time_series(browser, interval_seconds):
    while True:
        yield (datetime.now(), get_vital_busyness(browser))
        time.sleep(interval_seconds)


def log_vital_busyness_to_csv(browser, interval_seconds):
    while True:
        print("starting loop")
        try:
            for t, occ in vital_busyness_time_series(browser, interval_seconds):
                with Path("busyness.csv").open("a") as f:
                    f.write(f"{t.isoformat()},{occ}\n")
                print(f"{t:%H:%M:%S} >> {occ}")
        except Exception as e:
            print(f"got exn: {e!r}")
            print("quitting browser..")
            browser.quit()
            print("restarting a new one..")
            browser = get_browser(headless=True)
            print("snoozing a bit extra, 3s")
            time.sleep(3)


def main():
    b = get_browser(headless=False)
    log_vital_busyness_to_csv(b, 15)


if __name__ == "__main__":
    main()
