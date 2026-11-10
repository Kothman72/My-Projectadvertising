import csv
from html import escape
from math import ceil, sqrt
from pathlib import Path


DATA_PATH = Path(__file__).with_name("advertising.csv")
OUTPUT_PATH = Path(__file__).with_name("advertising_visualization.svg")

CLICK_COLUMN = "Clicked on Ad"
FEATURES = {
    "Age": "Age",
    "Daily Time Spent on Site": "Time on site",
    "Daily Internet Usage": "Internet use",
    "Area Income": "Area income",
}


def text(x, y, value, size=13, fill="#526078", anchor="middle", weight="normal"):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">'
        f"{escape(str(value))}</text>"
    )


def load_data():
    with DATA_PATH.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required_columns = {*FEATURES, CLICK_COLUMN}
        missing_columns = required_columns.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing_columns))}")

        rows = []
        for row in reader:
            record = {name: float(row[name]) for name in FEATURES}
            clicked = int(row[CLICK_COLUMN])
            if clicked not in (0, 1):
                raise ValueError(f"Expected {CLICK_COLUMN} to be 0 or 1, got {clicked}")
            record[CLICK_COLUMN] = clicked
            rows.append(record)

    if not rows:
        raise ValueError(f"No data rows found in {DATA_PATH.name}")
    if {row[CLICK_COLUMN] for row in rows} != {0, 1}:
        raise ValueError("The dataset must contain both clicked and not-clicked records")
    return rows


