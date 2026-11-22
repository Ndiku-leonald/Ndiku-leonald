"""Scrape the public contributions calendar (no token needed) into data/contributions.json."""
import json
import os
import re
import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "Ndiku-leonald")
URL = f"https://github.com/users/{USER}/contributions"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "contributions.json")


def parse(html: str):
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td[data-date]"):
        tip = tips.get(td.get("id"), "")
        m = re.match(r"([\d,]+)\s+contribution", tip)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level", 0))})
    days.sort(key=lambda d: d["date"])
    return days


def main():
    r = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    r.raise_for_status()
    days = parse(r.text)
    if len(days) < 300:
        sys.exit(f"Only parsed {len(days)} days — GitHub markup may have changed; keeping old data.")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"user": USER, "fetched": date.today().isoformat(), "days": days}, f, indent=1)
    print(f"Saved {len(days)} days, {sum(d['count'] for d in days)} contributions")


if __name__ == "__main__":
    main()
