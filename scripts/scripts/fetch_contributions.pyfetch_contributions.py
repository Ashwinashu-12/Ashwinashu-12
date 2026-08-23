import json
import re
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = "Ashwinashu-12"

URL = f"https://github.com/users/{USERNAME}/contributions"

OUTPUT = Path("data/contributions.json")


def fetch_contributions():
    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    days = []

    # GitHub renders contribution days as SVG <rect> elements.
    for rect in soup.select("rect[data-date]"):
        day = rect.get("data-date")
        count = rect.get("data-count")
        level = rect.get("data-level", "0")

        if not day:
            continue

        try:
            count = int(count or 0)
        except ValueError:
            count = 0

        try:
            level = int(level or 0)
        except ValueError:
            level = 0

        days.append({
            "date": day,
            "count": count,
            "level": level,
        })

    if not days:
        raise RuntimeError(
            "No contribution data was found. "
            "GitHub may have changed the contribution page structure."
        )

    # Sort chronologically.
    days.sort(key=lambda x: x["date"])

    total = sum(day["count"] for day in days)

    # Calculate current streak.
    current_streak = 0
    cursor = date.today()

    day_map = {
        date.fromisoformat(day["date"]): day["count"]
        for day in days
    }

    # GitHub's contribution timestamps use UTC, so use the latest
    # available calendar day rather than relying only on local time.
    latest_date = max(day_map)

    cursor = latest_date

    while cursor in day_map and day_map[cursor] > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    # Calculate longest streak.
    longest_streak = 0
    streak = 0

    for day in days:
        if day["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    # Best contribution day.
    best_day = max(days, key=lambda x: x["count"])

    # Monthly totals.
    monthly_totals = {}

    for day in days:
        month = day["date"][:7]
        monthly_totals[month] = (
            monthly_totals.get(month, 0) + day["count"]
        )

    data = {
        "username": USERNAME,
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
        "days": days,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"Username: {USERNAME}")
    print(f"Days found: {len(days)}")
    print(f"Total contributions: {total}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")
    print(f"Best day: {best_day['date']} ({best_day['count']} contributions)")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    fetch_contributions()
