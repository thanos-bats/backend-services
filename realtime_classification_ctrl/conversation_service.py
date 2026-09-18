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


def _extract_image_chat_text(chat: str) -> str:
    utterances = [utt for pair in parse_image_chat(chat) for utt in pair.values()]
    return "\n".join(utterances)


def simplify_conversation(raw: Dict[str, Any]) -> SimpleConversation:
    """
    Flatten the current message into a SimpleConversation.

    Realtime classification runs per-message: `raw` is the message just posted,
    with its `content` array holding the text plus one or more image
    attachments. Every screenshot's chat text is extracted into the `ocr` map
    (mediaId -> extracted chat text) so the model client can treat all of them
    as one conversation.
    """
    user_lines: List[str] = []
    chat_lines: Dict[str, str] = {}

    for c in raw.get("content") or []:
        if c.get("type") == "text":
            t = (c.get("text") or "").strip()
            if t:
                user_lines.append(t)

        if not _is_image_content(c) or not c.get("chat"):
            continue
        media_id = c.get("source", {}).get("mediaId")
        if not media_id:
            continue
        existing = chat_lines.get(media_id, "")
        new_text = _extract_image_chat_text(c["chat"])
        chat_lines[media_id] = f"{existing}\n{new_text}".strip() if existing else new_text
    print(f"chat_lines: {chat_lines}")
    print(f"user_lines: {user_lines}")

    return SimpleConversation(
        id=raw.get("id"),
        text="\n".join(user_lines),
        ocr=chat_lines if chat_lines else None,
    )
