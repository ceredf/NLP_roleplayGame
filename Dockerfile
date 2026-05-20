FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY .streamlit ./.streamlit
COPY src ./src
COPY examples ./examples

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install . --no-deps --no-build-isolation

EXPOSE 8080

CMD ["sh", "-c", "streamlit run examples/swm_roleplay/streamlit_app.py --server.address 0.0.0.0 --server.port ${PORT:-8080} --server.enableCORS false --server.enableXsrfProtection false --server.enableWebsocketCompression false"]
