from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://facultyprofile.vit.edu/department/vit-IT"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_selector("div.card")

    soup = BeautifulSoup(page.content(), "html.parser")

    cards = soup.select("div.card")

    for card in cards:
        name = card.select_one("h5.name-text")
        if name:
            print(name.get_text(strip=True))

    browser.close()
