from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from chat_loader import ChatMessage


def monthly_message_counts(messages: List[ChatMessage]) -> Dict[str, int]:
    """
    Return counts per month as 'YYYY-MM' -> count.
    """
    counts: Counter[str] = Counter()
    for m in messages:
        key = f"{m.date.year:04d}-{m.date.month:02d}"
        counts[key] += 1
    # sort by month key
    return dict(sorted(counts.items()))


def save_monthly_plot(
    messages: List[ChatMessage],
    output_path: str | Path,
    title: str = "Messages per month",
) -> None:
    """
    Generate a bar chart PNG of monthly message counts.
    """
    counts = monthly_message_counts(messages)
    if not counts:
        return

    months = list(counts.keys())
    values = [counts[m] for m in months]

    plt.figure(figsize=(10, 5))
    plt.bar(months, values)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Messages")
    plt.title(title)
    plt.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()



