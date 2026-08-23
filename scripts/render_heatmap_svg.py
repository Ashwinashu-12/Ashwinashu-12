import json
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


# ============================================================
# Files
# ============================================================

INPUT = Path("data/contributions.json")
OUTPUT = Path("contrib-heatmap.svg")


# ============================================================
# Heatmap settings
# ============================================================

WIDTH = 860
HEIGHT = 190

LEFT = 45
TOP = 45

CELL = 12
GAP = 3

# GitHub-style contribution colors.
PALETTE = [
    "#161b22",  # 0 contributions
    "#0e4429",  # level 1
    "#006d32",  # level 2
    "#26a641",  # level 3
    "#39d353",  # level 4
]


# ============================================================
# Load contribution data
# ============================================================

def load_data():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"{INPUT} was not found. "
            "Run fetch_contributions.py first."
        )

    with INPUT.open("r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# Build contribution lookup
# ============================================================

def build_day_map(days):
    return {
        day["date"]: day
        for day in days
    }


# ============================================================
# Convert contribution count to visual level
# ============================================================

def get_level(day):
    if day is None:
        return 0

    level = day.get("level", 0)

    try:
        level = int(level)
    except (TypeError, ValueError):
        level = 0

    # GitHub normally provides levels 0–4.
    return max(0, min(4, level))


# ============================================================
# Build the last 53 weeks
# ============================================================

def build_calendar(day_map):
    today = date.today()

    # Find the Sunday starting the final displayed week.
    days_since_sunday = (today.weekday() + 1) % 7

    end_sunday = today - (
        __import__("datetime").timedelta(days=days_since_sunday)
    )

    start_sunday = end_sunday - (
        __import__("datetime").timedelta(days=52 * 7)
    )

    calendar = []

    for week in range(53):

        week_data = []

        for weekday in range(7):

            current = (
                start_sunday
                + __import__("datetime").timedelta(
                    days=week * 7 + weekday
                )
            )

            key = current.isoformat()

            week_data.append(
                (
                    current,
                    day_map.get(key)
                )
            )

        calendar.append(week_data)

    return calendar


# ============================================================
# Create heatmap SVG
# ============================================================

def create_svg(data):

    username = data.get(
        "username",
        "Ashwinashu-12"
    )

    total = data.get(
        "total_contributions",
        0
    )

    current_streak = data.get(
        "current_streak",
        0
    )

    longest_streak = data.get(
        "longest_streak",
        0
    )

    best_day = data.get(
        "best_day",
        {}
    )

    best_count = best_day.get(
        "count",
        0
    )

    day_map = build_day_map(
        data.get("days", [])
    )

    calendar = build_calendar(day_map)

    svg = []

    # ========================================================
    # SVG header
    # ========================================================

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}"
role="img"
aria-label="GitHub contribution heatmap for {escape(username)}">'''
    )

    # ========================================================
    # Definitions
    # ========================================================

    svg.append(
        '''
<defs>

<style>

.title {
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Arial, sans-serif;
    font-size: 16px;
    font-weight: 600;
    fill: #c9d1d9;
}

.subtitle {
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Arial, sans-serif;
    font-size: 11px;
    fill: #8b949e;
}

.footer {
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Arial, sans-serif;
    font-size: 11px;
    fill: #8b949e;
}

.legend {
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Arial, sans-serif;
    font-size: 10px;
    fill: #8b949e;
}

.day {
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Arial, sans-serif;
    font-size: 9px;
    fill: #8b949e;
}

.cell {
    opacity: 0;
    transform-box: fill-box;
    transform-origin: center;
    animation: reveal 0.45s ease-out forwards;
}

@keyframes reveal {
    from {
        opacity: 0;
        transform: translateY(-8px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

</style>

</defs>
'''
    )

    # ========================================================
    # Background
    # ========================================================

    svg.append(
        f'''
<rect
    x="0"
    y="0"
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="14"
    fill="#0d1117"
    stroke="#30363d"
/>
'''
    )

    # ========================================================
    # Header
    # ========================================================

    svg.append(
        f'''
<text
    x="24"
    y="25"
    class="title"
>
    {escape(username)} — contribution activity
</text>

<text
    x="{WIDTH - 24}"
    y="25"
    text-anchor="end"
    class="subtitle"
>
    Last 53 weeks
</text>
'''
    )

    # ========================================================
    # Day labels
    # ========================================================

    day_labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri",
    }

    for weekday, label in day_labels.items():

        y = (
            TOP
            + weekday * (CELL + GAP)
            + CELL - 2
        )

        svg.append(
            f'''
<text
    x="8"
    y="{y}"
    class="day"
>
    {label}
</text>
'''
        )

    # ========================================================
    # Contribution cells
    # ========================================================

    animation_index = 0

    for week_index, week in enumerate(calendar):

        x = (
            LEFT
            + week_index * (CELL + GAP)
        )

        for weekday, (current_date, day) in enumerate(week):

            y = (
                TOP
                + weekday * (CELL + GAP)
            )

            level = get_level(day)

            color = PALETTE[level]

            delay = animation_index * 0.008

            title_text = (
                f"{day.get('count', 0) if day else 0} "
                f"contributions on "
                f"{current_date.isoformat()}"
            )

            svg.append(
                f'''
<g
    class="cell"
    style="animation-delay:{delay:.3f}s"
>
    <title>{escape(title_text)}</title>

    <rect
        x="{x}"
        y="{y}"
        width="{CELL}"
        height="{CELL}"
        rx="3"
        fill="{color}"
    />
</g>
'''
            )

            animation_index += 1

    # ========================================================
    # Legend
    # ========================================================

    legend_y = TOP + 7 * (CELL + GAP) + 12

    svg.append(
        f'''
<text
    x="{LEFT}"
    y="{legend_y}"
    class="legend"
>
    Less
</text>
'''
    )

    legend_x = LEFT + 31

    for index, color in enumerate(PALETTE):

        x = legend_x + index * (CELL + GAP + 2)

        svg.append(
            f'''
<rect
    x="{x}"
    y="{legend_y - 10}"
    width="{CELL}"
    height="{CELL}"
    rx="3"
    fill="{color}"
/>
'''
        )

    svg.append(
        f'''
<text
    x="{legend_x + 5 * (CELL + GAP + 2) + 3}"
    y="{legend_y}"
    class="legend"
>
    More
</text>
'''
    )

    # ========================================================
    # Statistics
    # ========================================================

    footer_y = HEIGHT - 19

    svg.append(
        f'''
<text
    x="24"
    y="{footer_y}"
    class="footer"
>
    {total:,} contributions
</text>

<text
    x="185"
    y="{footer_y}"
    class="footer"
>
    Current streak: {current_streak} days
</text>

<text
    x="365"
    y="{footer_y}"
    class="footer"
>
    Longest streak: {longest_streak} days
</text>

<text
    x="575"
    y="{footer_y}"
    class="footer"
>
    Best day: {best_count}
</text>
'''
    )

    svg.append("</svg>")

    return "".join(svg)


# ============================================================
# Main
# ============================================================

def main():

    print("Loading contribution data...")

    data = load_data()

    print("Rendering contribution heatmap...")

    svg = create_svg(data)

    OUTPUT.write_text(
        svg,
        encoding="utf-8"
    )

    print()
    print("======================================")
    print(" Contribution heatmap generated")
    print("======================================")
    print(f"Output: {OUTPUT}")
    print("======================================")


if __name__ == "__main__":
    main()
