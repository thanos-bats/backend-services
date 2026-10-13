from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SimpleConversation(BaseModel):
    id: Optional[str] = None
    text: str
    # Number of image attachments in the message, with or without chat analysis
    image_count: int = 0
    # mediaId -> utterances extracted from the image chat analysis
    ocr: Optional[Dict[str, List[str]]] = None


class ImagePrediction(BaseModel):
    class_name: str = Field(alias="class")
    confidence_score: float

    model_config = ConfigDict(populate_by_name=True)


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RealtimeClassificationRequest(BaseModel):
    # The current message, sent per-message as it is posted. `content` carries
    # the text plus one or more image attachments (screenshots). Multiple
    # screenshots are treated as a single conversation.
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "id": "422eccb2-1e8b-49e5-9d13-249a946c643d",
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please provide a caption for this image I have attached.\n"},
                    {
                        "type": "image",
                        "source": {
                            "mediaId": "6be4aaa886d9ad78303ab997fbefcc097b60406e/raw",
                            "mimeType": "Image",
                        },
                        "caption": "A blue car is parked at the roadside, it appears to have a shattered window.",
                        "ocr": "PARKING RESTRICTIONS APPLY",
                        "chat": "{ME: leave me alone},{Other: nobody likes you}",
                    },
                    {
                        "type": "image",
                        "source": {
                            "mediaId": "aekoriginale4aaa886d9ad78303ab997fbefcc097b60506e/raw",
                            "mimeType": "Image",
                        },
                        "ocr": "GO AWAY",
                        "chat": "{Other: everyone hates you},{ME: stop it}",
                    },
                ],
            }
        },
    )


class RealtimeClassificationResponse(BaseModel):
    id: Optional[str] = None
    class_name: Optional[str] = Field(default=None, alias="class")
    confidence_score: Optional[float] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "422eccb2-1e8b-49e5-9d13-249a946c643d",
                "class": "racism/xenophobia",
                "confidence_score": 0.8233574067287723,
            }
        },
    )
