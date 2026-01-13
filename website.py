from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import unicodedata
import sys

sys.stdout.reconfigure(encoding='utf-8')


def table_format(soup):
    table = soup.find("table")
    rows=table.find_all('tr')[1:]
    i=1
    for row in rows:
        if row.find("th"):
            continue
        cols = row.find_all("td")

        if not cols:
            continue 
        if not cols[0].get_text(strip=True).isdigit():
            continue
        name = cols[1].get_text(strip=True)
        name = cols[1].get_text(strip=True)
        name = unicodedata.normalize("NFKD", name)
        print(i,name)
        i+=1

def card_format(soup):
    cards = soup.select("div.card")
    i=1
    for card in cards:
        name = card.select_one("h5.name-text")
        if name:
            print(i,name.get_text(strip=True))
            i+=1

def faculty_details(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # visible browser
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_selector("div.card", timeout=5000)
        except:
            try:
                page.wait_for_selector("table", timeout=5000)
            except:
                pass

        html = page.content()
        soup=BeautifulSoup(html,"html.parser")
        
        if soup.find("table"):
            table_format(soup)

        elif soup.find("div", class_="card"):
            card_format(soup)

        else:
            print("This page format is not supported")

        browser.close()

url=input("enter input")
faculty_details(url)