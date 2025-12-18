from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chat_loader import load_messages
from stats_messages import (
    count_messages,
    count_messages_per_person,
    longest_talking_and_silent_streaks,
)
from stats_time import monthly_message_counts
from stats_words import count_specific_words, top_words


DEFAULT_JSON_PATH = Path("data/result.json")

app = FastAPI(title="Chat Stats API")

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)

def _load() -> list:
    return load_messages(DEFAULT_JSON_PATH)


@app.get("/")
def index():
    """Serve the simple frontend."""
    return FileResponse("frontend/index.html")


@app.get("/stats/messages")
def get_message_stats():
    msgs = _load()
    return {
        "total_messages": count_messages(msgs),
        "per_person": count_messages_per_person(msgs),
    }


@app.get("/stats/words/top")
def get_top_words(
    top_n: int = 10,
    min_len: int = 3,
    skip: Optional[List[str]] = Query(default=None),
):
    msgs = _load()
    return top_words(msgs, min_len=min_len, top_n=top_n, skip=skip)


@app.post("/stats/words/search")
def post_word_search(words: List[str]):
    msgs = _load()
    return count_specific_words(msgs, words)


@app.get("/stats/time/monthly")
def get_monthly_counts():
    msgs = _load()
    return monthly_message_counts(msgs)


@app.get("/stats/streaks")
def get_streaks():
    msgs = _load()
    return longest_talking_and_silent_streaks(msgs)

