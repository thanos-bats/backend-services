from typing import Any, Dict, List, Tuple
import logging
import random
import requests

from config import REALTIME_BULLYING_API_URL, REALTIME_BULLYING_OCR_API_URL
from schemas import RealtimeClassificationResponse, SimpleConversation

logger = logging.getLogger(__name__)

# Set to True later to reactivate the real realtime bullying model call.
ENABLE_REALTIME_MODEL = False

# Labels returned by the real hate speech detection model.
MODEL_LABELS = ["hate-speech", "non-hate-speech"]

# Classes used by the placeholder while the real model is disabled.
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
    # label -> probability, sent by the model as a JSON object
    probs: Dict[str, float] = hs_data.get("confidence") or {}
    if not isinstance(probs, dict):
        raise RuntimeError(f"Unexpected confidence format: {probs!r}")

    if prediction not in MODEL_LABELS:
        raise RuntimeError(f"Unexpected prediction label: {prediction!r}")

    confidence = probs.get(prediction)
    if confidence is None:
        raise RuntimeError(f"Missing confidence for prediction: {prediction!r}")

    return prediction, float(confidence)


def _call_model(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Tight latency budget for the realtime path: keep the timeout short.
    resp = requests.post(api_url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def run_realtime_classification_model(simple: SimpleConversation) -> RealtimeClassificationResponse:
    """
    Bullying/racism classification for the current message.

    The utterances of every screenshot attached to the message are merged into
    a single list and classified in one model call, so multiple screenshots
    are treated as one conversation and the endpoint stays within its latency
    budget.

    For the current phase the real model is intentionally disabled, and we
    return a seeded random placeholder class + confidence.
    """
    if simple.image_count == 0:
        raise ValueError("No image attached.")

    ocr_map: Dict[str, List[str]] = simple.ocr or {}
    if not ocr_map:
        raise ValueError("No chat analysis found for the attached image(s).")

    # Merge every screenshot's utterances into one conversation.
    utterances: List[str] = [utt for lines in ocr_map.values() for utt in lines]
    merged_text = "\n".join(utterances)

    payload: Dict[str, Any] = {
        "id": simple.id,
        "text": utterances,
    }
    logger.info(f"Model input ({len(ocr_map)} image(s) with chat): {payload}")

    if ENABLE_REALTIME_MODEL:
        try:
            hs_data = _call_model(REALTIME_BULLYING_OCR_API_URL, payload)
            logger.info(f"Model output: {hs_data}")
            class_name, confidence = _parse_prediction(hs_data)
        except Exception as exc:
            raise RuntimeError(f"Realtime bullying model failed: {exc}") from exc
    else:
        # Placeholder output while the realtime model is inactive.
        seed = f"{simple.id or ''}:{merged_text}"
        rng = random.Random(seed)
        class_name = rng.choice(REALTIME_CLASSES)
        confidence = rng.random()
        logger.info("Model disabled, returning placeholder prediction")

    return RealtimeClassificationResponse(
        id=simple.id,
        class_name=class_name,
        confidence_score=confidence,
    )
