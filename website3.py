from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import unicodedata


def table_format(soup):
    faculty = []
    table = soup.find("table")
    rows = table.find_all("tr")[1:]

    for row in rows:
        if row.find("th"):
            continue

        cols = row.find_all("td")
        if not cols:
            continue

        if not cols[0].get_text(strip=True).isdigit():
            continue

        name = cols[1].get_text(strip=True)
        name = unicodedata.normalize("NFKD", name)
        faculty.append(name)

    return faculty


def card_format(soup):
    faculty = []
    cards = soup.select("div.card")

    for card in cards:
        name = card.select_one("h5.name-text")
        if name:
            faculty.append(name.get_text(strip=True))

    return faculty


def faculty_details(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        browser.close()

        if soup.find("table"):
            return table_format(soup)

        elif soup.find("div", class_="card"):
            return card_format(soup)

        else:
            return []
