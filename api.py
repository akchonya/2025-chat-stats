import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Header, Request, Response
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
SHARE_DIR = Path("shared")
SHARE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Chat Stats API")

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# maps session_id -> temp file path
uploads: dict[str, Path] = {}


def _load(path: Optional[Path] = None) -> list:
    if path:
        return load_messages(path)
    return load_messages(DEFAULT_JSON_PATH)


@app.get("/")
def index():
    return FileResponse("frontend/index.html")


@app.post("/upload")
async def upload_result(
    file: UploadFile = File(...),
    year: int = 2025,
):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "Only JSON files allowed")

    raw = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    msgs = load_messages(tmp_path)
    msgs = [m for m in msgs if m.date and m.date.year == year]

    # generate session_id and store path
    session_id = str(uuid.uuid4())
    uploads[session_id] = tmp_path

    return {
        "session_id": session_id,
        "messages": {
            "total_messages": count_messages(msgs),
            "per_person": count_messages_per_person(msgs),
        },
        "words_top": top_words(msgs),
        "monthly": monthly_message_counts(msgs),
        "streaks": longest_talking_and_silent_streaks(msgs),
    }


@app.get("/stats/messages")
def get_message_stats(session_id: Optional[str] = Header(None)):
    path = uploads.get(session_id)
    msgs = _load(path)
    return {
        "total_messages": count_messages(msgs),
        "per_person": count_messages_per_person(msgs),
    }


@app.get("/stats/words/top")
def get_top_words(
    top_n: int = 10,
    min_len: int = 3,
    skip: Optional[List[str]] = Query(default=None),
    session_id: Optional[str] = Header(None),
):
    path = uploads.get(session_id)
    msgs = _load(path)
    return top_words(msgs, min_len=min_len, top_n=top_n, skip=skip)


@app.post("/stats/words/search")
def post_word_search(
    words: List[str],
    session_id: Optional[str] = Header(None),
):
    path = uploads.get(session_id)
    msgs = _load(path)
    return count_specific_words(msgs, words)


@app.get("/stats/time/monthly")
def get_monthly_counts(session_id: Optional[str] = Header(None)):
    path = uploads.get(session_id)
    msgs = _load(path)
    return monthly_message_counts(msgs)


@app.get("/stats/streaks")
def get_streaks(session_id: Optional[str] = Header(None)):
    path = uploads.get(session_id)
    msgs = _load(path)
    return longest_talking_and_silent_streaks(msgs)

@app.post("/share")
async def share_report(request: Request):
    html = await request.body()

    share_id = uuid.uuid4().hex[:10]
    path = SHARE_DIR / f"{share_id}.html"
    path.write_bytes(html)

    base_url = str(request.base_url).rstrip("/")

    return {
        "url": f"{base_url}/share/{share_id}"
    }

@app.get("/share/{share_id}")
def get_shared(share_id: str):
    path = SHARE_DIR / f"{share_id}.html"
    if not path.exists():
        return Response(status_code=404)

    return Response(
        content=path.read_text(encoding="utf-8"),
        media_type="text/html"
    )