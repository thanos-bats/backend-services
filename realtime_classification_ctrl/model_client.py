from typing import Any, Dict, Tuple
import ast
import random
import requests

from config import REALTIME_BULLYING_API_URL, REALTIME_BULLYING_OCR_API_URL
from schemas import RealtimeClassificationResponse, SimpleConversation

# Set to True later to reactivate the real realtime bullying model call.
ENABLE_REALTIME_MODEL = False

# Classes returned by the realtime bullying/racism model.
REALTIME_CLASSES = [
    "bullying",
    "physical appearance",
    "racism/xenophobia",
    "LGBTIphobia",
    "physical disability",
    "Intellectual disability",
]


def _parse_prediction(hs_data: Dict[str, Any]) -> Tuple[str, float]:
    prediction = (hs_data.get("prediction") or "").strip().lower()
    probs_raw = hs_data.get("probabilities") or ""
    probs: Dict[str, float] = {}

    if isinstance(probs_raw, str) and probs_raw:
        probs = ast.literal_eval(probs_raw)

    # Map των labels του bullying μοντέλου στα αναμενόμενα labels του API
    if prediction in ["hate-speech", "bullying"]:
        class_name = "hate-speech"
        # Παίρνουμε την τιμή είτε από το key 'hate-speech' είτε από το 'bullying'
        confidence = float(probs.get("hate-speech", probs.get("bullying", 0.0)))
    elif prediction in ["no-hate-speech", "no-bullying"]:
        class_name = "no-hate-speech"
        # Παίρνουμε την τιμή είτε από το key 'no-hate-speech' είτε από το 'no-bullying'
        confidence = float(probs.get("no-hate-speech", probs.get("no-bullying", 0.0)))
    else:
        raise RuntimeError(f"Unexpected prediction label: {prediction!r}")

    if confidence is None:
        raise RuntimeError(f"Missing confidence for prediction: {prediction!r}")

    return class_name, confidence


def _call_model(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Tight latency budget for the realtime path: keep the timeout short.
    resp = requests.post(api_url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def run_realtime_classification_model(simple: SimpleConversation) -> RealtimeClassificationResponse:
    """
    Bullying/racism classification for the current message.

    Every screenshot attached to the message is merged into a single blob of
    extracted text and classified in one model call, so multiple screenshots
    are treated as one conversation and the endpoint stays within its latency
    budget.

    For the current phase the real model is intentionally disabled, and we
    return a seeded random placeholder class + confidence.
    """
    ocr_map: Dict[str, str] = simple.ocr or {}
    if not ocr_map:
        raise ValueError("No images found in message. Please provide at least one image.")

    # Merge every screenshot's extracted text into one conversation.
    merged_text = "\n".join(text for text in ocr_map.values() if text).strip()

    payload: Dict[str, Any] = {
        "id": simple.id,
        "text": merged_text,
    }
    print(f"[Realtime model] Payload media_ids={list(ocr_map.keys())}: {payload}")

    if ENABLE_REALTIME_MODEL:
        try:
            hs_data = _call_model(REALTIME_BULLYING_OCR_API_URL, payload)
            print(f"[Realtime model] Response: {hs_data}")
            class_name, confidence = _parse_prediction(hs_data)
        except Exception as exc:
            print(f"[Realtime model] Failed: {exc!r}")
            raise RuntimeError(f"Realtime bullying model failed: {exc}") from exc
    else:
        # Placeholder output while the realtime model is inactive.
        seed = f"{simple.id or ''}:{merged_text}"
        rng = random.Random(seed)
        class_name = rng.choice(REALTIME_CLASSES)
        confidence = rng.random()
        print(f"[Realtime model] Placeholder prediction: {class_name} ({confidence})")

    return RealtimeClassificationResponse(
        id=simple.id,
        class_name=class_name,
        confidence_score=confidence,
    )