def make_dashboard(rows):
    navy = "#14213d"
    muted = "#65738b"
    grid = "#e7ebf2"
    blue = "#3678d4"
    orange = "#ef8248"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" '
        'viewBox="0 0 1200 850" role="img" aria-labelledby="title description">',
        "<title id=\"title\">Advertising data overview</title>",
        (
            '<desc id="description">A dashboard comparing ad clicks with '
            'browsing behavior, age, and area income.</desc>'
        ),
        '<rect width="1200" height="850" fill="#f3f6fb"/>',
        text(50, 56, "Advertising data overview", 28, navy, "start", "bold"),
        text(
            50,
            84,
            f"{len(rows):,} visitors  |  Clicked: "
            f"{sum(row[CLICK_COLUMN] for row in rows):,}  |  Did not click: "
            f"{sum(1 - row[CLICK_COLUMN] for row in rows):,}",
            14,
            muted,
            "start",
        ),
    ]

    cards = ((40, 115, 550, 370), (610, 115, 550, 370), (40, 505, 1120, 300))
    for x, y, width, height in cards:
        parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" '
            'fill="#ffffff" stroke="#e5eaf2"/>'
        )

    parts.extend(
        [
            text(65, 151, "Browsing time vs. internet use", 17, navy, "start", "bold"),
            text(65, 176, "Each point is one visitor", 12, muted, "start"),
            f'<circle cx="384" cy="170" r="5" fill="{blue}"/>',
            text(396, 174, "Did not click", 12, muted, "start"),
            f'<circle cx="500" cy="170" r="5" fill="{orange}"/>',
            text(512, 174, "Clicked", 12, muted, "start"),
        ]
    )

    plot_x, plot_y, plot_width, plot_height = 112, 211, 438, 215
    time_values = [row["Daily Time Spent on Site"] for row in rows]
    internet_values = [row["Daily Internet Usage"] for row in rows]
    x_min, x_max = min(time_values), max(time_values)
    y_min, y_max = min(internet_values), max(internet_values)
    x_pad = max((x_max - x_min) * 0.06, 1)
    y_pad = max((y_max - y_min) * 0.06, 1)
    x_min, x_max = x_min - x_pad, x_max + x_pad
    y_min, y_max = y_min - y_pad, y_max + y_pad

    for tick in range(5):
        x = plot_x + plot_width * tick / 4
        y = plot_y + plot_height * tick / 4
        x_value = x_min + (x_max - x_min) * tick / 4
        y_value = y_max - (y_max - y_min) * tick / 4
        parts.extend(
            [
                f'<line x1="{x:.1f}" y1="{plot_y}" x2="{x:.1f}" '
                f'y2="{plot_y + plot_height}" stroke="{grid}"/>',
                f'<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x + plot_width}" '
                f'y2="{y:.1f}" stroke="{grid}"/>',
                text(x, plot_y + plot_height + 20, f"{x_value:.0f}", 11, muted),
                text(plot_x - 12, y + 4, f"{y_value:.0f}", 11, muted, "end"),
            ]
        )
    for row in rows:
        x = plot_x + (row["Daily Time Spent on Site"] - x_min) / (x_max - x_min) * plot_width
        y = plot_y + (y_max - row["Daily Internet Usage"]) / (y_max - y_min) * plot_height
        color = orange if row[CLICK_COLUMN] else blue
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}" '
            'fill-opacity="0.55"/>'
        )
    parts.extend(
        [
            text(plot_x + plot_width / 2, 464, "Daily time spent on site (minutes)", 12, muted),
            (
                f'<text x="77" y="{plot_y + plot_height / 2}" text-anchor="middle" '
                f'transform="rotate(-90 77 {plot_y + plot_height / 2})" '
                f'font-size="12" fill="{muted}">Daily internet usage</text>'
            ),
        ]
    )

    parts.extend(
        [
            text(635, 151, "Click rate by age", 17, navy, "start", "bold"),
            text(635, 176, "Percentage of visitors who clicked", 12, muted, "start"),
        ]
    )
    age_groups = [
        ("Under 26", lambda age: age < 26),
        ("26-35", lambda age: 26 <= age < 36),
        ("36-45", lambda age: 36 <= age < 46),
        ("46-55", lambda age: 46 <= age < 56),
        ("56+", lambda age: age >= 56),
    ]
    age_plot_x, age_plot_y, age_plot_width, age_plot_height = 671, 211, 440, 215
    for tick in range(0, 101, 25):
        y = age_plot_y + age_plot_height * (100 - tick) / 100
        parts.extend(
            [
                f'<line x1="{age_plot_x}" y1="{y:.1f}" '
                f'x2="{age_plot_x + age_plot_width}" y2="{y:.1f}" stroke="{grid}"/>',
                text(age_plot_x - 12, y + 4, f"{tick}%", 11, muted, "end"),
            ]
        )
    slot_width = age_plot_width / len(age_groups)
    for index, (label, belongs) in enumerate(age_groups):
        group = [row for row in rows if belongs(row["Age"])]
        if not group:
            continue
        click_rate = sum(row[CLICK_COLUMN] for row in group) * 100 / len(group)
        bar_width = 42
        x = age_plot_x + index * slot_width + (slot_width - bar_width) / 2
        height = age_plot_height * click_rate / 100
        y = age_plot_y + age_plot_height - height
        parts.extend(
            [
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{height:.1f}" '
                f'rx="4" fill="{blue}"/>',
                text(x + bar_width / 2, y - 8, f"{click_rate:.0f}%", 12, navy, weight="bold"),
                text(x + bar_width / 2, age_plot_y + age_plot_height + 20, label, 11, muted),
                text(
                    x + bar_width / 2,
                    age_plot_y + age_plot_height + 36,
                    f"n={len(group)}",
                    10,
                    muted,
                ),
            ]
        )

    parts.extend(
        [
            text(65, 544, "What differs between clickers and non-clickers?", 17, navy, "start", "bold"),
            text(
                65,
                568,
                "Mean difference, scaled by the feature's spread  "
                "(negative = lower among clickers; positive = higher)",
                12,
                muted,
                "start",
            ),
        ]
    )
    clickers = [row for row in rows if row[CLICK_COLUMN] == 1]
    non_clickers = [row for row in rows if row[CLICK_COLUMN] == 0]
    effects = []
    for feature, label in FEATURES.items():
        clicked_values = [row[feature] for row in clickers]
        unclicked_values = [row[feature] for row in non_clickers]
        pooled_sd = sqrt(
            (sum((value - sum(clicked_values) / len(clicked_values)) ** 2 for value in clicked_values)
             + sum((value - sum(unclicked_values) / len(unclicked_values)) ** 2 for value in unclicked_values))
            / (len(clicked_values) + len(unclicked_values) - 2)
        )
        effect = (
            (sum(clicked_values) / len(clicked_values) - sum(unclicked_values) / len(unclicked_values))
            / pooled_sd
            if pooled_sd
            else 0
        )
        effects.append((label, effect))

    max_effect = max(abs(effect) for _, effect in effects)
    effect_limit = max(1, ceil(max_effect * 2) / 2)
    chart_left, chart_right = 270, 1095
    chart_top, row_gap = 600, 42
    zero_x = chart_left + (chart_right - chart_left) / 2
    parts.append(
        f'<line x1="{zero_x:.1f}" y1="{chart_top - 13}" '
        f'x2="{zero_x:.1f}" y2="{chart_top + row_gap * len(effects) - 15}" '
        f'stroke="#9aa6b8" stroke-width="1.5"/>'
    )
    for index, (label, effect) in enumerate(effects):
        y = chart_top + index * row_gap
        bar_width = abs(effect) / effect_limit * (chart_right - chart_left) / 2
        x = zero_x if effect >= 0 else zero_x - bar_width
        color = orange if effect >= 0 else blue
        parts.extend(
            [
                text(235, y + 5, label, 13, navy, "end", "bold"),
                f'<rect x="{x:.1f}" y="{y - 10}" width="{bar_width:.1f}" height="20" '
                f'rx="4" fill="{color}"/>',
                text(
                    zero_x + (bar_width + 8 if effect >= 0 else -bar_width - 8),
                    y + 5,
                    f"{effect:+.2f}",
                    12,
                    muted,
                    "start" if effect >= 0 else "end",
                ),
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    records = load_data()
    OUTPUT_PATH.write_text(make_dashboard(records), encoding="utf-8")
    print(f"Created visualization: {OUTPUT_PATH}")
