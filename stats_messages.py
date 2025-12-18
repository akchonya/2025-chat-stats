from collections import Counter, defaultdict
from dataclasses import asdict
from typing import Dict, List, Tuple

from chat_loader import ChatMessage


def count_messages(messages: List[ChatMessage]) -> int:
    """Total number of messages."""
    return len(messages)


def count_messages_per_person(messages: List[ChatMessage]) -> Dict[str, int]:
    """Number of messages per sender_name (falls back to sender_id if name is missing)."""
    counts: Counter[str] = Counter()
    for m in messages:
        key = m.sender_name or (m.sender_id or "unknown")
        counts[key] += 1
    return dict(counts)


def longest_talking_and_silent_streaks(
    messages: List[ChatMessage],
) -> Dict[str, Dict[str, object]]:
    """
    Compute:
    - longest streak of consecutive days with at least one message
    - longest streak of consecutive days with zero messages between first and last day
    """
    if not messages:
        return {
            "talking": {"length_days": 0, "start_date": None, "end_date": None},
            "silent": {"length_days": 0, "start_date": None, "end_date": None},
        }

    # Unique sorted list of days with messages
    days = sorted({m.date_only for m in messages})

    # Longest talking streak (consecutive days in 'days')
    best_talk_len = 1
    best_talk_start = days[0]
    best_talk_end = days[0]

    cur_len = 1
    cur_start = days[0]

    for prev, current in zip(days, days[1:]):
        delta = (current - prev).days
        if delta == 1:
            cur_len += 1
        else:
            # streak broken
            if cur_len > best_talk_len:
                best_talk_len = cur_len
                best_talk_start = cur_start
                best_talk_end = prev
            cur_len = 1
            cur_start = current

    # Check final streak
    if cur_len > best_talk_len:
        best_talk_len = cur_len
        best_talk_start = cur_start
        best_talk_end = days[-1]

    # Longest silent streak: gaps > 1 day between consecutive message days
    best_silent_len = 0
    best_silent_start = None
    best_silent_end = None

    for prev, current in zip(days, days[1:]):
        gap = (current - prev).days - 1
        if gap > best_silent_len:
            best_silent_len = gap
            if gap > 0:
                best_silent_start = prev.fromordinal(prev.toordinal() + 1)
                best_silent_end = prev.fromordinal(prev.toordinal() + gap)

    return {
        "talking": {
            "length_days": best_talk_len,
            "start_date": best_talk_start.isoformat(),
            "end_date": best_talk_end.isoformat(),
        },
        "silent": {
            "length_days": best_silent_len,
            "start_date": best_silent_start.isoformat() if best_silent_start else None,
            "end_date": best_silent_end.isoformat() if best_silent_end else None,
        },
    }



