import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class ChatMessage:
    id: int
    sender_name: Optional[str]
    sender_id: Optional[str]
    date: datetime
    date_only: date
    text: str
    media_type: Optional[str]
    file_name: Optional[str]
    sticker_emoji: Optional[str]


def _extract_text(raw_text) -> str:
    """
    Telegram JSON can store text as:
    - a plain string
    - a list of entities, each having a 'text' field
      (and sometimes plain strings mixed in)
    """
    if isinstance(raw_text, str):
        return raw_text or ""
    if isinstance(raw_text, list):
        parts: List[str] = []
        for part in raw_text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def load_messages(json_path: str | Path) -> List[ChatMessage]:
    """
    Load Telegram export JSON (result.json) and return a list of normalized ChatMessage objects.
    """
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    messages_raw = raw.get("messages", [])
    messages: List[ChatMessage] = []

    for msg in messages_raw:
        if msg.get("type") != "message":
            # skip service messages etc.
            continue

        try:
            dt = datetime.fromisoformat(msg["date"])
        except Exception:
            # Fallback: if anything weird happens just skip this message
            continue

        text = _extract_text(msg.get("text", ""))

        messages.append(
            ChatMessage(
                id=int(msg.get("id", 0)),
                sender_name=msg.get("from"),
                sender_id=msg.get("from_id"),
                date=dt,
                date_only=dt.date(),
                text=text,
                media_type=msg.get("media_type"),
                file_name=msg.get("file_name"),
                sticker_emoji=msg.get("sticker_emoji"),
            )
        )

    return messages


def iter_messages(json_path: str | Path) -> Iterable[ChatMessage]:
    """
    Generator version of load_messages, useful if memory is a concern.
    """
    for msg in load_messages(json_path):
        yield msg


