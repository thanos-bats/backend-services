FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for the API
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    requests \
    python-jose \
    pydantic-settings \
    python-dotenv

COPY . /app

EXPOSE 4041

CMD ["uvicorn", "realtime_classification_ctrl:app", "--host", "0.0.0.0", "--port", "4041"]
