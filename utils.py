import json
import time

from constants import TRANSCRIPT_DIR
from model import MODEL


def estimate_tokens(messages: list) -> int:
    return len(json.dumps(messages, default=str)) // 4


def microcompact(messages: list):
    indices = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            for part in msg["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    indices.append(part)
    if len(indices) <= 3:
        return
    for part in indices[:-3]:
        if isinstance(part.get("content"), str) and len(part["content"]) > 100:
            part["content"] = "[cleared]"


def auto_compact(messages: list) -> list:
    path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    conv_text = json.dumps(messages, default=str)[:80000]
    messages=[
        {"role": "user", "content": f"Summarize for continuity:\n{conv_text}"}
    ]
    resp = MODEL.invoke(messages, max_tokens=2000)
    summary = resp.text
    return [
        {"role": "user", "content": f"[Compressed. Transcript: {path}]\n{summary}"},
        {
            "role": "assistant",
            "content": "Understood. Continuing with summary context.",
        },
    ]
