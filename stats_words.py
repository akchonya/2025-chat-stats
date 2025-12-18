import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from chat_loader import ChatMessage


# Basic default stop-words you probably don't care about in top stats
DEFAULT_SKIP_WORDS: List[str] = [
    "ти",
    "я",
    "і",
    "та",
    "це",
    "що",
    "але",
    "не",
    "ну",
    "так",
    "мені",
    "мене",
    "там",
    "вже",
    "все",
    "тебе",
    "тобі",
    "про",
    "щоб",
    "теж"
]


def normalize_repeats(word: str) -> str:
    """
    Collapse repeated characters:
    'приииивет' -> 'привет'
    """
    return re.sub(r"(.)\1+", r"\1", word)


WORD_RE = re.compile(r"[^\W\d_]{3,}", flags=re.UNICODE)


def extract_normalized_words(text: str) -> List[str]:
    """
    Lowercase, split text into words (>=3 letters), normalize repeats,
    and drop anything that looks like a URL.
    """
    text = text.lower()
    # quick URL removal
    text = re.sub(r"https?://\S+", " ", text)

    words: List[str] = []
    for raw in WORD_RE.findall(text):
        w = normalize_repeats(raw)
        if len(w) < 3:
            continue
        words.append(w)
    return words


def write_normalized_corpus(messages: Iterable[ChatMessage], output_path: str | Path) -> None:
    """
    Create a text file where each line is the normalized text of one message.
    This is mainly for debugging / manual exploration.
    """
    path = Path(output_path)
    with path.open("w", encoding="utf-8") as f:
        for msg in messages:
            if not msg.text:
                continue
            words = extract_normalized_words(msg.text)
            if not words:
                continue
            f.write(" ".join(words) + "\n")


def top_words(
    messages: Iterable[ChatMessage],
    min_len: int = 3,
    top_n: int = 10,
    skip: List[str] | None = None,
) -> List[Dict[str, object]]:
    """
    Compute top-N most frequent words across all messages.
    Returns list of {word, total_count, per_person:{name:count}}.
    """
    total_counter: Counter[str] = Counter()
    per_person: Dict[str, Counter[str]] = defaultdict(Counter)

    # Merge built-in defaults with user-provided list
    all_skip = list(DEFAULT_SKIP_WORDS) + (skip or [])
    skip_set = {normalize_repeats(w.lower()) for w in all_skip}

    for msg in messages:
        if not msg.text:
            continue
        words = extract_normalized_words(msg.text)
        if not words:
            continue
        sender = msg.sender_name or (msg.sender_id or "unknown")
        for w in words:
            if len(w) < min_len:
                continue
            if w in skip_set:
                continue
            total_counter[w] += 1
            per_person[sender][w] += 1

    most_common = total_counter.most_common(top_n)
    result: List[Dict[str, object]] = []
    for word, count in most_common:
        per_person_counts = {
            person: c[word] for person, c in per_person.items() if c[word] > 0
        }
        result.append(
            {
                "word": word,
                "total_count": count,
                "per_person": per_person_counts,
            }
        )
    return result


def count_specific_words(
    messages: Iterable[ChatMessage],
    target_words: List[str],
) -> Dict[str, Dict[str, object]]:
    """
    Count how many times each target word appears (normalized),
    overall and per person.
    """
    # Normalize targets using the same pipeline
    norm_targets = {}
    for w in target_words:
        w_low = normalize_repeats(w.lower())
        if w_low:
            norm_targets[w] = w_low

    totals: Dict[str, int] = {w: 0 for w in norm_targets}
    per_person: Dict[str, Dict[str, int]] = defaultdict(lambda: {w: 0 for w in norm_targets})

    for msg in messages:
        if not msg.text:
            continue
        words = extract_normalized_words(msg.text)
        if not words:
            continue
        sender = msg.sender_name or (msg.sender_id or "unknown")
        # pre-normalize once per message
        for original, norm in norm_targets.items():
            count_here = sum(1 for w in words if w == norm)
            if count_here:
                totals[original] += count_here
                per_person[sender][original] = per_person[sender].get(original, 0) + count_here

    result: Dict[str, Dict[str, object]] = {}
    for original in norm_targets:
        result[original] = {
            "total_count": totals[original],
            "per_person": {
                person: counts[original]
                for person, counts in per_person.items()
                if counts.get(original, 0) > 0
            },
        }
    return result



