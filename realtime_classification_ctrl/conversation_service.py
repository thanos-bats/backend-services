from typing import Any, Dict, List
import re

from schemas import SimpleConversation


def clean_assistant_text(text: str) -> str:
    if not text:
        return text

    cleaned = text.replace("[PARAGRAPH_BREAK]", "\n\n")
    cleaned = re.sub(r"<source>.*?</source>", "", cleaned)
    cleaned = re.sub(r"<options>.*?</options>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<sources>.*?</sources>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s+\n", "\n\n", cleaned)
    return cleaned.strip()


def parse_image_chat(chat: str) -> List[Dict[str, str]]:
    convo: List[Dict[str, str]] = []
    if not chat:
        return convo

    for segment in chat.split("},"):
        segment = segment.strip().lstrip("{").rstrip("}")
        if not segment or ":" not in segment:
            continue
        speaker, msg_text = segment.split(":", 1)
        speaker = speaker.strip()
        msg_text = msg_text.strip()
        if msg_text:
            convo.append({speaker: msg_text})

    return convo


def _is_image_content(c: Dict[str, Any]) -> bool:
    return c.get("type") == "image" or c.get("_class", "").endswith("ConversationMessageImageContent")


def _extract_image_chat_utterances(chat: str) -> List[str]:
    return [utt for pair in parse_image_chat(chat) for utt in pair.values()]


def simplify_conversation(raw: Dict[str, Any]) -> SimpleConversation:
    """
    Flatten the current message into a SimpleConversation.

    Realtime classification runs per-message: `raw` is the message just posted,
    with its `content` array holding the text plus one or more image
    attachments. Every screenshot's chat is extracted into the `ocr` map
    (mediaId -> list of utterances) so the model client can treat all of them
    as one conversation. `image_count` counts every image attachment, so the
    caller can tell "no image" apart from "image without chat analysis".
    """
    user_lines: List[str] = []
    chat_lines: Dict[str, List[str]] = {}
    image_count = 0

    for c in raw.get("content") or []:
        if c.get("type") == "text":
            t = (c.get("text") or "").strip()
            if t:
                user_lines.append(t)

        if not _is_image_content(c):
            continue
        image_count += 1
        if not c.get("chat"):
            continue
        media_id = (c.get("source") or {}).get("mediaId") or f"image_{image_count}"
        utterances = _extract_image_chat_utterances(c["chat"])
        if utterances:
            chat_lines.setdefault(media_id, []).extend(utterances)

    return SimpleConversation(
        id=raw.get("id"),
        text="\n".join(user_lines),
        image_count=image_count,
        ocr=chat_lines if chat_lines else None,
    )
