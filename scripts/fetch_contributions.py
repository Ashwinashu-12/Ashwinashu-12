import json
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ============================================================
# GitHub username
# ============================================================

USERNAME = "Ashwinashu-12"

URL = f"https://github.com/users/{USERNAME}/contributions"

OUTPUT = Path("data/contributions.json")


# ============================================================
# Fetch contribution data
# ============================================================

def fetch_contributions():
    print(f"Fetching contributions for {USERNAME}...")

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

    # GitHub's contribution calendar uses SVG rect elements.
    for rect in soup.select("rect[data-date]"):

        contribution_date = rect.get("data-date")
        count = rect.get("data-count", "0")
        level = rect.get("data-level", "0")

        if not contribution_date:
            continue

        try:
            count = int(count)
        except ValueError:
            count = 0

        try:
            level = int(level)
        except ValueError:
            level = 0

        days.append(
            {
                "date": contribution_date,
                "count": count,
                "level": level,
            }
        )

    if not days:
        raise RuntimeError(
            "No contribution data found. "
            "GitHub may have changed its contribution page structure."
        )

    # Sort from oldest → newest
    days.sort(key=lambda item: item["date"])

    # ========================================================
    # Total contributions
    # ========================================================

    total_contributions = sum(
        day["count"] for day in days
    )

    # ========================================================
    # Create date lookup
    # ========================================================

    day_map = {
        date.fromisoformat(day["date"]): day["count"]
        for day in days
    }

    latest_date = max(day_map)

    # ========================================================
    # Current streak
    # ========================================================

    current_streak = 0
    current_date = latest_date

    while (
        current_date in day_map
        and day_map[current_date] > 0
    ):
        current_streak += 1
        current_date -= timedelta(days=1)

    # ========================================================
    # Longest streak
    # ========================================================

    longest_streak = 0
    streak = 0

    for day in days:

        if day["count"] > 0:
            streak += 1
            longest_streak = max(
                longest_streak,
                streak
            )
        else:
            streak = 0

    # ========================================================
    # Best contribution day
    # ========================================================

    best_day = max(
        days,
        key=lambda item: item["count"]
    )

    # ========================================================
    # Monthly totals
    # ========================================================

    monthly_totals = {}

    for day in days:

        month = day["date"][:7]

        monthly_totals[month] = (
            monthly_totals.get(month, 0)
            + day["count"]
        )

    # ========================================================
    # Final JSON
    # ========================================================

    data = {
        "username": USERNAME,

        "total_contributions": total_contributions,

        "current_streak": current_streak,

        "longest_streak": longest_streak,

        "best_day": best_day,

        "monthly_totals": monthly_totals,

        "days": days,
    }

    # Create data directory automatically.
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save JSON.
    OUTPUT.write_text(
        json.dumps(
            data,
            indent=2
        ),
        encoding="utf-8"
    )

    # ========================================================
    # Console output
    # ========================================================

    print()
    print("======================================")
    print(" GitHub Contribution Data")
    print("======================================")
    print(f"Username:            {USERNAME}")
    print(f"Days found:          {len(days)}")
    print(f"Total contributions: {total_contributions}")
    print(f"Current streak:      {current_streak}")
    print(f"Longest streak:      {longest_streak}")
    print(
        f"Best day:            "
        f"{best_day['date']} "
        f"({best_day['count']} contributions)"
    )
    print(f"Saved to:            {OUTPUT}")
    print("======================================")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    fetch_contributions()
