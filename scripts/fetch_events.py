#!/usr/bin/env python3
import argparse
import dataclasses
import json
import re
from datetime import datetime
from typing import Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

DATE_PATTERNS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
]


@dataclasses.dataclass
class Event:
    name: str
    location: str
    race_date: str
    registration_deadline: str
    registration_open: bool
    website: str
    source: str


def normalize_date(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("年", "-").replace("月", "-").replace("日", "")
    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return value


def guess_open_status(text: str) -> bool:
    text = text.strip()
    return any(keyword in text for keyword in ("報名中", "開放", "可報名", "立即報名"))


def extract_generic(url: str, source: str, selectors: dict) -> List[Event]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(selectors["item"])
    events: List[Event] = []

    for item in items:
        name_el = item.select_one(selectors["name"])
        date_el = item.select_one(selectors["race_date"])
        location_el = item.select_one(selectors["location"])
        deadline_el = item.select_one(selectors["deadline"])
        status_el = item.select_one(selectors["status"])
        link_el = item.select_one(selectors["link"])

        if not (name_el and date_el and location_el and link_el):
            continue

        name = name_el.get_text(strip=True)
        race_date = normalize_date(date_el.get_text(strip=True))
        location = location_el.get_text(strip=True)
        registration_deadline = (
            normalize_date(deadline_el.get_text(strip=True)) if deadline_el else ""
        )
        status_text = status_el.get_text(strip=True) if status_el else ""
        registration_open = guess_open_status(status_text)
        website = link_el.get("href", "")
        if website and website.startswith("/"):
            website = f"{url.rstrip('/')}{website}"

        events.append(
            Event(
                name=name,
                location=location,
                race_date=race_date,
                registration_deadline=registration_deadline,
                registration_open=registration_open,
                website=website,
                source=source,
            )
        )

    return events


def fetch_irunner() -> List[Event]:
    return extract_generic(
        url="https://www.irunner.com.tw/",
        source="iRunner",
        selectors={
            "item": ".race_list li",
            "name": ".race_name",
            "race_date": ".race_date",
            "location": ".race_city",
            "deadline": ".race_signup",
            "status": ".race_status",
            "link": "a",
        },
    )


def fetch_running_biji() -> List[Event]:
    return extract_generic(
        url="https://www.running.biji.co/index.php?q=competition",
        source="跑步筆記",
        selectors={
            "item": ".competition-list .item",
            "name": ".title",
            "race_date": ".date",
            "location": ".location",
            "deadline": ".signup",
            "status": ".status",
            "link": "a",
        },
    )


def fetch_sponet() -> List[Event]:
    return extract_generic(
        url="https://www.sponet.tw/",
        source="SPORTNET",
        selectors={
            "item": ".event-list .event-item",
            "name": ".event-title",
            "race_date": ".event-date",
            "location": ".event-location",
            "deadline": ".event-deadline",
            "status": ".event-status",
            "link": "a",
        },
    )


def dedupe_events(events: Iterable[Event]) -> List[Event]:
    seen = set()
    output = []
    for event in events:
        key = (event.name, event.race_date, event.location)
        if key in seen:
            continue
        seen.add(key)
        output.append(event)
    return output


def load_fallback_events(path: str) -> List[Event]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [
        Event(
            name=item["name"],
            location=item["location"],
            race_date=item["raceDate"],
            registration_deadline=item["registrationDeadline"],
            registration_open=item["registrationOpen"],
            website=item["website"],
            source=item["source"],
        )
        for item in data["events"]
    ]


def write_events(path: str, events: List[Event]) -> None:
    payload = {
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "events": [
            {
                "name": event.name,
                "location": event.location,
                "raceDate": event.race_date,
                "registrationDeadline": event.registration_deadline,
                "registrationOpen": event.registration_open,
                "website": event.website,
                "source": event.source,
            }
            for event in events
        ],
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="爬取台灣馬拉松報名網站並輸出成 JSON。"
    )
    parser.add_argument(
        "--output",
        default="data/events.json",
        help="輸出 JSON 路徑 (預設: data/events.json)",
    )
    parser.add_argument(
        "--fallback",
        default="data/events.json",
        help="若抓取失敗則讀取既有 JSON 作為替代",
    )
    args = parser.parse_args()

    events: List[Event] = []
    for fetcher in (fetch_irunner, fetch_running_biji, fetch_sponet):
        try:
            events.extend(fetcher())
        except requests.RequestException as error:
            print(f"警告: 無法抓取 {fetcher.__name__}: {error}")

    if not events:
        print("未取得任何賽事，改用 fallback 資料。")
        events = load_fallback_events(args.fallback)

    events = dedupe_events(events)
    write_events(args.output, events)
    print(f"已輸出 {len(events)} 場賽事至 {args.output}")


if __name__ == "__main__":
    main()
