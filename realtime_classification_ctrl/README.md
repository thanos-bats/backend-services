# Realtime Classification Controller

Classifies the chat text extracted from the screenshots attached to a message as `hate-speech` or `non-hate-speech`.

The controller only looks at images. Call it only when the message has at least one image attached.

## How to call it

Two steps: get a token, then send the message.

| Environment | Base URL |
|---|---|
| Local | `http://localhost:8085/koban` |
| Dev (dev1) | `https://dev1.m4d.iti.gr/koban/dev` |

### Step 1: get a token

```
POST {base}/text_analysis/token
Content-Type: application/x-www-form-urlencoded
```

| Field | Value |
|---|---|
| `grant_type` | `client_credentials` |
| `client_id` | your client id |
| `client_secret` | your client secret |

```bash
curl -X POST "http://localhost:8085/koban/text_analysis/token" \
  -d grant_type=client_credentials \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET
```

The response contains `access_token` and `expires_in` (seconds). Reuse the token until it expires.

### Step 2: send the message

```
POST {base}/text_analysis/realtime_bullying
Authorization: Bearer <access_token>
Content-Type: application/json
```

```bash
curl -X POST "http://localhost:8085/koban/text_analysis/realtime_bullying" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @model_contract/controller_request.sample.json
```

## Request

One message, with its text and image attachments in `content`.

```json
{
  "id": "1d2e3f40-aa11-4b22-9c33-5566778899aa",
  "role": "user",
  "content": [
    { "type": "text", "text": "two screenshots from the same group chat" },
    {
      "type": "image",
      "source": { "mediaId": "1111aaaa/raw", "mimeType": "Image" },
      "chat": "{Other: why are you even in this group},{Other: nobody wants you here},{ME: i didn't do anything}"
    },
    {
      "type": "image",
      "source": { "mediaId": "2222bbbb/raw", "mimeType": "Image" },
      "chat": "{Other: just leave already},{Other: everyone is laughing at you},{ME: please stop}"
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `id` | no | Returned unchanged in the response. |
| `content[].type` | yes | `text` or `image`. Only `image` items are classified. |
| `content[].source.mediaId` | yes, for images | Identifies the image. |
| `content[].chat` | yes, for images | The conversation extracted from the screenshot. |

Format of `chat`: one `{speaker: text}` per message, separated by commas.

```
{Other: nobody wants you here},{ME: please stop}
```

Other fields (`caption`, `ocr`, ...) are accepted and ignored.

When a message has several images, all their chats are joined in order and classified together as one conversation.

## Response

`200 OK`: one result for the whole message.

```json
{
  "id": "1d2e3f40-aa11-4b22-9c33-5566778899aa",
  "class": "hate-speech",
  "confidence_score": 0.8233574067287723
}
```

| Field | Notes |
|---|---|
| `id` | The `id` from the request. |
| `class` | `hate-speech` or `non-hate-speech`. |
| `confidence_score` | Between 0 and 1. |

> The real model is currently switched off. Until it is switched on, the controller returns a random placeholder class and score.

## Errors

Errors come back as `{ "detail": "<message>" }`.

| Status | Message | Meaning |
|---|---|---|
| 400 | `No image attached.` | The message has no image. |
| 400 | `No chat analysis found for the attached image(s).` | There are images, but none has a usable `chat`. |
| 401 | `Missing or invalid Authorization header.` | No token was sent. |
| 401 | `Invalid Keycloak token: ...` | The token is wrong or expired. Get a new one. |
| 502 | `Error calling realtime bullying service: ...` | The model failed or returned an unexpected answer. |

If only some of the images have a `chat`, the ones without are skipped and the rest are classified.

## Run it

```bash
docker compose up -d --build
```

The controller listens on port `4041`. It needs the `koban` Docker network and the Keycloak container to be running.

## Logs

```bash
docker logs -f realtime_classification_ctrl
```

Each request is logged between a blank line and a dashed line: what was received, what was sent to the model, what the model answered, and what was returned. Timestamps are in UTC.

## Model contract

The `model_contract/` folder has the schema and a sample for what the controller sends to the hate speech model and what it expects back.
