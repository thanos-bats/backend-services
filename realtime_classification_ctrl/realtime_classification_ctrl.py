import logging
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from auth_service import verify_jwt_token
from conversation_service import simplify_conversation
from model_client import run_realtime_classification_model
from schemas import RealtimeClassificationRequest, RealtimeClassificationResponse

app = FastAPI(title="Realtime Bullying Classification API")
logger = logging.getLogger(__name__)


@app.post(
    "/realtime_bullying",
    response_model=RealtimeClassificationResponse,
    response_model_exclude_none=True,
)
def realtime_bullying_endpoint(
    raw: RealtimeClassificationRequest,
    token_payload: Dict[str, Any] = Depends(verify_jwt_token),
) -> RealtimeClassificationResponse:
    logger.info(f"Received /realtime_bullying request from sub: {token_payload.get('sub')}")
    simple = simplify_conversation(raw.model_dump())
    try:
        return run_realtime_classification_model(simple)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed processing /realtime_bullying")
        raise HTTPException(status_code=502, detail=f"Error calling realtime bullying service: {exc}")
