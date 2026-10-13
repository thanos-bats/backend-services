import logging
import sys
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from auth_service import verify_jwt_token
from conversation_service import simplify_conversation
from model_client import run_realtime_classification_model
from schemas import RealtimeClassificationRequest, RealtimeClassificationResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

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
    body = raw.model_dump()
    # Blank line before each request and a dashed line after it keep the log readable.
    sys.stderr.write("\n")
    logger.info(f"Received /realtime_bullying from sub={token_payload.get('sub')}: {body}")
    simple = simplify_conversation(body)
    try:
        result = run_realtime_classification_model(simple)
        logger.info(f"Response id={simple.id}: {result.model_dump(by_alias=True, exclude_none=True)}")
        return result
    except ValueError as exc:
        logger.warning(f"Rejected id={simple.id} with 400: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed processing /realtime_bullying")
        raise HTTPException(status_code=502, detail=f"Error calling realtime bullying service: {exc}")
    finally:
        sys.stderr.write("-" * 60 + "\n")
