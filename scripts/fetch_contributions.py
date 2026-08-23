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
    # Find contribution calendar cells
    # ========================================================

    calendar_days = soup.select(
        "td.ContributionCalendar-day[data-date]"
    )

    if not calendar_days:
        calendar_days = soup.select(
            "td[data-date][data-level]"
        )

    print(f"Calendar cells found: {len(calendar_days)}")

    if not calendar_days:
        raise RuntimeError(
            "Could not find GitHub contribution calendar."
        )

    # ========================================================
    # Parse every contribution day
    # ========================================================

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
        except (TypeError, ValueError):
            level = 0

        # ----------------------------------------------------
        # Find tooltip reference
        #
        # GitHub commonly uses:
        #
        # <td
        #   id="contribution-day-component-..."
        #   data-date="2026-08-23"
        # >
        #
        # <tool-tip for="contribution-day-component-...">
        #   2 contributions on August 23rd.
        # </tool-tip>
        # ----------------------------------------------------

        count = None

        cell_id = cell.get("id")

        if cell_id:

            tooltip = soup.find(
                "tool-tip",
                attrs={
                    "for": cell_id
                }
            )

            if tooltip:

                tooltip_text = tooltip.get_text(
                    " ",
                    strip=True
                )

                count = extract_count(
                    tooltip_text
                )

        # ----------------------------------------------------
        # Fallback:
        # Search all tooltips for the date.
        # ----------------------------------------------------

        if count is None:

            for tooltip in soup.find_all(
                "tool-tip"
            ):

                tooltip_text = tooltip.get_text(
                    " ",
                    strip=True
                )

                if contribution_date in tooltip_text:

                    count = extract_count(
                        tooltip_text
                    )

                    if count is not None:
                        break

        # ----------------------------------------------------
        # Fallback: title attribute
        # ----------------------------------------------------

        if count is None:

            title = cell.get("title")

            if title:

                count = extract_count(
                    title
                )

        # ----------------------------------------------------
        # Fallback: aria-label
        # ----------------------------------------------------

        if count is None:

            aria_label = cell.get(
                "aria-label"
            )

            if aria_label:

                count = extract_count(
                    aria_label
                )

        # ----------------------------------------------------
        # Fallback: child elements
        # ----------------------------------------------------

        if count is None:

            for child in cell.find_all():

                text = child.get_text(
                    " ",
                    strip=True
                )

                if text:

                    count = extract_count(
                        text
                    )

                    if count is not None:
                        break

        # ----------------------------------------------------
        # Zero contribution
        # ----------------------------------------------------

        if count is None:

            # A level of 0 means no contribution.
            #
            # This is safe because GitHub's contribution
            # calendar uses level 0 for empty days.

            if level == 0:
                count = 0

        # ----------------------------------------------------
        # Final fallback
        # ----------------------------------------------------

        if count is None:

            print(
                f"Warning: Could not determine count "
                f"for {contribution_date}"
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
    # Remove duplicates
    # ========================================================

    unique_days = {}

    for day in days:

        unique_days[day["date"]] = day

    days = list(
        unique_days.values()
    )

    # ========================================================
    # Sort oldest → newest
    # ========================================================

    days.sort(
        key=lambda item: item["date"]
    )

    # ========================================================
    # Validate
    # ========================================================

    if not days:

        raise RuntimeError(
            "No contribution days were found."
        )

    # ========================================================
    # Total contributions
    # ========================================================

    total_contributions = sum(
        day["count"]
        for day in days
    )

    # ========================================================
    # Date lookup
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
            monthly_totals.get(
                month,
                0
            )
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
    # Create output directory
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
    print("======================================")
    print(" GitHub Contribution Data")
    print("======================================")

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

    print("======================================")

    # ========================================================
    # Final validation
    # ========================================================

    if total_contributions == 0:

        raise RuntimeError(
            "Contribution data was found, "
            "but all contribution counts are zero."
        )

    print()
    print(
        "SUCCESS: Real GitHub contribution "
        "data extracted successfully."
    )


# ============================================================
# Extract contribution count
# ============================================================

def extract_count(text):
    """
    Extract contribution count from GitHub text.

    Examples:

        "1 contribution on August 20th."
        "5 contributions on August 21st."
        "No contributions on August 22nd."
    """

    if not text:
        return None

    text = text.strip()

    # No contributions
    if re.search(
        r"\bno\s+contributions?\b",
        text,
        re.IGNORECASE,
    ):
        return 0

    # Number of contributions
    match = re.search(
        r"(\d[\d,]*)\s+contributions?",
        text,
        re.IGNORECASE,
    )

    if match:

        return int(
            match.group(1).replace(
                ",",
                ""
            )
        )

    return None


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    fetch_contributions()
