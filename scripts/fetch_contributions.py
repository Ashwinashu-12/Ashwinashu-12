import json
import re
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
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html",
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    days = []

    # ========================================================
    # Current GitHub contribution calendar
    #
    # GitHub now uses:
    #
    # <td data-date="YYYY-MM-DD" data-level="0-4">
    #
    # instead of the old:
    #
    # <rect data-date="..." data-count="...">
    #
    # The contribution count is available through the
    # accessibility/tooltip information associated with the day.
    # ========================================================

    calendar_days = soup.select(
        "td.ContributionCalendar-day[data-date]"
    )

    # Fallback in case GitHub changes the class name again.
    if not calendar_days:
        calendar_days = soup.select(
            "[data-date][data-level]"
        )

    print(f"Calendar cells found: {len(calendar_days)}")

    for cell in calendar_days:

        contribution_date = cell.get("data-date")

        if not contribution_date:
            continue

        # ----------------------------------------------------
        # Contribution level
        # ----------------------------------------------------

        try:
            level = int(
                cell.get("data-level", "0")
            )
        except ValueError:
            level = 0

        # ----------------------------------------------------
        # Find contribution count
        # ----------------------------------------------------

        count = None

        # Possible direct attributes.
        for attribute in (
            "data-count",
            "data-contribution-count",
        ):
            value = cell.get(attribute)

            if value is not None:
                try:
                    count = int(value)
                    break
                except ValueError:
                    pass

        # ----------------------------------------------------
        # Look for GitHub's tooltip/custom element.
        # ----------------------------------------------------

        if count is None:

            tooltip = cell.find(
                "tool-tip"
            )

            if tooltip:

                tooltip_text = tooltip.get_text(
                    " ",
                    strip=True
                )

                match = re.search(
                    r"(\d[\d,]*)\s+contribution",
                    tooltip_text,
                    re.IGNORECASE,
                )

                if match:
                    count = int(
                        match.group(1).replace(",", "")
                    )

        # ----------------------------------------------------
        # Look through aria-label/title attributes.
        # ----------------------------------------------------

        if count is None:

            possible_texts = []

            for attribute in (
                "aria-label",
                "title",
            ):
                value = cell.get(attribute)

                if value:
                    possible_texts.append(value)

            # Also inspect children.
            for child in cell.find_all(
                attrs={
                    "aria-label": True
                }
            ):
                possible_texts.append(
                    child.get("aria-label")
                )

            for child in cell.find_all(
                attrs={
                    "title": True
                }
            ):
                possible_texts.append(
                    child.get("title")
                )

            for text in possible_texts:

                match = re.search(
                    r"(\d[\d,]*)\s+contribution",
                    text,
                    re.IGNORECASE,
                )

                if match:
                    count = int(
                        match.group(1).replace(",", "")
                    )
                    break

        # ----------------------------------------------------
        # Look at all text inside the cell.
        # ----------------------------------------------------

        if count is None:

            cell_text = cell.get_text(
                " ",
                strip=True
            )

            match = re.search(
                r"(\d[\d,]*)\s+contribution",
                cell_text,
                re.IGNORECASE,
            )

            if match:
                count = int(
                    match.group(1).replace(",", "")
                )

        # ----------------------------------------------------
        # Zero contribution days
        # ----------------------------------------------------

        if count is None:

            # GitHub commonly represents zero contribution
            # days explicitly in accessibility text.

            combined_text = " ".join(
                [
                    str(cell.get("aria-label", "")),
                    str(cell.get("title", "")),
                    cell.get_text(" ", strip=True),
                ]
            )

            if re.search(
                r"no contributions?",
                combined_text,
                re.IGNORECASE,
            ):
                count = 0

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        if count is None:

            print(
                f"Warning: Could not determine count "
                f"for {contribution_date}; using 0."
            )

            count = 0

        days.append(
            {
                "date": contribution_date,
                "count": count,
                "level": level,
            }
        )

    # ========================================================
    # Validate data
    # ========================================================

    if not days:

        raise RuntimeError(
            "No contribution data found. "
            "GitHub may have changed its contribution "
            "calendar structure."
        )

    # Remove duplicate dates.
    unique_days = {}

    for day in days:
        unique_days[day["date"]] = day

    days = list(unique_days.values())

    # Sort oldest → newest.
    days.sort(
        key=lambda item: item["date"]
    )

    # ========================================================
    # Total contributions
    # ========================================================

    total_contributions = sum(
        day["count"]
        for day in days
    )

    # ========================================================
    # Create date lookup
    # ========================================================

    day_map = {
        date.fromisoformat(
            day["date"]
        ): day["count"]
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

        current_date -= timedelta(
            days=1
        )

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

        "total_contributions": (
            total_contributions
        ),

        "current_streak": (
            current_streak
        ),

        "longest_streak": (
            longest_streak
        ),

        "best_day": best_day,

        "monthly_totals": (
            monthly_totals
        ),

        "days": days,
    }

    # ========================================================
    # Create data directory
    # ========================================================

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # Save JSON
    # ========================================================

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
    print(
        "======================================"
    )
    print(
        " GitHub Contribution Data"
    )
    print(
        "======================================"
    )

    print(
        f"Username:            {USERNAME}"
    )

    print(
        f"Days found:          {len(days)}"
    )

    print(
        f"Total contributions: "
        f"{total_contributions}"
    )

    print(
        f"Current streak:      "
        f"{current_streak}"
    )

    print(
        f"Longest streak:      "
        f"{longest_streak}"
    )

    print(
        f"Best day:            "
        f"{best_day['date']} "
        f"({best_day['count']} contributions)"
    )

    print(
        f"Saved to:            {OUTPUT}"
    )

    print(
        "======================================"
    )

    # ========================================================
    # Important validation
    # ========================================================

    if total_contributions == 0:

        raise RuntimeError(
            "Contribution cells were found, "
            "but all contribution counts are zero. "
            "GitHub's contribution count markup may "
            "have changed again."
        )

    print()
    print(
        "SUCCESS: Contribution counts were "
        "successfully extracted."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    fetch_contributions()
