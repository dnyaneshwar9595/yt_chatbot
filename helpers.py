import json
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

DATA_DIR = Path("data")
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

def get_youtube_id(url: str) -> str:
    """Extract video ID from a YouTube link."""
    import re
    match = re.search(r"(?:v=|be/)([A-Za-z0-9_-]{11})", url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

def fetch_transcript(video_id: str, languages=["en"]) -> str:
    """Return transcript as a single string, cached in JSON."""
    out_path = TRANSCRIPT_DIR / f"{video_id}.json"

    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("text", "")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        if hasattr(transcript, "fetch"):  # handle FetchedTranscript
            transcript = transcript.fetch()
        if not isinstance(transcript, list):
            transcript = list(transcript)
    except NoTranscriptFound:
        raise RuntimeError("Transcript not available for this video")

    full_text = "\n".join([seg["text"] for seg in transcript])

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"video_id": video_id, "text": full_text}, f, ensure_ascii=False, indent=2)

    return full_text
