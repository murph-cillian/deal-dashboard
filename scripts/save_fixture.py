from pathlib import Path

from bs4 import BeautifulSoup

from deal_dashboard.fetching import RequestsFetcher

URL = "https://rorystravelclub.com/pages/rtc-leinster-offers"
OUT = Path("tests/fixtures")

html = RequestsFetcher().fetch(URL)
OUT.mkdir(parents=True, exist_ok=True)

# The whole page, for reference and for "many cards" tests.
(OUT / "rorys_leinster_page.html").write_text(html, encoding="utf-8")

# Is the card data in the raw HTML, or injected by JavaScript?
print("data-hotel in raw HTML:", "data-hotel" in html)

# One card, for the golden test.
soup = BeautifulSoup(html, "html.parser")
card = soup.select_one('div[data-hotel*="spencer"]')
if card is None:
    print("Spencer card not found")
else:
    (OUT / "rorys_card.html").write_text(str(card), encoding="utf-8")
